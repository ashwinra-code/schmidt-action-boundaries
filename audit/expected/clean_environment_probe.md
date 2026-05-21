# Clean Environment Probe

OS: macOS-26.4.1-arm64-arm-64bit-Mach-O
Python executable: `/opt/homebrew/opt/python@3.14/bin/python3.14`

| Check | Status | Detail |
|---|---:|---|
| `python_isolated_numpy_import` | PASS | 3.14.3 / 2.4.3 |
| `conda_available` | WARN | conda not found on PATH |
| `docker_daemon_available` | WARN | Client: Docker Engine - Community /  Version:           29.3.0 /  API version:       1.54 /  Go version:        go1.26.1 /  Git commit:        5927d80c76 /  Built:             Thu Mar  5 14:22:32 2026 /  OS/Arch:           darwin/arm64 /  Context:           default / failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock: connect: no such file or directory |
| `strict_assertion_current_outputs` | PASS | STRICT RAW-RESPONSE-TO-RESULT REPRODUCTION PASSED / Tier 2A status: PASS / Tier 2B status: PASS /  / Raw/structured responses -> parser replay -> AFC cells -> exact canonical surface match -> denominator flow -> split masks -> hidden-cell reconstruction -> raw-label shuffle null -> final metrics /  / Mean hidden balanced accuracy: 0.746930 / Majority baseline: 0.525086 / Mean lift: 0.221844 / Shuffle null mean: 0.522559 / Shuffle exceedances: 0 / 5000 / Per-model lift: positive in 10 / 10 /  / Denominator: / 150 AFC model-scenario groups / 4 incomplete groups preserved separately / 146 complete 32-cell surfaces / 77 nonconstant eligible surfaces |

Interpretation:
- The local isolated Python check and strict output assertion passed.
- Conda is not available on this machine.
- Docker is installed, but the daemon is not reachable from this session, so a Docker clean-environment run was not executed here.
- Tier 3 independent reproduction still requires an external clean-machine run of `bash run_full_repro.sh --strict`.