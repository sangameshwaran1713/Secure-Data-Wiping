Missing Features & Proposed Fixes

This document lists remaining gaps between the repository and the README/ideal feature set, and proposes concrete fixes (prioritised).

1) Real physical destruction
- Gap: Current implementation simulates physical destruction; README previously implied hardware-level destruction.
- Risk: Misleading for operational use; legal/forensic evidence expectations.
- Fix: Mark simulation clearly in docs (done). For real integration: provide an abstraction layer in `secure_data_wiping/wipe_engine` with a hardware backend interface; implement a `PhysicalDestroyer` plugin that invokes vendor/HDD disposal tooling. Add CLI flags to enable/disable simulation and require explicit operator acknowledgement.
- Effort: Medium; requires hardware access and safety/legal review.

2) Hosted/Production Verifier
- Gap: QR links point at a local/placeholder verifier; no hosted verifier service is provided.
- Risk: Users expect online verification; current verifier is local-only.
- Fix: Provide deployment path for the `verifier` service: (a) Docker image (added), (b) `docker-compose` stack (added), (c) optional Kubernetes manifest or a Heroku/Cloud Run example. Add documentation and an installer script that publishes the `contract_config.json` to the hosted verifier's config store.
- Effort: Low–Medium.

3) Turnkey CI / Deployment
- Gap: CI workflow added, but it requires solc install and Ganache; production deployment automation not included.
- Risk: Reproducibility gaps across contributors.
- Fix: Harden CI to cache solc, pin versions, and add a `release` job that compiles and publishes the contract ABI and a release artifact. Add `Makefile` or `scripts/setup_ci.sh` to encapsulate steps.
- Effort: Low.

4) Dependency management (`eth_typing` shim)
- Gap: Project uses a project-level `eth_typing` shim to avoid site-packages edits.
- Risk: Shim masks real upstream incompatibilities and may cause subtle runtime differences.
- Fix: Keep shim for academic/demo use (documented). For production, remove shim and pin upstream versions in `requirements.txt`; add CI gate that installs pinned deps and runs tests across supported Python versions.
- Effort: Low.

5) Demo automation & reproducibility
- Gap: Demo scripts exist; `run_quick_demo_e2e.py` added for E2E but more polish needed (timeouts, clearer logs, optional Docker-driven runs).
- Fix: Add `scripts/demo_runner.sh` or `make demo` to run `docker-compose up --build`, deploy contract, run demo, and shutdown. Add a `--offline` flag for synthetic demo fallback.
- Effort: Low.

6) Verifier completeness & tests
- Gap: `verifier` service is minimal (best-effort log decoding) and lacks tests.
- Fix: Add unit tests and integration tests for `verifier` using a Ganache test container. Add an endpoint to verify certificate contents (accept certificate JSON or QR payload) and return canonical proof object.
- Effort: Low–Medium.

7) Security & legal review
- Gap: README claims legal defensibility; the implementation is educational and needs audit.
- Fix: Add a security section with threat model, data retention policy, and suggested forensic evidence capture steps. Seek legal/supervisor sign-off for any claims about legal defensibility.
- Effort: High (external review recommended).

8) Packaging & releases
- Gap: No published package or release process.
- Fix: Add `pyproject.toml` and `setup.cfg` for packaging, a GitHub Action to build sdist/wheel, and publish to GitHub Releases on tag.
- Effort: Low.

9) Documentation improvements
- Gap: README inflated feature language; some internal docs missing.
- Fix: Add `docs/` pages for deploy, demo, verifier API, and developer setup. Add a quick troubleshooting section for Windows PowerShell execution policy and Docker setup.
- Effort: Low.

Prioritised roadmap (short)
- P0 (now): Document shim decision, add verifier Dockerfile & docker-compose, add CI logging (done).
- P1 (next): Add demo runner (`make demo`/script), add verifier integration tests, add CI release job.
- P2: Hardware integration abstraction (plugin), legal/security review, hosted verifier deployment example.

If you want, I can now: (choose one)
- Implement `make demo` / demo runner (automate Docker compose + deploy + demo),
- Add tests for the `verifier` service, or
- Add the `release` CI job to build/publish artifacts.
