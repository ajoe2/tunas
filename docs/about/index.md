# About Tunas

This section contains background on `tunas` design principles, architecture, and release history.

`tunas` parses `.cl2` (SDIF v3) files into a clean, fully-typed object graph and bundles offline motivational time standards. It is designed to **parse, but not interpret**: meets are self-contained and independent, while cross-meet reconciliation, scoring, and analytics are delegated to the application (see [Cookbook](../guide/cookbook.md)).

### Sections

- **[Design & Architecture](architecture.md)**: The core design philosophy, repository layout, domain-model relationships, parser internals, and scoping rules.
- **[Changelog](changelog.md)**: The release history and detailed changes over time.

See also the [File Format](../formats/index.md) reference for the underlying SDIF v3 (`.cl2`)
and Hy-Tek (`.hy3`) specifications, and the [API Reference](../reference/index.md) for the
full symbol-level documentation.
