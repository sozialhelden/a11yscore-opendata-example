"""
Prototype: short accessibility progress stats for citizens, generated with little
effort from the a11y-Score open data (regenerated daily).

Usage: pip install duckdb pandas pyarrow && python mainz_a11y_stats.py
Data:  https://a11yscore.org/open-data
Set A11YSCORE_PARQUET to run against a local snapshot instead of the live URL
(the e2e test does this with the pinned dump in data/).
Attribution: "a11y-Score by Sozialhelden e.V., based on data © OpenStreetMap contributors" (ODbL)
"""
import os

import duckdb
import pandas as pd

URL = os.environ.get(
    "A11YSCORE_PARQUET",
    "https://sozialhelden-opendata.fra1.digitaloceanspaces.com/a11yscore/v1/latest/dimension-combination-metrics.parquet",
)
CITY_NAME = "Mainz"
CITY_WIKIDATA_ID = "Q1720"  # Wikidata ID of Mainz
MIN_COMPLETENESS = 0.10  # categories with less survey completeness are cut off

rows = duckdb.sql(f"""
    SELECT dim2_name_en            AS place_type,
           a11yscore,
           d0_x_d1_x_d2_count      AS places_with_data,
           d0_x_d1_count,
           n_total,
           updated_at,
           is_parent_row
    FROM '{URL}'
    WHERE chart_kind = 'category'
      AND dim0_wikidata_id = '{CITY_WIKIDATA_ID}'
      AND dim0_tree_slug = 'geography-4-levels'
      AND dimension_slug = 'tree-root-accessibility'
""").df()

total = rows[rows.is_parent_row].iloc[0]
bars = rows[~rows.is_parent_row].copy()
bars["places_total"] = bars.n_total
bars["score"] = (bars.a11yscore * 100).round(1)
bars["completeness"] = bars.places_with_data / bars.places_total
bars["coverage"] = (bars.completeness * 100).round(0).astype(int)
confident = bars[bars.completeness >= MIN_COMPLETENESS]
excluded = bars[bars.completeness < MIN_COMPLETENESS]

pivot = (
    confident.pivot_table(
        index="place_type",
        values=["score", "places_with_data", "places_total", "coverage"],
        aggfunc="first",
    )
    .rename(
        columns={
            "score": "Score (0-100)",
            "places_with_data": "Places with data",
            "places_total": "Places total",
            "coverage": "Coverage %",
        }
    )
    .rename_axis("Place type")
    .sort_values("Score (0-100)", ascending=False)
)
print(pivot.to_string())

best = confident.loc[confident.score.idxmax()]
worst = confident.loc[confident.score.idxmin()]
overall_score = round(total.a11yscore * 100)
covered = f"{int(total.d0_x_d1_count):,}"
all_places = f"{int(total.n_total):,}"

print()
print(
    f"Accessibility in {CITY_NAME}: {overall_score} of 100 points "
    f"(a11y-Score, as of {total.updated_at:%Y-%m-%d}). "
    f"The most accessible places are in the \u201c{best.place_type}\u201d category "
    f"({best.score:.0f} points); the greatest need for action is in "
    f"\u201c{worst.place_type}\u201d ({worst.score:.0f} points). "
    f"These figures are based on {covered} places with accessibility data out of "
    f"{all_places} recorded places in total — every improvement in OpenStreetMap "
    f"updates this status daily."
)
if not excluded.empty:
    print(
        f"Not rated due to insufficient data (coverage below {MIN_COMPLETENESS:.0%}): "
        + ", ".join(
            f"\u201c{r.place_type}\u201d ({r.coverage}%)"
            for _, r in excluded.sort_values("coverage").iterrows()
        )
        + "."
    )
print()
print("Source: a11y-Score by Sozialhelden e.V., based on data © OpenStreetMap contributors (ODbL)")
