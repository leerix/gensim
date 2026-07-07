# gensim 3.8.3 on modern Python — change log

This branch keeps **gensim 3.8.3** (an end-of-life release) installing,
building its docs, and passing its test suite on **modern Python 3.9 and
macOS (Apple Silicon)**. Upstream 3.8.3 predates NumPy 1.24, SciPy 1.13,
scikit-learn 1.x, Sphinx 3+, tox 4, and modern setuptools/PEP 517, so a
number of pins, environment tweaks, and small source fixes are needed.

The install works with poetry.

Nothing here changes gensim's runtime behaviour; the edits are confined to
dependency constraints, packaging metadata, the tox/docs configuration, and
a few compatibility shims in test and docstring code.

> **Maintenance:** keep this file up to date. Whenever we make a further
> change to get 3.8.3 working on a modern stack, add it here with the
> **what** and the **why**.

## Quick start

```bash
# Run the test suite for your platform
tox -e py39-linux      # Linux
tox -e py39-mac        # macOS (Apple Silicon or Intel)
tox -e py39-win        # Windows

# Build the HTML documentation
tox -e docs            # output lands in docs/
```

## Changes and rationale

### Dependency pins (`setup.py`)

| Dependency | Pin | Why |
|---|---|---|
| **numpy** (py3) | `>= 1.11.3, < 1.24` | numpy ≥ 1.24 removed the `np.int` / `np.float` / `np.bool` aliases and tightened `np.stack`/`np.vstack` and ragged-array creation, all of which gensim 3.8.3 source relies on. Capping keeps the codebase working unmodified. |
| **scipy** (py3) | `>= 0.18.1, < 1.13` | Later SciPy drops APIs gensim uses and needs newer numpy; `< 1.13` is the last line that resolves cleanly on Python 3.9. |
| **Cython** | `== 0.29.14` | Pinned upstream for reproducible extension builds; still builds the `.pyx` modules on Python 3.9. |
| **Morfessor** | `== 2.0.6` (was `2.0.2a4`) | The old `2.0.2a4` sdist's bundled `ez_setup.py` calls `TarFile.chown()` with the pre-3.6 signature and cannot even build its metadata. 2.0.6 ships a pure-Python wheel. |

> ⚠️ **Trade-off:** the `numpy < 1.24` cap applies to *all* installs, not just
> tests. It constrains downstream users to older numpy. The alternative would
> be to patch the `np.int`/`np.float`/`np.vstack` call sites throughout gensim
> source — a much larger diff — to allow modern numpy.

### Test environments (`setup.py` + `tox.ini`)

- **Added `py39` and a `mac` factor** to the tox `envlist`
  (`{py27,py36,py37,py38,py39}-{win,linux,mac}`).
- **`platform` map**: added `mac: darwin`. tox matches this regex against
  `sys.platform` (which is `darwin` on macOS), so `mac` envs only run on a Mac.
- **New `test-mac` extra** (`mac_testenv`), wired up as `mac: .[test-mac]`.
  It mirrors the Windows set — i.e. **without tensorflow/keras**. Modern
  tensorflow requires numpy ≥ 1.25 (it touches `np.dtypes` at import), which
  conflicts with the `numpy < 1.24` cap, and its wheels are painful on Apple
  Silicon. The keras-backed tests skip cleanly when keras is absent.
- **`whitelist_externals` → `allowlist_externals`** (all four occurrences).
  tox 4.x renamed the setting; without it `make`/`rm` are disallowed and the
  `docs`/`docs-upload`/`download-wheels`/`test-pypi` envs fail.
- **Build-isolation setuptools pinned `< 81` for the test envs**
  (`build-constraints.txt` + `PIP_BUILD_CONSTRAINT` in the `tox.ini`
  `[testenv]` `setenv`). Unlike the `docs` extra, the `test`/`test-win`/`test-mac`
  extras keep `visdom` (it is needed by `test_lda_callback.py`), and pip resolves
  it to `visdom 0.2.4`, whose `setup.py` does `import pkg_resources` at build
  time. setuptools ≥ 81 removed `pkg_resources`, so under PEP 517 build isolation
  the wheel build dies with `ModuleNotFoundError: No module named 'pkg_resources'`
  before any test runs. Constraining the *build-env* setuptools below 81 (it still
  ships `pkg_resources`) lets visdom build while staying installed. We use
  `PIP_BUILD_CONSTRAINT` rather than `PIP_CONSTRAINT` because pip warns the latter
  will stop affecting build environments in pip 26.2.

