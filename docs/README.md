# docs

This is a basic tool to build sphinx documentation.

## Quick start guide

Run **[generate_doc.sh](generate_doc.sh)** to produce full documentation of **src**.

## Options

The following option allow to customize the documentation:

```bash
    --clean
        remove folders produced by the script
    --init
        initialize sphinx tree
    --build
        build the doc
```

## Markdown documentation

**md_doc** folder is added to the sphinx main toctree through *introduction.md* file. Feel free to add any documentation in this folder.
