import os
import subprocess
import sys
from pathlib import Path


def test_flow_complet_e2e(tmp_path):
    db_file = tmp_path / "e2e.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_file}"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])

    result = subprocess.run(
        [sys.executable, "-m", "backend.scripts.test_flow_complet"],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"flow e2e failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
    assert "Flow complet OK" in result.stdout
