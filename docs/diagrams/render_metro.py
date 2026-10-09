"""Deterministic, repository-native SVG maps. No network or rendering dependencies."""

import argparse
import hashlib
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COLORS = {
    "reads": "#087f8c", "reference": "#4169b1", "qc": "#9260b7",
    "peaks": "#ce6030", "tracks": "#438362", "spp": "#bd527d",
    "future": "#81909f",
}


Point = tuple[int, int]
Node = tuple[str, int, int, str, str, str]
Edge = tuple[str, list[Point], str, bool]


def route(points: list[Point]) -> str:
    result = f"M {points[0][0]} {points[0][1]}"
    for i in range(1, len(points) - 1):
        a, b, c = points[i - 1], points[i], points[i + 1]
        l1 = abs(b[0] - a[0]) + abs(b[1] - a[1])
        l2 = abs(c[0] - b[0]) + abs(c[1] - b[1])
        radius = min(14, l1 / 2, l2 / 2)
        p = (b[0] + (a[0] - b[0]) * radius / l1,
             b[1] + (a[1] - b[1]) * radius / l1)
        q = (b[0] + (c[0] - b[0]) * radius / l2,
             b[1] + (c[1] - b[1]) * radius / l2)
        result += f" L {p[0]:g} {p[1]:g} Q {b[0]} {b[1]} {q[0]:g} {q[1]:g}"
    return result + f" L {points[-1][0]} {points[-1][1]}"


def document(title: str, subtitle: str, nodes: list[Node], edges: list[Edge],
             notes: list[str], workflows: list[str], animated: bool = False) -> str:
    css = """
    svg{--bg:#fbfcfe;--text:#172c3d;--muted:#536779;--panel:#e2e8ef;background:var(--bg);font-family:Arial,Helvetica,sans-serif}
    .title{font-size:32px;font-weight:700;letter-spacing:1px;fill:var(--text)}
    .subtitle,.note{font-size:17px;fill:var(--muted)}
    .label{font-size:21px;font-weight:700;fill:var(--text)}
    .detail{font-size:16px;fill:var(--muted)}
    .station{fill:var(--bg);stroke-width:4}
    .line{fill:none;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}
    .planned{stroke-dasharray:9 9}
    .flow{fill:none;stroke:white;stroke-width:2;stroke-dasharray:2 38;stroke-linecap:round;animation:travel 12s linear infinite;pointer-events:none}
    @keyframes travel{to{stroke-dashoffset:-400}}
    @media(prefers-reduced-motion:reduce){.flow{display:none}}
    @media(prefers-color-scheme:dark){svg{--bg:#14212d;--text:#eff6fc;--muted:#bdcbd6;--panel:#344957}.line,.station{filter:brightness(1.25)}}
    @media print{.flow{display:none}svg{--bg:#fff;--text:#172c3d;--muted:#536779;--panel:#e2e8ef}}
    """
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1480 870" role="img" aria-labelledby="title description">',
        f'<title id="title">{escape(title)}</title>',
        f'<desc id="description">{escape(subtitle + ". " + " ".join(notes))}</desc>',
        f"<style>{css}</style>",
        '<rect width="1480" height="870" fill="var(--bg)"/>',
        f'<text class="title" x="48" y="52">{escape(title)}</text>',
        f'<text class="subtitle" x="48" y="85">{escape(subtitle)}</text>',
    ]
    for i, (color, points, label, planned) in enumerate(edges):
        geometry = route(points)
        cls = "line planned" if planned else "line"
        parts.append(f'<path id="route-{i}" class="{cls}" stroke="{COLORS[color]}" d="{geometry}"><title>{escape(label)}</title></path>')
        if animated and not planned:
            parts.append(f'<path class="flow" style="animation-delay:-{i % 12}s" d="{geometry}"/>')
    for ident, x, y, label, detail, color in nodes:
        parts.extend([
            f'<g id="{ident}"><title>{escape(label + ": " + detail)}</title>',
            f'<circle class="station" cx="{x}" cy="{y}" r="9" stroke="{COLORS[color]}"/>',
            f'<text class="label" text-anchor="middle" x="{x}" y="{y - 40}">{escape(label)}</text>',
            f'<text class="detail" text-anchor="middle" x="{x}" y="{y - 17}">{escape(detail)}</text></g>',
        ])
    parts.append('<path d="M48 762 H1432" stroke="var(--panel)" stroke-width="2"/>')
    for i, note in enumerate(notes):
        parts.append(f'<text class="note" x="48" y="{798 + i * 25}">{escape(note)}</text>')
    fingerprints = "; ".join(
        f"{name} SHA256 {hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}"
        for name in workflows
    )
    parts.append(f"<metadata>Genesis diagram schema 2; {fingerprints}; schematic animation.</metadata></svg>")
    return "\n".join(parts) + "\n"


def edge(color: str, points: list[Point], label: str, planned: bool = False) -> Edge:
    return color, points, label, planned


