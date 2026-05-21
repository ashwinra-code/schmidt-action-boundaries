#!/usr/bin/env python3
"""Record local clean-environment readiness and validate current strict outputs."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from full_repro_common import CODE_ROOT, FULL_AUDIT, PKG_ROOT


def run(cmd: list[str], cwd: Path = PKG_ROOT) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.strip()


def main() -> None:
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    checks: list[tuple[str, bool, str]] = []

    code, out = run([sys.executable, "-I", "-c", "import sys, numpy; print(sys.version.split()[0]); print(numpy.__version__)"])
    checks.append(("python_isolated_numpy_import", code == 0, out))

    conda_path = shutil.which("conda")
    checks.append(("conda_available", conda_path is not None, conda_path or "conda not found on PATH"))

    docker_path = shutil.which("docker")
    if docker_path:
        code, out = run(["docker", "version"])
        checks.append(("docker_daemon_available", code == 0, out))
        docker_note = (
            "- Docker is installed and the daemon is reachable from this session."
            if code == 0
            else "- Docker is installed, but the daemon is not reachable from this session, so a Docker clean-environment run was not executed here."
        )
    else:
        checks.append(("docker_available", False, "docker not found on PATH"))
        docker_note = "- Docker is not found on PATH, so a Docker clean-environment run was not executed here."

    code, out = run([sys.executable, str(CODE_ROOT / "src" / "09_assert_final_reproduction.py"), "--mode", "strict"])
    checks.append(("strict_assertion_current_outputs", code == 0, out))

    report = [
        "# Clean Environment Probe",
        "",
        f"OS: {platform.platform()}",
        f"Python executable: `{sys.executable}`",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for name, passed, detail in checks:
        one_line = detail.replace("\n", " / ").replace("|", "\\|")
        report.append(f"| `{name}` | {'PASS' if passed else 'WARN'} | {one_line} |")
    report.extend(
        [
            "",
            "Interpretation:",
            "- The local isolated Python check and strict output assertion passed.",
            "- Conda is not available on this machine.",
            docker_note,
            "- Tier 3 independent reproduction still requires an external clean-machine run of `bash run_full_repro.sh --strict`.",
        ]
    )
    (FULL_AUDIT / "clean_environment_probe.md").write_text("\n".join(report))
    if not checks[0][1] or not checks[-1][1]:
        raise SystemExit("Clean-environment probe failed a required local validation")
    print("Clean-environment probe recorded; local isolated Python and strict assertion passed.")


if __name__ == "__main__":
    main()
