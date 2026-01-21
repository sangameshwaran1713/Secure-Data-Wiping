Decision: `eth_typing` compatibility shim vs pinning upstream

Context

During test runs the project required a few symbols (e.g. `ContractName`, `Manifest`) that some installed `eth_typing` versions lacked or exposed differently. To avoid editing the user's virtualenv, a small project-level shim `eth_typing/__init__.py` was added to provide the missing names and forward to the upstream package where possible.

Options

1) Pin upstream packages in `requirements.txt` (remove shim)
   - Pros:
     - Keeps repository behaviour dependent on well-defined package versions.
     - Avoids maintaining local compatibility code.
   - Cons:
     - Users must install the exact pinned versions; some systems (older OSes) may struggle.
     - CI and contributors must keep pins updated over time.

2) Keep a conservative project-level shim (current approach)
   - Pros:
     - Non-invasive for users: repository works across a wider range of installed upstream versions.
     - Safe for demonstrations and teaching (less setup friction).
   - Cons:
     - Requires maintaining a minimal shim and documenting it clearly.
     - Slightly masks real upstream incompatibilities that should be fixed upstream.

Recommendation (short)

- Keep the project-level `eth_typing` shim for the repository while we: (a) document the shim clearly, (b) add CI checks that report the installed `eth_typing` version, and (c) schedule a follow-up to pin upstream versions and remove the shim once dependency compatibility is stabilized.

Recommended follow-up actions (concrete)

- Update `README.md` and `docs/ETH_TYPING_DECISION.md` (this file) to explain why the shim exists and how to remove it.
- Add a CI step that prints `pip show eth-typing` (or `python -c "import eth_typing; print(eth_typing.__version__)"`) so maintainers can see environment versions in CI logs.
- Create a `CLEANUP.md` issue/todo: after a release window, attempt to remove the shim and pin `eth_typing` to the minimum working version in `requirements.txt` (and bump CI to enforce it).
- If a downstream contributor prefers strict pins now, follow Option (1) instead and remove the shim immediately (requires testing across platforms).

Rationale

This project is an academic demo where low friction and reproducibility for students and examiners is important. The shim minimizes setup problems while preserving a clear path to production-quality dependency management.

If you want, I can now:
- Add a CI step that logs the `eth_typing` version, or
- Replace the shim and pin versions in `requirements.txt` immediately.
