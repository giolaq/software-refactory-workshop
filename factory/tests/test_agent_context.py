import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1]))

from agent_context import INLINE_CHAR_LIMIT, PART_CHAR_LIMIT, isolated_template, is_context_error, prepare_context
from adapter_capabilities import load_capabilities
from cursor_cli import cursor_result, invoke_cursor, CursorCLIError
from orchestrator import Factory
from planning_presentation import planning_recovery


class AgentContextTests(unittest.TestCase):
    def test_old_blocked_runs_receive_context_specific_recovery_guidance(self):
        view = planning_recovery({'failure_kind': 'agent', 'error': 'Context too big'}, 'claude', ['claude', 'codex'])
        self.assertEqual(view['kind'], 'context_limit')
        self.assertFalse(view['retry_same_adapter'])
        self.assertEqual(view['recommended_adapter'], 'codex')

    def test_file_backed_assignment_preserves_every_character_and_bounds_each_part(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            source = 'Requirement: preserve café 🍲 and all human decisions.\n' * 2000
            prompt = prepare_context(source, repo)
            self.assertLess(len(prompt), INLINE_CHAR_LIMIT)
            directory = repo / '.factory/context' / hashlib.sha256(source.encode()).hexdigest()
            self.assertEqual((directory / 'assignment.md').read_text(), source)
            parts = [path.read_text() for path in sorted(directory.glob('part-*.txt'))]
            self.assertEqual(''.join(parts), source)
            self.assertTrue(all(len(part) <= PART_CHAR_LIMIT for part in parts))
            self.assertIn('Read ALL', prompt)
            self.assertIn('do not replay', prompt)

    def test_short_input_is_unchanged_until_context_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            self.assertEqual(prepare_context('short assignment', repo), 'short assignment')
            self.assertFalse((repo / '.factory').exists())
            self.assertIn('file-backed', prepare_context('short assignment', repo, force=True))

    def test_context_files_do_not_dirty_a_generic_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            prepare_context('Read this assignment', repo, force=True)
            status = subprocess.run(['git', 'status', '--porcelain'], cwd=repo, text=True, capture_output=True, check=True)
            self.assertEqual(status.stdout, '')

    def test_context_errors_are_distinct_from_auth_quota_and_timeouts(self):
        for message in ('Context too big', 'context_length_exceeded', 'maximum context length is 128000',
                        'prompt is too long', 'context window is full', 'input is too long'):
            self.assertTrue(is_context_error(message), message)
        for message in ('rate limit exceeded', 'invalid API key', 'timed out', 'Context received', 'Token budget exhausted'):
            self.assertFalse(is_context_error(message), message)

    def test_default_and_legacy_templates_isolate_without_breaking_formatting(self):
        template = isolated_template('claude', 'claude -p "$(cat {prompt})" --permission-mode plan')
        command = shlex.split(template.format(prompt='prompt.md'))
        self.assertEqual(json.loads(command[command.index('--mcp-config') + 1]), {'mcpServers': {}})
        self.assertIn('--strict-mcp-config', command)
        self.assertIn('--disable-slash-commands', command)
        self.assertEqual(isolated_template('claude', template), template)
        self.assertIn('--ignore-user-config', isolated_template('codex', '{codex} exec --sandbox read-only {prompt}'))
        custom = 'company-adapter --assignment {assignment}'
        self.assertEqual(isolated_template('claude', custom), custom)

    def test_cursor_context_error_in_zero_exit_envelope_is_not_lost(self):
        with self.assertRaises(CursorCLIError) as error:
            cursor_result(json.dumps({'type': 'result', 'subtype': 'error', 'is_error': True, 'result': 'Context too big'}))
        self.assertTrue(is_context_error(str(error.exception)))

    def test_cursor_config_is_rejected_before_startup_and_never_changed(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(os.environ, {}, clear=True):
            repo = Path(temporary)
            config = repo / '.cursor/mcp.json'
            config.parent.mkdir()
            original = json.dumps({'mcpServers': {'personal': {'command': 'must-not-start'}}})
            config.write_text(original)
            with patch('pathlib.Path.home', return_value=repo), patch('cursor_cli.subprocess.run') as invoke:
                result = invoke_cursor('agent', repo, 'prompt', read_only=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('MCP configuration detected', result.stderr)
            invoke.assert_not_called()
            self.assertEqual(config.read_text(), original)

    def test_all_delivery_roles_restart_once_and_preserve_partial_work(self):
        for agent in ('claude', 'codex', 'cursor'):
            for phase in ('implementation', 'qa', 'code-review', 'final_verifier'):
                with self.subTest(agent=agent, phase=phase), tempfile.TemporaryDirectory() as temporary:
                    repo = Path(temporary)
                    script = repo / 'adapter.py'
                    script.write_text(
                        "import pathlib,sys\n"
                        "work = pathlib.Path('partial.txt')\n"
                        "if not work.exists():\n"
                        "    work.write_text('preserve me')\n"
                        "    print('Context too big')\n"
                        "    sys.exit(1)\n"
                        "assert work.read_text() == 'preserve me'\n"
                        "assert 'file-backed' in pathlib.Path(sys.argv[1]).read_text()\n"
                        "print('FACTORY_ROLE_VERDICT: PASS')\n"
                    )
                    template = shlex.quote(sys.executable) + ' ' + shlex.quote(str(script)) + ' {prompt}'
                    prompt = repo / '.factory/prompts/task.md'
                    prompt.parent.mkdir(parents=True)
                    prompt.write_text('Implement the full requirement; preserve existing behavior.\n')
                    factory = Factory.__new__(Factory)
                    factory.repo = repo
                    factory.run_id = 'context-test'
                    factory.profile_name = 'standard'
                    factory.governance = {'charter_sha256': 'a' * 64}
                    factory.store = SimpleNamespace(data={})
                    factory.cfg = {'agents': {agent: template}, 'factory': {'agent_timeout': 5}}
                    factory.capabilities = load_capabilities({}, {agent: template})
                    factory.charter = SimpleNamespace(max_retries=2)
                    factory.args = SimpleNamespace(scenario='test', mock=False)
                    factory.python = sys.executable
                    factory.codex_bin = None
                    factory._sync_store = lambda: None
                    ticket = {'number': 1, 'attempt': 1}
                    code, output = factory.run_adapter(agent, ticket, repo, prompt, 'task.log', phase)
                    self.assertEqual(code, 0, output)
                    self.assertEqual(len(ticket['context_history']), 1)
                    self.assertIn('context-recovery', ticket['current_log'])
                    self.assertTrue((repo / '.factory/logs/task.log').is_file())
                    script.write_text("import sys\nprint('Context too big')\nsys.exit(1)\n")
                    previous_failures = len(ticket['context_history'])
                    code, output = factory.run_adapter(agent, ticket, repo, prompt, 'blocked.log', phase)
                    self.assertNotEqual(code, 0)
                    self.assertIn('still cannot fit', output)
                    self.assertEqual(len(ticket['context_history']) - previous_failures, 2)
                    factory.charter.max_retries = 0
                    previous_failures = len(ticket['context_history'])
                    code, output = factory.run_adapter(agent, ticket, repo, prompt, 'no-retry.log', phase)
                    self.assertNotEqual(code, 0)
                    self.assertEqual(len(ticket['context_history']) - previous_failures, 1)


if __name__ == '__main__':
    unittest.main()
