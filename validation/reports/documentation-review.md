# Documentation and installation validation, 13 October 2026

The README now leads with installation, a first DAP or ATAC analysis, and where to
find the results. It uses the installed `genesis` command throughout. Optional
catalog, review, worker and AI features have their own task guides, linked from
the README and [documentation index](../../docs/README.md).

## Changes readers will notice

- Shorter introductions explain what a command does, its prerequisites and where
  its outputs go. Examples use consistent input and output names.
- The detailed DAP guide retains control assignments, reference handling,
  alignment/SPP policies, duplicate behavior, track units and peak-score definitions.
  The original DAP README remains unchanged in the historical archive.
- The bulk and single-cell ATAC guides distinguish lanes, libraries, biological
  replicates, fragments and cut sites. Missing metrics remain distinct from zero.
- The benchmark guide names the compared packages, fixed settings, measurement
  populations, timing scope and reproduction commands. Component comparisons,
  complete workflows and synthetic software checks have separate interpretations.
- Design documents, validation reports and retired prototypes link back to the
  current guides. Historical workspace paths are identified as records of the
  original environment, rather than presented as working download links.

The vendored SPP README previously described full-length reads for its separate
QC alignment. It now describes the implemented 50-base cutting step. The upstream
script and scientific processing behavior were preserved.

## Verification

At revision `83ec12b60db6824cfeaced50b2a629e87347d720`, the full `pixi run checks`
command passed. The documentation check parsed 143 maintained CLI examples,
resolved 24 Pixi recipes, checked local links and anchors in all 77 Markdown files,
and verified the archived DAP README's original checksum. New workflow preparation
was also executed on verified public inputs; its generated Genesis and nf-core
configurations passed their input checks.

The full suite also passed at `f35a4f9`, after the production aligner identity was
corrected. Its package metadata and executable hashes establish BWA-MEM2 2.3;
the misleading 2.2.1 banner is now explained in both benchmark guides. Earlier
measurements retain their original package identities.

The revision `a85211237470d7146457167e1723b04a7ebf3cff` passed the full
suite again. Its documentation check covered 80 Markdown files, 143 CLI examples
and 24 Pixi recipes. A new wheel installed outside the checkout also completed
the offline curation tutorial. [Acceptance records](../evidence/method-comparison-20261013/release-acceptance/)
identify the exact commands, package contents and remaining live-service exclusions.

A fresh clone of GitHub `main` at `57e6a0d` installed the direct command using the
documented custom-bin option. General help, DAP/ATAC help and runtime discovery
worked from `/tmp`, and all eight transferred benchmark archives matched their
recorded checksums. The cloned working tree remained clean. See the
[installation record](../evidence/method-comparison-20261013/installation/).

The benchmark HTML report was opened in Chromium. Its initial view now selects
one library and a useful retention metric, and sorts methods and repetitions.
Static figures use explicit proportion/correlation scales and record their source
table and renderer hashes. Figure changes do not change measured results.

These checks verify navigation, command structure and the exercised examples.
They do not make every historical observation current, independently repeat every
old study, or establish that all external services and deployment sites work.
