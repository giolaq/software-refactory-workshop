# Use Cursor CLI with the Factory

Cursor can fill every built-in Agent Role: Product Review, System Architecture,
Program Design, Vertical Slices, Supervisor, independent QA, Implementation,
and Code Review. The Factory uses Cursor non-interactively; you do not need to
keep the Cursor editor open.

## 1. Install Cursor CLI

On macOS, Linux, or Windows with WSL, run the command from the
[Cursor installation guide](https://cursor.com/docs/cli/installation):

```sh
curl https://cursor.com/install -fsS | bash
agent --version
```

If `agent` is not found after installation, add `$HOME/.local/bin` to `PATH`
as described by Cursor. The Factory also recognizes the older
`cursor-agent` compatibility name. Set `FACTORY_CURSOR_BIN` only when the
executable uses another path:

```sh
export FACTORY_CURSOR_BIN=/absolute/path/to/agent
```

If Doctor reports missing required options, update the CLI and retry:

```sh
agent update
./factory/factory doctor --full
```

## 2. Sign in

Browser login is the simplest local option:

```sh
agent login
agent status
```

For a non-interactive runner, Cursor also supports `CURSOR_API_KEY`. The
Factory forwards that credential only to Cursor processes; it does not write
the value into prompts, logs, state, or Git.

## 3. Select the Cursor preset

Run this in the product repository after its Project Contract has been
created:

```sh
./factory/factory configure \
  --preset cursor-workshop \
  --github-repository https://github.com/YOUR-NAME/YOUR-REPOSITORY
./factory/factory doctor --full
```

In the Control Center, choose **Cursor workshop** under **Setup →
Connection**. The preset assigns Cursor to planning, supervision,
implementation, QA, and code review. It keeps the Standard profile, one
parallel Ticket, and human review of Acceptance Tests.

Once Doctor passes, every normal Factory command uses Cursor automatically:

```sh
./factory/factory plan PRD.md
./factory/factory continue-plan PLAN_ID
./factory/factory revise PLAN_ID product --feedback "..."
./factory/factory run
```

You can also mix Cursor with other registered adapters by passing
`--planning-agent`, `--supervisor-agent`, `--agent`, `--qa-agent`, or
`--review-agent` to `factory configure`.

## Execution modes

The adapter applies one execution contract consistently:

| Factory Role | Cursor mode | Can edit the Ticket worktree? |
| --- | --- | --- |
| Planning experts | Ask | No |
| Supervisor | Ask | No |
| Architecture, critic, verifier, and Code Review | Ask | No |
| Implementation | Agent | Yes |
| Independent QA | Agent | Yes, within QA-owned paths |

All invocations send the prompt over standard input and use Cursor print mode
with JSON or stream-JSON result output. They also use
`--force` so an unattended process does not stop at a command prompt, and
`--sandbox enabled` for Cursor's command sandbox. The Factory creates and owns
the Ticket worktree, so it deliberately does not pass Cursor's `--worktree`
option.

Cursor documents that print mode can write files and run shell commands. Treat
the Factory worktree, Charter, protected-path checks, diff checks, and gates as
the delivery controls around that access—not as a host security boundary. For
higher-risk repositories, configure Cursor permissions in
`.cursor/cli.json` or `~/.cursor/cli-config.json`. Explicit deny rules still
apply when the Factory uses `--force`.

Example project policy:

```json
{
  "permissions": {
    "allow": [
      "Shell(git)",
      "Shell(npm)",
      "Shell(python3)",
      "Read(**)",
      "Write(**)"
    ],
    "deny": [
      "Read(.env*)",
      "Write(.env*)",
      "Read(**/*.key)",
      "Write(**/*.key)",
      "Shell(rm)"
    ]
  }
}
```

Adapt the allowlist to the target repository. Do not copy it unchanged into a
project that needs a narrower boundary.

## Optional model selection

Cursor chooses its normal default model unless you set:

```sh
export FACTORY_CURSOR_MODEL=MODEL_NAME
```

The value is passed through Cursor's documented `--model` option. Model names,
availability, quotas, and charges remain Cursor account concerns.

## Verification status

The repository tests the complete adapter contract with a fake current Cursor
CLI: executable discovery, required options, authentication status, Cursor
planning, read-only roles, write roles, JSON output, credential filtering, and
the `cursor-workshop` preset. A real subscription is not available in the
development environment used for this change, so a paid model invocation and
a live Cursor-created pull request remain a release-candidate smoke test. Run
`factory doctor --full` and a disposable-repository Ticket before relying on a
new Cursor CLI release in a workshop.

## Official Cursor references

- [Install Cursor CLI](https://cursor.com/docs/cli/installation)
- [Use Agent in the CLI](https://cursor.com/docs/cli/using)
- [Authenticate Cursor CLI](https://cursor.com/docs/cli/reference/authentication)
- [Configure Cursor permissions](https://cursor.com/docs/cli/reference/permissions)