### Documentation build (`docs/src/conf.py`, `docs/src/gallery/README.txt`)

Getting `tox -e docs` to pass with Sphinx 2.4.4 on a modern toolchain required:

- **Sphinx transitive pins** in the `docs` extra (`setup.py`): `jinja2 < 3.0`,
  `markupsafe < 2.1`, `docutils == 0.16`, `alabaster == 0.7.12`, and the
  split-out `sphinxcontrib-{applehelp,devhelp,htmlhelp,jsmath,qthelp,serializinghtml}`
  helpers. Modern versions removed APIs Sphinx 2.x imports
  (`environmentfilter`, `soft_unicode`) or now require Sphinx ≥ 3.4 / ≥ 5.
- **`scikit-learn < 1.2`** in the `docs` extra: newer scikit-learn injects
  `set_output`/metadata-routing methods into the `sklearn_api` wrappers whose
  docstrings reference scikit-learn's own doc labels → "undefined label"
  warnings that are fatal under Sphinx's `-W`.
- **visdom excluded** from the `docs` extra: it is only imported lazily for the
  visdom callback logger, and its latest release fails to build under PEP 517
  isolation (`import pkg_resources` in its `setup.py`).
- **`conf.py` gallery config**: `show_memory = False` (memory_profiler + psutil
  raise `psutil.ZombieProcess` on modern macOS during gallery init) and
  `plot_gallery = False` (render the gallery pages from source **without**
  executing the `run_*.py` examples, which would train models and download
  corpora over the network).
- **`gallery/README.txt`**: added an explicit `.. _sphx_glr_auto_examples:`
  label. sphinx-gallery 0.11 no longer auto-emits it (0.4.0 did), which
  otherwise breaks a `:ref:` in `support.rst`.

### Source and test fixes

- **`gensim/utils.py`**: fixed an RST defect in the `chunkize` docstring
  (`` `np.ndarray`s `` → `` `np.ndarray` ``); the backtick-then-letter form is
  an "inline interpreted text without end-string" warning, fatal under `-W`.
- **`gensim/test/test_sklearn_api.py`**: alias the removed `sklearn.datasets.base`
  module to `sklearn.utils.Bunch` so the pickled `mini_newsgroup` fixture
  (a `Bunch` from that old module path) still unpickles on scikit-learn ≥ 0.24.
- **`gensim/test/test_lda_callback.py`**: poll `viz.check_connection(timeout_seconds=30)`
  instead of a fixed `time.sleep(3)` before asserting, and **skip** if the
  visdom server never becomes reachable. Spawn the server with `sys.executable`.
  The old fixed delay was too short for a modern visdom server to boot.

### Tooling and housekeeping (earlier branch commits)

- **`pyproject.toml`**: added ruff configuration for formatting and linting
  (line length 160, single quotes, curated rule selection incl. `NPY201`, with
  test/fixture per-file ignores). Existing source was reformatted to match.
- **`requirements_docs.txt`**: bumped `nltk` to `3.9.1`.
- **`gensim/test/make_d2v_model.py`**: helper script that builds a doc2vec model
  fixture used by the tests.
- **`.gitignore`**: broadened to ignore build/test artefacts.

## Verification status

| Command | Result |
|---|---|
| `tox -e docs` | ✅ Build finished (HTML in `docs/`) |
| `tox -e py39-mac` | ✅ 1040 passed, 55 skipped |

The 55 skips are environment-optional dependencies (annoy, autograd,
Mallet via `MALLET_HOME`, Vowpal Wabbit via `VOWPAL_WABBIT_PATH`) and the
keras-backed tests (keras intentionally absent from `test-mac`).

## Docker

In the `docker39/` directory:

- build.sh: builds a docker image
- run.sh: runs the image with a bash shell

Once it's running, run `./test-3.8.3.sh`. This runs all the commands listed in CONTRIBUTING.md.
