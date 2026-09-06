"""Serve real, disposable Rehearsal states for browser checks and screenshots.

No GitHub remote, live model, or user run is used. Ctrl+C removes the fixture.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parents[1]))
from control_center import ControlCenter, ControlCenterServer


def prepare(root: Path, repo: Path, stage: str) -> None:
    for name in ("factory", "demo-app"):
        shutil.copytree(root / name, repo / name, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    for name in (".gitignore", "README.md", "recipe-app-prd.md", "factory.project.toml", "factory.charter.toml", "setup_demo.sh"):
        shutil.copy2(root / name, repo / name)

    def command(*args):
        result = subprocess.run(args, cwd=repo, capture_output=True, text=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stdout[-4000:] + result.stderr[-4000:])

    command("git", "init", "-qb", "main")
    command("git", "config", "user.name", "Workshop Rehearsal")
    command("git", "config", "user.email", "rehearsal@example.invalid")
    command("git", "add", ".")
    command("git", "commit", "-qm", "Disposable workshop fixture")
    command("git", "tag", "factory-baseline")
    if stage == "fresh":
        return
    cli = (sys.executable, "factory/orchestrator.py")
    command(*cli, "plan", "recipe-app-prd.md", "--mock")
    plan = json.loads((repo / ".factory/plans/latest.json").read_text())["plan_id"]
    center = ControlCenter(repo)
    center.save_prd((repo / "recipe-app-prd.md").read_text())
    if stage == "running":
        from planning_pipeline import load_manifest, save_manifest
        run_dir = repo / ".factory/plans" / plan
        manifest = load_manifest(run_dir)
        manifest["status"] = "planning_product_review"
        manifest["stages"]["product_review"].update(status="running", markdown="", json="", sha256="")
        (run_dir / "01-product-review.json").unlink()
        (run_dir / "01-product-review.md").unlink()
        save_manifest(repo, run_dir, manifest)
        return
    if stage == "product":
        return
    command(*cli, "approve-product", plan, "--yes")
    command(*cli, "continue-plan", plan, "--mock")
    command(*cli, "approve-rehearsal", plan, "--yes")
    run = (*cli, "run", "--mock", "--scenario", "recipe-rebrand", "--max-parallel", "1", "--once", "--review-qa-tests")
    command(*run)
    if stage == "qa":
        return
    for _ in range(20):
        state = json.loads((repo / ".factory/state.json").read_text())
        if stage == "review" and any(t["status"] == "In Review" for t in state["tickets"]):
            return
        for ticket in state["tickets"]:
            if ticket["status"] == "QA Review":
                command(*cli, "approve-tests", str(ticket["number"]), "--yes")
            elif ticket["status"] == "In Review":
                command(*cli, "merge", str(ticket["number"]), "--mock", "--yes")
        state = json.loads((repo / ".factory/state.json").read_text())
        if all(t["status"] == "Done" for t in state["tickets"]):
            command(*cli, "evidence", plan, "--output", str(center.runtime / f"evidence-{plan}"))
            return
        command(*run)
    raise RuntimeError("Rehearsal fixture did not reach the requested state")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("fresh", "running", "product", "qa", "review", "done"), default="qa")
    parser.add_argument("--port", type=int, default=5055)
    args = parser.parse_args()
    # CLI buttons in this fixture must use the same test interpreter.
    os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]
    with tempfile.TemporaryDirectory(prefix="factory-browser-") as directory:
        repo = Path(directory) / "rehearsal"
        repo.mkdir()
        prepare(Path(__file__).parents[2], repo, args.stage)
        center = ControlCenter(repo)
        if args.stage == "running":
            # Freeze an in-flight operation for read-only browser checks; no agent runs.
            center.operation = {
                "status": "running", "action": "plan", "title": "Planning fixture",
                "command": "factory plan recipe-app-prd.md --mock",
            }
        with ControlCenterServer(("127.0.0.1", args.port), center) as server:
            print(f"FIXTURE_URL=http://127.0.0.1:{server.server_port}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                center.stop()
