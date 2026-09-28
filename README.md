# Flight-Price-Tracker
Tracks one-way and round-trip fares on Google Flights and emails you when a flight drops below your target price.
Forked from [Ritik3111/fly_tracker](https://github.com/Ritik3111/fly_tracker).

## Table of Contents

- [Installation](#Installation)
- [Usage](#Usage)
- [Example](#Example)

## Installation

```
pip install -r requirements.txt
```

Requires Python 3.10+. No browser or API key is needed: searches go through
[fast-flights](https://github.com/AWeirdDev/fast-flights), which queries Google Flights directly.

Emails are sent through Gmail. Create an [app password](https://myaccount.google.com/apppasswords) for the sending account and set:

```
FLY_TRACKER_SENDER=you@gmail.com
FLY_TRACKER_APP_PASSWORD=abcdabcdabcdabcd
```

## Usage

| Argument | Type | Description |
| -------- | -------- | -------- |
| --src | string | Origin airport code, e.g. `BOS` |
| --dest | string | Destination airport code, e.g. `ATL` |
| --price | int | Notify when a fare is at or below this (USD) |
| --date | YYYY-MM-DD | Departure date |
| --return-date | YYYY-MM-DD | Optional. Return date; makes it a round trip |
| --email | string | Where to send the notification |

The search runs once immediately, then every day at 12 AM and 12 PM. An email (and a `Results_*.csv`) is produced only when
at least one fare is under your price.

## Example

One-way, Boston to Atlanta on Nov 7, under $200:

`python -m fly_tracker --src BOS --dest ATL --price 200 --date 2026-11-07 --email you@example.com`

Round trip, returning Nov 9, under $300 total:

`python -m fly_tracker --src BOS --dest ATL --price 300 --date 2026-11-07 --return-date 2026-11-09 --email you@example.com`

For round trips, the price is Google's total for both legs; the table shows the outbound flight.
