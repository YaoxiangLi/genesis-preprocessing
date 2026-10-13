# Genesis workflow maps

The README map describes the implemented validation workflow. Routes show data
dependencies, not measured execution order or performance. Station titles name
the tools or operations; circles indicate stages and plain crossings do not
implicitly join channels. FastQC observes each raw mate independently. SPP uses
a separate shortened-read alignment and is not currently parsed into MultiQC.
The chapter labels are reading guides, not synchronization barriers.

The architecture map distinguishes implemented DAP-seq processing, bulk ATAC, tested pseudobulk/multiome contracts and planned barcode processing.
Solid routes include the available bulk ATAC workflow. Dashed routes mark specified or planned integrations. Biological replicates are not implicitly pooled.

Edit `render_metro.py` to update station labels, data dependencies and layout, then
run `python docs/diagrams/render_metro.py`. It uses only Python's standard library
and deterministically generates seven static, animated and architecture SVGs.
The SVG metadata records the SHA256 of each documented workflow (DAP or ATAC); it is not a
claim about an upstream release. Update a map with its corresponding workflow
change. Do not depict validation-only features as available in an upstream revision
which does not contain them.

SVG text remains editable and selectable. The assets contain no external fonts,
scripts, remote resources or raster images. Native CSS animates small route
markers; the static SVG works without animation. Reduced-motion and print media
disable moving markers, and the palette adapts to dark mode.

Before committing, regenerate and inspect the static SVG at full size and README
width, the animated version in a browser, and the architecture status labels.
Check XML validity and compare routes with the actual Nextflow channels. Screenshots
and browser validation evidence belong in the validation workspace's results,
not the source repository.

The execution map shows local, scheduler and independent-worker routes. It describes
software capabilities; it does not imply live validation on every named cluster.

Illustrated stage-card figures are also available through `pixi run genesis schematic`.
See the [schematic guide](../usage/schematics.md) for themes, editable templates
and the licensed asset catalog. These supplement the detailed metro maps.
