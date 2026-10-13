# Genesis tools

Python helpers for Genesis plant sequencing workflows, validation, benchmarks,
execution monitoring and workflow illustrations.

From the repository root, run `pixi run install-all --install-cli` and add
`~/.local/bin` to your PATH. Then use `genesis --help`. For example, create an
editable workflow figure with:

```bash
genesis schematic --workflow atac --output atac.svg
```

See [the project documentation](../docs/README.md) for processing, catalog and
benchmark commands.

The schematic assets include their license notices and a checksummed source
catalog. SVG exports retain these notices in metadata. See the repository's
`docs/usage/schematics.md` for templates, themes and custom layouts.
