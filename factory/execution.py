"""One execution owner at a time, without a second command queue or daemon."""

from contextlib import contextmanager
import fcntl
from pathlib import Path


@contextmanager
def execution_lock(repo: Path, *, runner: bool = False):
    path = repo / ".factory" / ("runner.lock" if runner else "execution.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if runner:
                raise ValueError("A Factory runner already owns this repository. Use its Control Center or stop it first.")
            print("Waiting for the current worker wave to reach a checkpoint. No changes have been applied yet.", flush=True)
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