DAP_NODES = [
    ("samples", 140, 330, "Sample sheet", "SE / PE + controls", "reads"),
    ("VALIDATE_SHEET", 370, 330, "Validate", "Inputs + provenance", "reads"),
    ("DOWNLOAD", 600, 330, "Download", "Unmodified raw mates", "reads"),
    ("BWA_MEM2_ALIGN", 830, 330, "bwa-mem2", "Full-read alignment", "reads"),
    ("CALL_PEAKS", 1060, 330, "MACS3 peaks", "Assigned control", "peaks"),
    ("QUANTIFY", 1290, 330, "Quantify", "RPM + mean RPKM", "peaks"),
    ("FASTQC", 600, 180, "FastQC", "One report per mate", "qc"),
    ("QC", 1060, 180, "samtools QC", "Three metric families", "qc"),
    ("MULTIQC", 1290, 180, "MultiQC", "HTML + parsed data", "qc"),
    ("CHROM_SIZES", 140, 510, "Chromosome sizes", "Verified products", "reference"),
    ("METADATA", 600, 510, "Metadata", "Genome + read length", "reads"),
    ("spp", 830, 510, "SPP", "Separate 50-bp R1", "spp"),
    ("reference", 140, 690, "Exact FASTA", "Explicit assembly", "reference"),
    ("BWA_MEM2_INDEX", 370, 690, "bwa-mem2 index", "Verified products", "reference"),
    ("TRACKS", 1060, 690, "deepTools tracks", "BigWig signal", "tracks"),
]
DAP_EDGES = [
    edge("reads", [(140,330),(600,330),(830,330)], "Validated libraries download and align"),
    edge("peaks", [(830,330),(1060,330),(1290,330)], "Treatment/control peaks and quantification"),
    edge("qc", [(600,330),(715,330),(715,180),(600,180)], "Raw mates independently feed FastQC"),
    edge("qc", [(600,180),(715,180),(715,230),(1405,230),(1405,180),(1290,180)], "FastQC reports feed MultiQC"),
    edge("qc", [(830,330),(945,330),(945,180),(1060,180)], "Alignment QC feeds MultiQC"),
    edge("reads", [(600,330),(485,330),(485,510),(600,510)], "Read metadata"),
    edge("reads", [(600,510),(715,510),(715,330),(830,330)], "Metadata accompanies alignment"),
    edge("reference", [(140,690),(255,690),(255,330),(370,330)], "Reference identity is validated"),
    edge("reference", [(370,330),(255,330),(255,510),(140,510)], "Build or verify chromosome sizes"),
    edge("reference", [(370,330),(255,330),(255,690),(370,690)], "Build or verify index"),
    edge("reference", [(140,510),(600,510)], "Chromosome sizes feed metadata and index resources"),
    edge("reference", [(370,690),(715,690),(715,330),(830,330)], "Verified index feeds alignment"),
    edge("spp", [(830,330),(945,330),(945,510),(830,510)], "Separate shortened-read alignment feeds SPP"),
    edge("tracks", [(830,330),(945,330),(945,690),(1060,690)], "Full-read coverage"),
    edge("tracks", [(1060,690),(1405,690),(1405,330),(1290,330)], "Coverage and chromosome bounds support quantification"),
    edge("qc", [(600,510),(485,510),(485,105),(1405,105),(1405,180),(1290,180)], "Metadata joins run-level reporting"),
]
ATAC_NODES = [
    ("reads",140,330,"Raw PE mates","Synthetic adapter-free","reads"),
    ("ALIGN_AND_MARK",370,330,"Align + mark","bwa-mem2 / samtools","reads"),
    ("FRAGMENTS",600,330,"Filter + fragments","Explicit MAPQ / contigs","reads"),
    ("PEAKS",830,330,"MACS3 BAMPE","Unshifted fragments","peaks"),
    ("ENRICHMENT",1060,330,"Enrichment","Fragment FRiP + toy TSS","peaks"),
    ("PROVENANCE",1290,330,"Provenance","Inputs + policies + SHA","reference"),
    ("RAW_FASTQC",370,180,"FastQC × 2","One task per mate","qc"),
    ("REPORT",1290,180,"MultiQC","Raw + usable QC","qc"),
    ("reference",140,690,"Exact FASTA","Explicit assembly","reference"),
    ("organelles",370,510,"Analysis policy","Mark, then exclude dup.","reference"),
    ("cuts",600,510,"Tn5 cut sites","+4 / −5 convention","tracks"),
    ("complexity",830,690,"Fragment QC","Lengths / NRF / PBC","qc"),
    ("tss",1060,690,"TSS positions","BED0 + strand","reference"),
]
ATAC_EDGES = [
    edge("reads",[(140,330),(600,330)],"Align, mark duplicates, then apply explicit fragment policy"),
    edge("peaks",[(600,330),(1060,330)],"Unshifted usable fragments feed BAMPE peaks and enrichment"),
    edge("qc",[(140,330),(255,330),(255,180),(370,180),(1290,180)],"Raw mate FastQC reports"),
    edge("qc",[(370,330),(485,330),(485,180),(1290,180)],"Raw samtools metrics"),
    edge("qc",[(600,330),(715,330),(715,180),(1290,180)],"Usable samtools metrics"),
    edge("qc",[(1060,330),(1175,330),(1175,180),(1290,180)],"Report waits for enrichment completion"),
    edge("reference",[(1290,180),(1405,180),(1405,330),(1290,330)],"Provenance completes after the report"),
    edge("reference",[(140,690),(255,690),(255,330),(370,330)],"Exact reference feeds alignment"),
    edge("reference",[(370,510),(485,510),(485,330),(600,330)],"Explicit MAPQ, organelles and duplicate policy"),
    edge("tracks",[(600,330),(715,330),(715,510),(600,510)],"Separate shifted cut-site representation"),
    edge("qc",[(600,330),(715,330),(715,690),(830,690)],"Usable fragment distributions and complexity"),
    edge("reference",[(1060,690),(1175,690),(1175,330),(1060,330)],"Explicit TSS positions support diagnostic enrichment"),
]
ROAD_NODES = [
    ("manifest",140,330,"Manifest","Biological library IDs","reads"),
    ("acquisition",370,330,"Acquisition + QC","Original reads retained","reads"),
    ("dap",600,180,"DAP-seq","Implemented","reads"),
    ("dap_outputs",1060,180,"Peaks + quantification","Per treatment","reads"),
    ("bulk_atac",600,330,"Bulk ATAC","Available experimental","tracks"),
    ("bulk_outputs",1060,330,"Fragments + ATAC QC","Synthetic PE validated","tracks"),
    ("single_cell",600,510,"sc/snATAC","Planned barcode route","future"),
    ("cells",1060,510,"Cells + fragments","Specified contract","future"),
    ("pseudobulk",1290,510,"Pseudobulks","Type × replicate","future"),
    ("multiome",140,690,"Multiome identity","Tested linking contract","future"),
    ("rna",600,690,"RNA modality","External, separate QC","future"),
    ("reference_registry",140,180,"Reference registry","Tested schema","reference"),
    ("models",1290,690,"Model inputs","Model-specific export","future"),
]
ROAD_EDGES = [
    edge("reads",[(140,330),(370,330),(485,330),(485,180),(600,180),(1060,180)],"Implemented DAP route"),
    edge("tracks",[(370,330),(600,330),(1060,330)],"Available experimental bulk ATAC route"),
    edge("future",[(370,330),(485,330),(485,510),(600,510),(1060,510),(1290,510)],"Planned barcode processing and pseudobulk",True),
    edge("reference",[(140,180),(255,180),(255,330),(370,330)],"Versioned registry contract",True),
    edge("future",[(140,690),(600,690),(945,690),(945,510),(1060,510)],"Modality-specific QC with shared annotation provenance",True),
    edge("future",[(1060,330),(1175,330),(1175,690),(1290,690)],"Proposed bulk model export",True),
    edge("future",[(1290,510),(1405,510),(1405,690),(1290,690)],"Replicate-specific pseudobulk export",True),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/images")
    out = parser.parse_args().output_dir
    out.mkdir(parents=True, exist_ok=True)
    for assay, title, subtitle, nodes, edges, notes, workflows in [
        ("", "GENESIS / DAP-seq", "Implemented workflow · raw-read QC · explicit controls and reference identity",
         DAP_NODES, DAP_EDGES,
         ["QC is diagnostic. FastQC warnings do not reject a dataset; SPP is reported separately.",
          "Controls receive QC and tracks; treatments receive peaks and quantification. FASTQs and BAMs stay intermediate.",
          "Routes summarize data dependencies, not runtime. Crossings without a station do not join channels."],
         ["main.nf"]),
        ("_atac", "GENESIS / BULK ATAC", "Experimental synthetic PE workflow · explicit policies · no plant pass/fail thresholds",
         ATAC_NODES, ATAC_EDGES,
         ["Duplicate marking measures reads; analysis then excludes marked duplicates and explicitly named organelles.",
          "BAMPE peaks use unshifted fragments. Tn5 cut sites are a separate output. TSS scoring is a toy diagnostic.",
          "One synthetic library; no trimming, replicate pooling or IDR. FASTQs and BAMs stay intermediate."],
         ["experimental/atac/main.nf"]),
    ]:
        for animated, suffix in [(False, ""), (True, "_animated")]:
            (out / f"genesis{assay}_metro_map{suffix}.svg").write_text(
                document(title, subtitle, nodes, edges, notes, workflows, animated))
    (out / "genesis_architecture_metro_map.svg").write_text(document(
        "GENESIS / ARCHITECTURE", "Available assay routes and future contracts · biological replicates remain separate",
        ROAD_NODES, ROAD_EDGES,
        ["Solid: available processing, with ATAC explicitly experimental. Dashed: contracts or planned integration.",
         "RNA and ATAC retain separate QC and inclusion decisions. No implicit biological replicate pooling.",
         "Plant biological thresholds remain UNSPECIFIED. Barcode processing and model export are not production workflows."],
        ["main.nf", "experimental/atac/main.nf"]))
    print("Rendered 5 Genesis SVG maps")


if __name__ == "__main__":
    main()
