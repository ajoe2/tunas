# Cookbook

Recipes for common tasks. All assume:

```python
from tunas import (
    read_cl2,
    Time, Event, Session, TimeStandard,
    qualifies_for, all_qualified, standard_time,
)
```

Most recipes flatten the per-file [`MeetArchive`](parsing.md#meetarchive)s into one list of meets. Swimmers and clubs belong to a single meet, so cross-meet analysis needs explicit indexing.

## Helper functions

```python
def age_at(swimmer, on_date):
    """Swimmer's age in years on a date, or None."""
    birthday = swimmer.birthday
    if birthday is None or on_date is None:
        return None
    return on_date.year - birthday.year - ((on_date.month, on_date.day) < (birthday.month, birthday.day))

def fastest(swims):
    """The fastest timed swim, or None."""
    timed = [s for s in swims if s.time is not None]
    return min(timed, key=lambda s: s.time, default=None)
```


## Top 10 fastest swimmers in a club for an event

```python
def top_ten(club, event):
    bests = []
    for swimmer in club.swimmers:
        best = fastest(swimmer.swims_in(event))
        if best is not None:
            bests.append((swimmer, best.time))
    bests.sort(key=lambda pair: pair[1])
    return bests[:10]

meets = [m for arc in read_cl2("meet.cl2") for m in arc.meets]
club = meets[0].clubs[0]                              # pick a club in this meet
for swimmer, time in top_ten(club, Event.FREE_100_SCY):
    print(f"{swimmer.full_name:<28} {time}")
```

## Find swimmers qualifying for a cut

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

meets = [m for arc in read_cl2("champs.cl2") for m in arc.meets]
qualifiers = [
    s
    for meet in meets
    for s in meet.swimmers
    if has_qualified(s, Event.FREE_100_SCY, TimeStandard.AAAA)
]
print(f"{len(qualifiers)} AAAA performances in 100 SCY Free")
```

## Build a cross-meet swimmer index

Track swimmers across meets by `id_short`:

```python
from collections import defaultdict

meets = [m for arc in read_cl2("season/") for m in arc.meets]

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

Every individual swim, including DQs and scratches:

```python
import csv

meets = [m for arc in read_cl2("results/") for m in arc.meets]

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
                r.session.name if r.session else "",  # None for an entry
                r.status.value,
                r.time.centiseconds if r.time else "",
                str(r.time) if r.time else "",
                age_at(r.swimmer, r.date),
                r.rank,
            ])
```

## Rank entries into a psych sheet

An entries file (a Hy-Tek `.hy3` entries export or an SDIF entries `.cl2`/`.sd3`) parses
into swims with `status=ResultStatus.ENTERED`. Rank each event's entries by seed time,
with no-time (`NT`) seeds last:

```python
from tunas import ResultStatus, read_hy3

(archive,) = read_hy3("Meet Entries-Fall Invite-001.hy3")
meet = archive.meets[0]

events = sorted({s.event for s in meet.individual_swims})  # Event is ordered
for event in events:
    entries = [s for s in meet.individual_swims_for(event)
               if s.status is ResultStatus.ENTERED]
    entries.sort(key=lambda s: (s.seed_time is None, s.seed_time or 0, s.swimmer.last_name))
    print(f"Event {entries[0].event_number or ''} {event.name}")
    for rank, s in enumerate(entries, 1):
        club = s.club.team_code if s.club else "UN"
        print(f"  {rank:>3} {s.swimmer.full_name:<28} {club:<8} {s.seed_time or 'NT'}")
```

## Relay-leg analysis

```python
def all_relay_swims(meet, event):
    """Yield (swimmer, time) for every leg of the given relay event."""
    for relay in meet.relays_for(event):
        for leg in relay.legs:
            if leg.swimmer is None or leg.time is None:
                continue
            yield leg.swimmer, leg.time

meets = [m for arc in read_cl2("champs.cl2") for m in arc.meets]
legs = [pair for meet in meets
        for pair in all_relay_swims(meet, Event.FREE_400_RELAY_SCY)]
legs.sort(key=lambda pair: pair[1])
for swimmer, time in legs[:10]:
    print(f"{swimmer.full_name:<28} {time}")
```

## Get all motivational standards achieved

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

```python
from tunas import ParseReport

# Fold the per-file reports into one running total.
report = ParseReport()
for arc in read_cl2("messy_data/"):
    report.merge(arc.report)

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

## Treat warnings as errors after parsing

```python
warnings = [w for arc in read_cl2("results.cl2") for w in arc.report.warnings]
if warnings:
    raise RuntimeError(
        f"{len(warnings)} bad records: "
        + ", ".join(f"line {w.line_no}: {w.reason}" for w in warnings[:3])
    )
```

## Outcome rates (DQs, scratches)

```python
from collections import Counter

from tunas import ResultStatus

def status_breakdown(meet):
    """How many of each outcome across all individual swims at a meet?"""
    return Counter(r.status for r in meet.individual_swims)

def dq_rate(meet):
    swims = meet.individual_swims
    dqs = sum(1 for r in swims if r.status is ResultStatus.DQ)
    return dqs / len(swims) if swims else 0.0

meets = [m for arc in read_cl2("champs.cl2") for m in arc.meets]
for meet in meets:
    print(meet.name, status_breakdown(meet), f"DQ {dq_rate(meet):.1%}")
```

## Work with splits

Splits live on `IndividualSwim.splits` and, for relays, `Relay.splits` (legs derive their
own; see [Data model](models.md#relay-legs-and-their-events)). This helper yields
per-segment times whether the file stored `INTERVAL` or `CUMULATIVE` splits:

```python
from tunas import SplitType

def interval_splits(swim):
    """Yield (segment_distance, segment_time) for a swim's splits."""
    prev = None
    for sp in sorted(swim.splits, key=lambda s: s.distance):
        if sp.time is None:
            continue
        if sp.split_type is SplitType.INTERVAL:
            yield sp.distance, sp.time
        else:  # CUMULATIVE — subtract the previous cumulative time
            yield sp.distance, sp.time if prev is None else sp.time - prev
            prev = sp.time

meets = [m for arc in read_cl2("champs.cl2") for m in arc.meets]
for r in meets[0].individual_swims:
    if r.splits:
        print(r.swimmer.full_name, r.event.name)
        for dist, seg in interval_splits(r):
            print(f"  @{dist:>4}  {seg}")
```

## Time arithmetic

[`Time`](models.md#times) compares, adds, and subtracts in exact centiseconds:

```python
from tunas import Time

def legs_total(relay):
    """Sum a relay's leg times (None if any leg is missing a time)."""
    total = Time(0)
    for leg in relay.legs:
        if leg.time is None:
            return None
        total = total + leg.time
    return total

def gap_to(standard, swim, age, sex):
    """How much a swim must drop to hit a standard (None if it already qualifies)."""
    cut = standard_time(standard, swim.event, age, sex)
    if cut is None or swim.time is None or swim.time <= cut:
        return None
    return swim.time - cut
```

## Compare prelims and finals

```python
def prelim_final(swimmer, event):
    """(prelim_time, final_time) for an event, when both were swum."""
    by_session = {s.session: s for s in swimmer.swims_in(event) if s.time is not None}
    p, f = by_session.get(Session.PRELIMS), by_session.get(Session.FINALS)
    return (p.time, f.time) if p and f else None
```

## Inspect file provenance

`meet.source_file` holds the file header (`A0`/`Z0`, or `.hy3` `A1`):

```python
meets = [m for arc in read_cl2("results.cl2") for m in arc.meets]
src = meets[0].source_file
if src is not None:
    print("software:", src.software_name, src.software_version)
    print("contact: ", src.contact_name, src.contact_phone)
    print("created: ", src.created, "| file type:", src.file_type)
    print("LSC:     ", src.submitted_by_lsc)
```

## Print a swimmer's full standards table

Using `standards_table` from above:

```python
def print_standards(swimmer):
    table = standards_table(swimmer)
    for event in sorted(table):
        cuts = table[event]
        best = cuts[-1].display() if cuts else "—"   # fastest standard met
        print(f"{event.name:<22} {best:<5} ({', '.join(c.display() for c in cuts) or 'none'})")
```
