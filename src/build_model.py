"""
Generate the Power BI project scaffolding and semantic-model table definitions
(TMDL) from the CSVs in powerbi/data/.

A Power BI project (.pbip) is a folder of text files: a .SemanticModel folder
describing tables, columns and relationships, and a .Report folder describing
pages and visuals. This script writes the model side; build_pbir.py writes the
report side. Both are generated from code so the dashboard is reproducible.

Run:    python src/build_model.py       (after build_dashboard_data.py)
"""
import json
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
NAME = "hamilton_debt_assumption"
MODEL = PBI / f"{NAME}.SemanticModel"
REPORT = PBI / f"{NAME}.Report"
DATA = (PBI / "data").resolve()
TABLES = ["states", "ledger_long", "waterfall", "rollforward", "counterfactual", "stats",
          "tieout", "enclosure_d_tieout"]

# Columns that sort by another column (so steps show in ledger order, not alphabetical).
SORT_BY = {("ledger_long", "step"): "step_order", ("waterfall", "step"): "step_order",
           ("stats", "test"): "test_order", ("rollforward", "line"): "line_order",
           ("tieout", "line"): "line_order", ("enclosure_d_tieout", "state"): "line_order"}
# Geographic role so the filled map can geocode state names.
DATA_CATEGORY = {("states", "state"): "StateOrProvince", ("ledger_long", "state"): "StateOrProvince",
                 ("counterfactual", "state"): "StateOrProvince"}
# Many-side column -> states.state, so a region slicer on states filters everything.
RELATIONSHIPS = [("ledger_long", "state"), ("counterfactual", "state"), ("enclosure_d_tieout", "state")]


def uid() -> str:
    return str(uuid.uuid4())


def fmt_for(name: str, series: pd.Series) -> str:
    """Display format by column-name convention."""
    if name in ("pop_total_1790", "pop_enslaved_1790", "pop_free_1790"):
        return "#,0"
    if name.endswith("_pct"):
        return "0.0"
    if name == "p_value":
        return "0.000"
    # Accounting convention: negatives in parentheses, never a minus sign.
    if name.endswith("_m"):
        return "#,0.00;(#,0.00)"
    if "per_capita" in name or "per_free_person" in name:
        return "$#,0.00;($#,0.00)"
    if "usd" in name:
        return "$#,0;($#,0)"
    if name.endswith("_order") or name.endswith("_rank"):
        return "0"
    if pd.api.types.is_integer_dtype(series):
        return "#,0"
    if pd.api.types.is_float_dtype(series):
        return "#,0.00"
    return ""


def col_spec(series: pd.Series) -> tuple[str, str]:
    if pd.api.types.is_integer_dtype(series):
        return "int64", "Int64.Type"
    if pd.api.types.is_float_dtype(series):
        return "double", "type number"
    return "string", "type text"


def table_tmdl(name: str, df: pd.DataFrame) -> str:
    out = [f"table {name}", f"\tlineageTag: {uid()}", ""]
    pq_types = []
    for c in df.columns:
        dtype, pqtype = col_spec(df[c])
        fmt = fmt_for(c, df[c])
        pq_types.append(f'{{"{c}", {pqtype}}}')
        out += [f"\tcolumn {c}", f"\t\tdataType: {dtype}"]
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out += [f"\t\tlineageTag: {uid()}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {c}"]
        if (name, c) in SORT_BY:
            out.append(f"\t\tsortByColumn: {SORT_BY[(name, c)]}")
        if (name, c) in DATA_CATEGORY:
            out.append(f"\t\tdataCategory: {DATA_CATEGORY[(name, c)]}")
        out += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
    path = str(DATA / f"{name}.csv")
    out += [
        f"\tpartition {name} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\t\tlet",
        f'\t\t\t\t  Source = Csv.Document(File.Contents("{path}"), '
        f"[Delimiter = \",\", Columns = {len(df.columns)}, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),",
        '\t\t\t\t  #"Promoted headers" = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),',
        '\t\t\t\t  #"Changed column type" = Table.TransformColumnTypes(#"Promoted headers", {'
        + ", ".join(pq_types) + "})",
        "\t\t\t\tin",
        '\t\t\t\t  #"Changed column type"',
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    return "\n".join(out)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def platform(kind: str) -> str:
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind, "displayName": NAME},
        "config": {"version": "2.0", "logicalId": uid()},
    }, indent=2)


def scaffold() -> None:
    """Project, model and report container files. Only written if missing, so
    Desktop-generated ids and settings survive re-runs."""
    files = {
        PBI / f"{NAME}.pbip": json.dumps({"version": "1.0",
                                          "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                                          "settings": {"enableAutoRecovery": True}}, indent=2),
        MODEL / ".platform": platform("SemanticModel"),
        MODEL / "definition.pbism": json.dumps({"version": "4.2", "settings": {}}, indent=2),
        MODEL / "definition" / "database.tmdl": "database\n\tcompatibilityLevel: 1606\n",
        MODEL / "definition" / "cultures" / "en-US.tmdl":
            'cultureInfo en-US\n\n\tlinguisticMetadata =\n\t\t\t{"Version": "2.0.0", "Language": "en-US"}\n',
        MODEL / ".pbi" / "editorSettings.json": json.dumps({
            "version": "1.0", "autodetectRelationships": False, "parallelQueryLoading": False,
            "typeDetectionEnabled": True, "relationshipImportEnabled": True,
            "shouldNotifyUserOfNameConflictResolution": True}, indent=2),
        REPORT / ".platform": platform("Report"),
        REPORT / "definition.pbir": json.dumps({"version": "4.0", "datasetReference": {
            "byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2),
    }
    for p, text in files.items():
        if not p.exists():
            write(p, text)
            print(f"created {p.relative_to(ROOT)}")


def model_tmdl() -> str:
    return "\n".join([
        "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US", "\tvalueFilterBehavior: independent",
        "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        f"annotation PBI_QueryOrder = {json.dumps(TABLES)}", "",
        'annotation PBI_ProTooling = ["DevMode"]', "",
        *[f"ref table {t}" for t in TABLES], "",
        "ref cultureInfo en-US", "",
    ])


def relationships_tmdl() -> str:
    blocks = [f"relationship {uid()}\n\tfromColumn: {t}.{c}\n\ttoColumn: states.state"
              for t, c in RELATIONSHIPS]
    return "\n\n".join(blocks) + "\n"


def clear_desktop_cache() -> None:
    """Delete Power BI Desktop's per-user data cache so it rebuilds from the
    files on disk. Power BI Desktop must be closed."""
    for cache in PBI.glob("*.SemanticModel/.pbi/cache.abf"):
        cache.unlink()
        print(f"cleared {cache.relative_to(ROOT)}")


def main() -> None:
    scaffold()
    clear_desktop_cache()
    for name in TABLES:
        df = pd.read_csv(DATA / f"{name}.csv")
        write(MODEL / "definition" / "tables" / f"{name}.tmdl", table_tmdl(name, df))
        print(f"tables/{name}.tmdl: {len(df.columns)} columns")
    write(MODEL / "definition" / "model.tmdl", model_tmdl())
    write(MODEL / "definition" / "relationships.tmdl", relationships_tmdl())
    print(f"model.tmdl: {len(TABLES)} tables, {len(RELATIONSHIPS)} relationships")


if __name__ == "__main__":
    main()
