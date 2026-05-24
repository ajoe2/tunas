# Cookbook

Runnable recipes for common tasks. All recipes assume:

```python
from tunas import (
    read_cl2,
    Time, Event, Sex, Stroke, Course, Session, TimeStandard,
    qualifies_for, all_qualified, standard_time,
)
```

`read_cl2` returns `(meets, report)`. Swimmers and clubs are scoped to single meets; cross-meet lookups require explicit iteration.

## Helpers

Common helper functions for calculating swimmer age or fastest swims from parsed fields:

```python
def age_at(swimmer, on_date):
    """Age in years on a date, from the parsed birthday, or None."""
    b = swimmer.birthday
    if b is None or on_date is None:
        return None
    return on_date.year - b.year - ((on_date.month, on_date.day) < (b.month, b.day))

def fastest(swims):
    """The fastest timed swim in an iterable of Swims, or None."""
    timed = [s for s in swims if s.time is not None]
    return min(timed, key=lambda s: s.time, default=None)
```


## Iterate every individual swim

Print every individual swim across all meets:

```python
meets, _ = read_cl2("season/")

for meet in meets:
    for r in meet.individual_swims:
        print(meet.name, r.swimmer.full_name, r.event.name, r.time)
```

## Top 10 fastest swimmers in a club for an event

Find the top 10 fastest swimmers in a club for a specific event:

```python
def top_ten(club, event):
    bests = []
    for swimmer in club.swimmers:
        best = fastest(swimmer.swims_in(event))
        if best is not None:
            bests.append((swimmer, best.time))
    bests.sort(key=lambda pair: pair[1])
    return bests[:10]

meets, _ = read_cl2("meet.cl2")
club = meets[0].clubs[0]                              # pick a club in this meet
for swimmer, time in top_ten(club, Event.FREE_100_SCY):
    print(f"{swimmer.full_name:<28} {time}")
```

## Find swimmers qualifying for a cut

Find swimmers who qualified for a specific motivational standard (e.g., `AAAA`):

```python
def has_qualified(swimmer, event, standard):
    best = fastest(swimmer.swims_in(event))
    if best is None or best.date is None:
        return False
    age = age_at(swimmer, best.date)
    if age is None:
        return False
    std = qualifies_for(best.time, event, age, swimmer.sex)
    return std is not None and std >= standard

meets, _ = read_cl2("champs.cl2")
qualifiers = [
    s
    for meet in meets
    for s in meet.swimmers
    if has_qualified(s, Event.FREE_100_SCY, TimeStandard.AAAA)
]
print(f"{len(qualifiers)} AAAA performances in 100 SCY Free")
```

## Build a cross-meet swimmer index

Reconcile and track a swimmer across multiple meets using `id_short`:

```python
from collections import defaultdict

meets, _ = read_cl2("season/")

# id_short -> list of (meet, swimmer) for that person
by_id = defaultdict(list)
for meet in meets:
    for swimmer in meet.swimmers:
        by_id[swimmer.id_short].append((meet, swimmer))

# All of one swimmer's 100 SCY Free results across the season, by date
def progression(id_short, event):
    rows = []
    for meet, swimmer in by_id.get(id_short, []):
        rows.extend(r for r in swimmer.swims_in(event) if r.date is not None)
    return sorted(rows, key=lambda r: r.date)

for r in progression("49AC52F69618", Event.FREE_100_SCY):
    print(f"{r.date}  {r.time}  {r.meet.name}")
```


## Export to CSV

Export all parsed individual swims to a CSV file (including DQs and scratches):

```python
import csv

meets, _ = read_cl2("results/")

with open("results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "meet", "date", "swimmer", "club", "event", "session", "status",
        "time_centiseconds", "time_str", "age", "rank",
    ])
    for meet in meets:
        for r in meet.individual_swims:
            w.writerow([
                meet.name,
                r.date.isoformat() if r.date else "",
                r.swimmer.full_name,
                r.club.abbreviated_name if r.club else "UN",
                r.event.name,
                r.session.name,
                r.status.value,
                r.time.centiseconds if r.time else "",
                str(r.time) if r.time else "",
                age_at(r.swimmer, r.date),
                r.rank,
            ])
```

## Relay-leg analysis

Find the fastest relay legs for a given relay event:

```python
def all_relay_swims(meet, event):
    """Yield (swimmer, time) for every leg of the given relay event."""
    for relay in meet.relays_for(event):
        for leg in relay.legs:
            if leg.swimmer is None or leg.time is None:
                continue
            yield leg.swimmer, leg.time

meets, _ = read_cl2("champs.cl2")
legs = [pair for meet in meets
        for pair in all_relay_swims(meet, Event.FREE_400_RELAY_SCY)]
legs.sort(key=lambda pair: pair[1])
for swimmer, time in legs[:10]:
    print(f"{swimmer.full_name:<28} {time}")
```

## Get all motivational standards achieved

Find all motivational standards achieved by a swimmer across events:

```python
def standards_table(swimmer):
    """Return a dict: event -> list[TimeStandard] for every event the swimmer hit."""
    out = {}
    for event in {r.event for r in swimmer.individual_swims}:
        best = fastest(swimmer.swims_in(event))
        if best is None or best.date is None:
            continue
        age = age_at(swimmer, best.date)
        if age is None:
            continue
        out[event] = all_qualified(best.time, event, age, swimmer.sex)
    return out
```

## Print parse summary

Summarize parsing metrics and warning counts:

```python
meets, report = read_cl2("messy_data/")
print(f"Read {report.files_read} files")
print(f"  {report.meets_parsed} meets")
print(f"  {report.swimmers_parsed} swimmers")
print(f"  {report.individual_swims_parsed} individual results")
print(f"  {report.relays_parsed} relay results")
print(f"  {report.splits_parsed} splits")
if report.has_warnings:
    print(f"  {len(report.warnings)} warnings:")
    for w in report.warnings[:5]:
        print(f"    {w.source}:{w.line_no} ({w.record_type}): {w.reason}")
    if len(report.warnings) > 5:
        print(f"    ... and {len(report.warnings) - 5} more")
```

## Treat warnings as errors post-parse

Treat parsing warnings as fatal errors post-parse:

```python
meets, report = read_cl2("results.cl2")
if report.warnings:
    raise RuntimeError(
        f"{len(report.warnings)} bad records: "
        + ", ".join(f"line {w.line_no}: {w.reason}" for w in report.warnings[:3])
    )
```

## Analyze outcomes (DQs, Scratches, and Times)

Compute disqualification and scratch rates across a meet:

```python
from tunas import ResultStatus

# Only official times
official = [r for r in meet.individual_swims
            if r.status is ResultStatus.OK]

# Fastest legal swim in an event (ignores DQ/NS/etc.)
def best_legal(swimmer, event):
    times = [r for r in swimmer.swims_in(event)
             if r.status is ResultStatus.OK and r.time is not None]
    return min(times, key=lambda r: r.time, default=None)

from collections import Counter

def status_breakdown(meet):
    """How many of each outcome across all individual swims at a meet?"""
    return Counter(r.status for r in meet.individual_swims)

def dq_rate(meet):
    swims = meet.individual_swims
    dqs = sum(1 for r in swims if r.status is ResultStatus.DQ)
    return dqs / len(swims) if swims else 0.0

meets, _ = read_cl2("champs.cl2")
for meet in meets:
    print(meet.name, status_breakdown(meet), f"DQ {dq_rate(meet):.1%}")
```
