# a11y-Score open-data example

Minimal Python example that turns the [a11y-Score open data](https://a11yscore.org/open-data) into a short, citizen-facing accessibility summary for a city — with a pivot table of scores and place counts by place type, plus a generated progress text (German).

```console
$ python mainz_a11y_stats.py

                                  Abdeckung %  Orte gesamt  Orte mit Daten  Score (0-100)
Ortstyp
Arbeit                                     62          307             189           94.8
Soziale Dienste                            66           53              35           93.6
Bildung                                    62          315             196           93.1
…

Barrierefreiheit in Mainz: 72 von 100 Punkten (a11y-Score, Stand 01.10.2026). Am
zugänglichsten sind Orte der Kategorie „Arbeit“ (95 Punkte), den größten
Handlungsbedarf gibt es bei „Parks und öffentliche Räume“ (32 Punkte). …
```

## Run it

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install duckdb pandas pyarrow
python mainz_a11y_stats.py
```

No download required: DuckDB reads the daily Parquet export straight from its URL using HTTP range requests, so only the queried parts are transferred. Set `A11YSCORE_PARQUET` to run against a local file instead.

## Tests

The e2e test runs the script against the pinned Parquet snapshot in `data/` (Git LFS), so it needs no network:

```sh
pip install pytest
pytest
```

## How it works

- The open data publishes every chart row of a11yscore.org as Parquet (`dimension-combination-metrics`), regenerated daily around 06:00 (Europe/Berlin).
- The script selects the one `category` chart computed for the city — overall accessibility (`tree-root-accessibility`) grouped by place category — and pivots it with pandas.
- Place types whose **survey completeness** (places with accessibility data ÷ all places, `d0_x_d1_x_d2_count / n_total`) is below 10 % are cut off and reported separately instead of being ranked.

## Adapt it

Change `CITY_NAME` and `CITY_WIKIDATA_ID` in `mainz_a11y_stats.py` to summarize another city. Look up the Wikidata ID on [Wikidata](https://www.wikidata.org) (Mainz is `Q1720`) — and be careful, neighbouring Q-numbers are easy to confuse.

## Attribution

Data: “a11y-Score by Sozialhelden e.V., based on data © OpenStreetMap contributors”, published under the [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). Region names and Wikidata IDs come from [Wikidata](https://www.wikidata.org) (CC0). The `data/` snapshot (`exported_at 2026-11-03T15:39:21Z`) is a derived database under the same licence.
