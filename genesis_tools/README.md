# Genesis tools

Python helpers for Genesis plant sequencing workflows, validation, benchmarks,
execution monitoring and workflow illustrations.

From the repository root, install with `pixi run install-all` and use
`pixi run genesis --help`. Generate an offline, editable figure with:

```bash
pixi run genesis schematic --workflow atac --output atac.svg
```

The schematic assets include their license notices and a checksummed source
catalog. SVG exports retain these notices in metadata. See the repository's
`docs/usage/schematics.md` for templates, themes and custom layouts.
