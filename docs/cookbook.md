# Cookbook

Short, runnable recipes for common tasks. Each one assumes:

```python
from tunas import (
    read_cl2, Time, Event, Sex, Stroke, Course, Session, TimeStandard,
    qualifies_for, all_qualified, standard_time,
)
```

## Top 10 fastest swimmers in a club for an event

```python
def top_ten(club, event):
    swimmers_and_times = []
    for swimmer in club.swimmers:
        best = swimmer.best_result(event)
        if best is not None:
            swimmers_and_times.append((swimmer, best.time))
    swimmers_and_times.sort(key=lambda pair: pair[1])
    return swimmers_and_times[:10]

meets, _ = read_cl2("season/")
club = meets[0].clubs[0]                              # pick a club
for swimmer, time in top_ten(club, Event.FREE_100_SCY):
    print(f"{swimmer.full_name:<28} {time}")
```

## Has the swimmer hit a season qualifying cut?

```python
def has_qualified(swimmer, event, standard, end_of_season):
    best = swimmer.best_result(event)
    if best is None:
        return False
    age = swimmer.age_on(best.date)
    if age is None:
        return False
    std = qualifies_for(best.time, event, age, swimmer.sex)
    return std is not None and std >= standard

# Example: "did anyone hit AAAA in 100 SCY Free this season?"
meets, _ = read_cl2("season/")
qualifiers = [
    s
    for meet in meets
    for s in meet.swimmers
    if has_qualified(s, Event.FREE_100_SCY, TimeStandard.AAAA, end_of_season=None)
]
print(f"{len(qualifiers)} AAAA qualifiers")
```

## Track a swimmer's progression over a season

```python
import datetime

def progression(swimmer, event):
    results = swimmer.results_in(event)
    # results_in is sorted fastest-first; resort by date for a timeline
    return sorted(results, key=lambda r: r.date)

meets, _ = read_cl2("season/")
me = meets[0].find_swimmer(usa_id="49AC52F69618")
if me:
    for r in progression(me, Event.FREE_100_SCY):
        std = qualifies_for(r.time, r.event, me.age_on(r.date), me.sex)
        tag = f" ({std.name})" if std else ""
        print(f"{r.date}  {r.time}{tag}  {r.meet.name}")
```

## Export everything to CSV

```python
import csv

meets, _ = read_cl2("results/")

with open("results.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "meet", "date", "swimmer", "club", "event", "session",
        "time_centiseconds", "time_str", "age", "rank",
    ])
    for meet in meets:
        for r in meet.individual_results:
            w.writerow([
                meet.name,
                r.date.isoformat(),
                r.swimmer.full_name,
                r.club.abbreviated_name if r.club else "UN",
                r.event.name,
                r.session.name,
                r.time.centiseconds,
                str(r.time),
                r.swimmer.age_on(r.date),
                r.rank,
            ])
```

## Relay-leg analysis: who was the fastest 50 Free leg this season?

```python
def all_relay_legs(meets, event, leg_stroke, leg_distance, course):
    """Yield (swimmer, leg_time) for every leg matching the criteria."""
    for meet in meets:
        for relay in meet.relay_results:
            if relay.event != event:
                continue
            for leg in relay.legs:
                if leg.swimmer is None or leg.leg_time is None:
                    continue
                yield leg.swimmer, leg.leg_time

meets, _ = read_cl2("season/")
legs = list(all_relay_legs(meets, Event.FREE_400_RELAY_SCY,
                           Stroke.FREESTYLE, 100, Course.SCY))
legs.sort(key=lambda pair: pair[1])
for swimmer, time in legs[:10]:
    print(f"{swimmer.full_name:<28} {time}")
```

## Find every result that beat the all_qualified threshold

```python
def standards_table(swimmer):
    """Return a dict: event → list[TimeStandard] for every event the swimmer hit."""
    out = {}
    for event in {r.event for r in swimmer.individual_results}:
        best = swimmer.best_result(event)
        age = swimmer.age_on(best.date)
        if age is None:
            continue
        out[event] = all_qualified(best.time, event, age, swimmer.sex)
    return out
```

## Print the parse report

```python
meets, report = read_cl2("messy_data/")
print(f"Read {report.files_read} files")
print(f"  {report.meets_parsed} meets")
print(f"  {report.swimmers_parsed} unique swimmers")
print(f"  {report.individual_results_parsed} individual results")
print(f"  {report.relay_results_parsed} relay results")
print(f"  {report.splits_parsed} splits")
if report.has_warnings:
    print(f"  {len(report.warnings)} warnings:")
    for w in report.warnings[:5]:
        print(f"    {w.source}:{w.line_no} ({w.record_type}): {w.reason}")
    if len(report.warnings) > 5:
        print(f"    ... and {len(report.warnings) - 5} more")
```

## Treat warnings as errors after the fact

If you want the lenient parser's full warning list (instead of
`strict=True`'s fail-fast behavior), check `report.warnings` after
parsing:

```python
meets, report = read_cl2("results.cl2")
if report.warnings:
    # Either raise, log, or fail your CI job here
    raise RuntimeError(
        f"{len(report.warnings)} bad records: "
        + ", ".join(f"line {w.line_no}: {w.reason}" for w in report.warnings[:3])
    )
```

## Distinguish "no time" from "fast time"

`Time(0)` is the canonical "no time" value — `str(Time(0))` is `""` and
`Time(0) == Time(0)` is `True`. The parser drops `NT`, `NS`, `DNF`,
`DQ`, and `SCR` entries entirely rather than encoding them as `Time(0)`,
so when iterating results you can assume `result.time` is always a real
time. If you build a `Time(0)` manually (e.g. as a sentinel), guard
against it:

```python
if best is not None and best.time.centiseconds > 0:
    ...
```
