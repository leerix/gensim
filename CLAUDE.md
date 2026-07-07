# CLAUDE.md

## What this repo is

This is **gensim 3.8.3**, an end-of-life upstream release. This branch's job is
**not** to develop gensim further — it is to keep 3.8.3 **installing, building
its docs, and passing its test suite on a modern stack** (Python 3.9, modern
setuptools/PEP 517, tox 4, and macOS/Apple Silicon).

Upstream 3.8.3 predates NumPy 1.24, SciPy 1.13, scikit-learn 1.x, Sphinx 3+,
tox 4, and modern setuptools/PEP 517. Making it work again is done through
**dependency pins, environment/packaging tweaks, and small compatibility shims**
— never by changing gensim's runtime behaviour.

## Guiding principle

Prefer the **smallest change that keeps 3.8.3 working unmodified**. In order of
preference:

1. A dependency pin or constraint (`setup.py`, `build-constraints.txt`).
2. An environment/packaging tweak (`tox.ini`, `docs/src/conf.py`).
3. A minimal compatibility shim in **test or docstring** code.
4. Only as a last resort, a change to gensim **source** — and only when a pin
   would otherwise force an unreasonably large diff. Call this out explicitly.

Do not "modernize," refactor, or reformat source beyond what a fix requires.

## Layout / where things live

- `setup.py` — dependency pins and the `test` / `test-win` / `test-mac` / `docs`
  extras (`linux_testenv`, `win_testenv`, `mac_testenv`, `docs_testenv`).
- `tox.ini` — test/docs environments. `[testenv]` runs the suite per platform
  factor (`{py..}-{win,linux,mac}`).
- `build-constraints.txt` — constraints applied to PEP 517 **build-isolation**
  envs via `PIP_BUILD_CONSTRAINT` (distinct from what gets installed).
- `README-3.8.3.md` — **the human-readable change log** for this branch. See below.

## Common commands

```bash
tox -e py39-linux      # run the test suite (Linux)
tox -e py39-mac        # macOS (Apple Silicon or Intel)
tox -e py39-win        # Windows
tox -e docs            # build the HTML docs
tox -e flake8          # lint
```

## ⚠️ ALWAYS update README-3.8.3.md

**Every time you make a change to get 3.8.3 working on a modern stack, you MUST
record it in `README-3.8.3.md`.** This is the standing convention for this branch
(the file states it too) — treat it as part of the task, not an afterthought.

For each change, capture:

- **What** changed — the file(s) and the concrete edit (the pin, the setting, the
  shim).
- **Why** — the modern-stack breakage it fixes (the error, the removed API, the
  version boundary). Be specific enough that a future reader understands the
  failure without reproducing it.
- **Trade-offs**, if the fix constrains downstream users (e.g. a global pin) or
  reduces coverage.

Put the entry in the matching section (Dependency pins / Test environments /
Documentation build / Source and test fixes) and, when relevant, keep the
**Verification status** table honest — only add a result you actually observed.
