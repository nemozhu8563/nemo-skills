# Import And Copyright

Use this reference when importing a book or verifying the source package.

## Source Package

Create a source package:

```text
02_Sources/_books/<book-slug>/book.md
02_Sources/_books/<book-slug>/source/
02_Sources/_books/<book-slug>/manifest.json
```

`book.md` should include:

- YAML frontmatter: `type: book_source`, `status`, `title`, `author`, `created`, `source_path`, `project`
- original source path
- local source path
- chapter index
- current learning status
- links to course map and learning project

`manifest.json` should include:

- original path
- imported source path
- imported assets path when present
- import timestamp
- line count
- checksum when practical

## Copyright Boundary

When importing a copyrighted commercial book into a vault that is also a git repository:

- copy the full book into the vault only when the user wants local sync or management
- add or verify a git ignore rule for `02_Sources/_books/**/source/`
- keep `book.md`, `manifest.json`, course maps, learning records, and absorbed notes trackable unless the user says otherwise
- do not quote long copyrighted passages in generated notes; use short excerpts only when needed for learning context
