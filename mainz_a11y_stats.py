"""
Prototype: short accessibility progress stats for citizens, generated with little
effort from the a11y-Score open data (regenerated daily).

Usage: pip install duckdb pandas pyarrow && python mainz_a11y_stats.py
Data:  https://a11yscore.org/open-data
Attribution: "a11y-Score by Sozialhelden e.V., based on data © OpenStreetMap contributors" (ODbL)
"""
import duckdb
import pandas as pd

URL = "https://sozialhelden-opendata.fra1.digitaloceanspaces.com/a11yscore/v1/latest/dimension-combination-metrics.parquet"
CITY_NAME = "Mainz"
CITY_WIKIDATA_ID = "Q1720"  # Wikidata ID of Mainz
MIN_COMPLETENESS = 0.10  # categories with less survey completeness are cut off

rows = duckdb.sql(f"""
    SELECT dim2_name_de            AS place_type,
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
    .rename(columns={"score": "Score (0-100)", "places_with_data": "Orte mit Daten", "places_total": "Orte gesamt", "coverage": "Abdeckung %"})
    .rename_axis("Ortstyp")
    .sort_values("Score (0-100)", ascending=False)
)
print(pivot.to_string())

best = confident.loc[confident.score.idxmax()]
worst = confident.loc[confident.score.idxmin()]
overall_score = round(total.a11yscore * 100)
covered = f"{int(total.d0_x_d1_count):,}".replace(",", ".")
all_places = f"{int(total.n_total):,}".replace(",", ".")

print()
print(
    f"Barrierefreiheit in {CITY_NAME}: {overall_score} von 100 Punkten "
    f"(a11y-Score, Stand {total.updated_at:%d.%m.%Y}). "
    f"Am zugänglichsten sind Orte der Kategorie „{best.place_type}“ ({best.score:.0f} Punkte), "
    f"den größten Handlungsbedarf gibt es bei „{worst.place_type}“ ({worst.score:.0f} Punkte). "
    f"Grundlage sind {covered} Orte mit Barrierefreiheitsdaten von insgesamt "
    f"{all_places} erfassten Orten — jede Verbesserung in OpenStreetMap "
    f"aktualisiert diesen Stand täglich."
)
if not excluded.empty:
    print(
        f"Nicht bewertet wegen zu geringer Datengrundlage "
        f"(Abdeckung unter {MIN_COMPLETENESS:.0%}): "
        + ", ".join(f"„{r.place_type}“ ({r.coverage}%)" for _, r in excluded.sort_values("coverage").iterrows())
        + "."
    )
print()
print("Quelle: a11y-Score by Sozialhelden e.V., based on data © OpenStreetMap contributors (ODbL)")
