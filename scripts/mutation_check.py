"""Verify that the active-loan boundary test rejects an off-by-one defect."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    project = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="library-mutation-") as directory:
        target = Path(directory).resolve()
        if target.parent != Path(tempfile.gettempdir()).resolve():
            raise SystemExit("Unexpected temporary directory")
        for name in ("app", "tests"):
            shutil.copytree(project / name, target / name, ignore=shutil.ignore_patterns("__pycache__"))
        source = target / "app/main.py"
        code = source.read_text(encoding="utf-8")
        original = "if active_count >= get_settings().max_active_loans:"
        if code.count(original) != 1:
            raise SystemExit("Mutation target must match exactly once")
        source.write_text(
            code.replace(original, "if active_count > get_settings().max_active_loans:"), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests/test_boundaries.py::test_active_limit"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        if (
            result.returncode != 1
            or "test_active_limit" not in result.stdout
            or "1 failed" not in result.stdout
        ):
            raise SystemExit("Boundary mutation was not detected by the intended test")
        print("Mutation detected: accepting the sixth loan fails the boundary test")


if __name__ == "__main__":
    main()
