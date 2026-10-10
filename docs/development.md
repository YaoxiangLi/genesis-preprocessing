# Continue development on another server

GitHub `main` is the development handoff. Clone it to obtain the source, README,
architecture artwork, examples, test fixtures, validation evidence, project
instructions and dependency locks. No Git LFS objects or submodules are required.

## Set up a fresh checkout

Install Git and [Pixi](https://pixi.sh/) for your server, then run:

```bash
git clone --branch main https://github.com/YaoxiangLi/genesis-preprocessing.git
cd genesis-preprocessing
git log -1 --oneline
pixi run install-all
pixi run genesis --help
pixi run genesis doctor
```

`install-all` uses the committed `pixi.lock`, `genesis_tools/uv.lock` and Python
selection in `genesis_tools/.python-version` (currently Python 3.14.5 with the GIL).
It creates environments on the new server. Initial installation needs network
access or populated package caches. Do not copy `.pixi/` or `.venv/` from the old
server: environment paths and binaries are machine-specific. The supported Pixi
platforms are Linux x86_64 and macOS x86_64/ARM64; private vLLM deployment requires
an authorized Linux node and its separate serving environment.

`doctor` reports available tools and Docker access. Docker, a GPU and API
credentials are not prerequisites for the core development checks or mock tutorial;
scientific-container and live-model acceptance have their own prerequisites.

Read [AGENTS.md](../AGENTS.md) before editing. Create a branch for the next change:

```bash
git switch -c work/next-change
```

## Establish your baseline

```bash
pixi run checks
pixi run uv run --frozen --project genesis_tools python \
  examples/curation/offline_workflow.py /tmp/genesis-development-demo
git status --short
```

The demo requires a new, empty destination. Expected result: `status: PASS`, two
included datasets and six demonstration review decisions. It uses synthetic files
and a mock provider; it does not run sequencing pipelines or call a live model.

`checks` includes lint, formatting checks, types, Nextflow stubs, local worker
tests, registry/review tests, fake HTTP, simulated model services and README
command checks. Its initial Nextflow run needs access to the pinned plugin
registry or a verified cache containing `nf-schema@2.4.2` and `nf-dotenv@1.0.0`.
If plugin resolution fails, restore registry access or configure an approved cache
with `NXF_PLUGINS_DIR`; only enable `NXF_OFFLINE=true` after populating it. The
historical `/tmp/genesis-*` paths in validation reports identify old test runs and
are not paths to reuse on a new server. The [hybrid validation report](../validation/reports/hybrid-llm-validation.md)
records the verified plugin archive hashes.

### Recovery when plugin lookup fails

If `checks` stops with `Plugin with id nf-schema not found in any repository`,
this recipe downloads the exact two pinned archives from the official registry,
checks their SHA256 values, and installs them in an ignored checkout-local cache.
Run it from the repository root. It refuses to replace an existing plugin directory.

```bash
pixi run uv run --frozen --project genesis_tools python - <<'PY'
import hashlib
import io
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlopen

cache = Path(".nextflow/genesis-plugins").resolve()
cache.mkdir(parents=True, exist_ok=True)
plugins = [
    ("nf-schema", "2.4.2", "02c2fc38cefd5a38238a208ec6ae52927a3f509f07c97f0e266841924cbbfd9d"),
    ("nf-dotenv", "1.0.0", "bb75972f8557f547b3e1472004e6d71a586b1614431437d3ec64590f550735d4"),
]
for name, version, expected in plugins:
    target = cache / f"{name}-{version}"
    if target.exists():
        raise SystemExit(f"Refusing to overwrite {target}")
    url = f"https://registry.nextflow.io/api/v1/plugins/{name}/{version}/download/{name}-{version}.zip"
    with urlopen(url, timeout=60) as response:
        data = response.read(64 * 1024 * 1024 + 1)
    if len(data) > 64 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit(f"Archive verification failed for {name}")
    with tempfile.TemporaryDirectory(prefix=".stage-", dir=cache) as temporary:
        stage = Path(temporary)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                if item.filename.startswith("/") or ".." in Path(item.filename).parts:
                    raise SystemExit("Unsafe archive member")
            archive.extractall(stage)
        stage.rename(target)
    print(f"Verified {name}@{version}: {expected}")
PY

NXF_PLUGINS_DIR="$PWD/.nextflow/genesis-plugins" NXF_OFFLINE=true pixi run checks
```

Reuse the final command on subsequent runs. If the server cannot reach the download
URLs either, prepare this verified cache on a connected machine and transfer those
two plugin directories through your approved storage workflow. Nextflow documents
the cache and offline settings in its [plugin guide](https://docs.seqera.io/nextflow/plugins/using-plugins).
Do not change the pinned plugin versions or bypass failed checks to recover access.

Pixi currently reports a pre-existing `system-requirements` deprecation warning.
If uv's package cache and the checkout are on different filesystems, its hardlink
attempt may fall back to copying; `UV_LINK_MODE=copy pixi run install-all` selects
copying explicitly. Neither warning is a failed scientific check.

## Current implementation and next work

The completed implementation is on `main`; there are no unpublished local feature
branches or stashes needed to resume it. Milestones:

- `117e5dc`: versioned validation, scientific registry, QC and accountable review.
- `accaf04`: hybrid providers, metadata curation, diagnosis and private model-service management.
- `b04bee2`: README architecture overview and capability status table.

Start with the [README](../README.md#architecture-and-current-capabilities), the
[shared specification](curation/IMPLEMENTATION_BRIEF.md), and the
[completed checklist](curation/CHECKLIST.md). Baseline-audit passages in the
specification describe the earlier checkout; the README and validation reports
describe the implemented state.

For evidence, see [scientific processing](../validation/reports/supported-atac-execution-validation.md),
[curation and hybrid LLMs](../validation/reports/hybrid-llm-validation.md), and
[the architecture figure](../validation/reports/architecture-overview-validation.md).
Real API, GPU/SSH service and remote-scheduler acceptance remain separate next
steps. Synthetic metadata tests do not establish real biological annotation
accuracy. The README supplies opt-in live acceptance commands and prerequisites.

Keep scientific processing deterministic and AI optional. Preserve existing
parameters and resume behavior; metadata changes create reviewed revisions rather
than rewriting executed campaigns. A model proposal is not an approval or a job
operation. Run focused checks while developing and the applicable full suite
before publishing a code change.

## What Git does and does not transfer

Git transfers code, locks, small fixtures, bundled schema/template/icon resources
and recorded validation evidence. The tracked root `.env` contains scientific
image references, not personal API credentials.

Generated environments, caches, build products, reference genomes, sequencing
files, run/work directories, live registry/campaign databases, model weights and
personal credentials are not a GitHub backup. Some validation reports cite large
historical outputs outside Git; the committed reports retain their scope and
recorded evidence. These files are not needed for the synthetic development demo.

If you also need existing scientific data on the new server, transfer it through
your approved storage workflow. Use the documented [registry backup/restore](usage/curation.md)
path for a consistent catalog snapshot, and preserve worker-qualified artifact
locations. Cloning the code does not relocate data, migrate running jobs or grant
credentials on the new host.

Keep secrets and machine-specific provider/site configurations outside the checkout.
Use the committed example configurations as templates, provision existing approved
credentials on the target host, and inspect `git status` before committing.

## Handoff verification

On 2026-10-10, a fresh GitHub clone of `b04bee2` installed successfully, passed CLI
help/doctor and the complete offline demo, and passed the full check suite in
133.200 seconds after applying the verified plugin-cache recovery above. The first
default suite attempt stopped at the registry lookup; it is recorded as a failure,
not a pass. The checkout stayed clean and contained all 383 tracked files, with no
LFS pointers or submodules. This handoff adds documentation/evidence to that code.

[Recorded commands, results and plugin hashes](../validation/evidence/development-handoff/checks.json)
and the [full suite log](../validation/evidence/development-handoff/checks.log)
are committed. This check used a new checkout and new project environments on the
existing Linux host, with existing package caches; it does not claim acceptance
on the as-yet-unspecified destination server or a completely uncached installation.
