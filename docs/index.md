<div class="tunas-hero" markdown>
![tunas](assets/logo.svg)
</div>

# tunas

Parse USA Swimming meet files (`.cl2` / SDIF v3 and Hy-Tek `.hy3`) into typed objects — [`Meet`][tunas.models.Meet], [`Club`][tunas.models.Club], [`Swimmer`][tunas.models.Swimmer], [`IndividualSwim`][tunas.models.IndividualSwim], [`Relay`][tunas.models.Relay] — and look up motivational time standards offline. Parsing is lenient by default: problems are collected in a [`ParseReport`][tunas.ParseReport] instead of dropping data.

## Install

```bash
pip install tunas
```

Requires Python 3.12+. No runtime dependencies.

## Quick example

```python
from tunas import read_cl2, read_hy3

# One MeetArchive (meets + parse report) per source file
for archive in read_cl2("results.cl2"):
    for meet in archive.meets:
        print(meet.name, "—", len(meet.swimmers), "swimmers")
        for swim in meet.individual_swims:
            print(swim.swimmer.full_name, swim.event.name, swim.time)

# Same object graph from Hy-Tek files
for archive in read_hy3("results.hy3"):
    for meet in archive.meets:
        print(meet.name, "—", len(meet.swimmers), "swimmers")
```

## Where to next

<div class="grid cards" markdown>

-   :material-rocket-launch-outline:{ .lg .middle } __Getting started__

    ---

    Parse your first `.cl2` file in a few lines.

    [:octicons-arrow-right-24: Get up and running](guide/getting_started.md)

-   :material-file-document-alert-outline:{ .lg .middle } __Parsing & errors__

    ---

    Lenient vs. strict parsing and the error model.

    [:octicons-arrow-right-24: Parsing files](guide/parsing.md)

-   :material-chef-hat:{ .lg .middle } __Cookbook__

    ---

    Recipes for common analysis tasks.

    [:octicons-arrow-right-24: Browse recipes](guide/cookbook.md)

-   :material-graph-outline:{ .lg .middle } __Domain model__

    ---

    The object graph: `Meet`, `Club`, `Swimmer`, `Relay`.

    [:octicons-arrow-right-24: Domain model](guide/models.md)

-   :material-api:{ .lg .middle } __API reference__

    ---

    Every class, function, and exception.

    [:octicons-arrow-right-24: API reference](reference/index.md)

-   :material-drawing:{ .lg .middle } __Design__

    ---

    Architecture and the decisions behind it.

    [:octicons-arrow-right-24: Design notes](about/architecture.md)

</div>
