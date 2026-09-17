"""
Generate the Power BI report definition (PBIR files) for the dashboard.

Power BI Desktop can save a report as a "project" (.pbip): a folder of JSON
files, one per page and one per visual. This script writes those files, so the
dashboard layout is code - reviewable, version-controlled, and rebuildable.

Workflow:
  1. python src/analysis.py                (rebuild output/assumption_ledger.csv)
  2. python src/build_dashboard_data.py    (rebuild the powerbi/data CSVs)
  3. python src/build_model.py             (rebuild table definitions if columns changed)
  4. python src/build_pbir.py              (write pages + visuals)
  5. Open powerbi/hamilton_debt_assumption.pbip in Power BI Desktop, click Refresh.

The report is laid out as a set of audit workpapers - lettered schedules, a
tie-out page, a roll-forward, a T-account, totals on every table and negatives in
parentheses - with one chart form per schedule chosen to match how an accountant
reads that ledger: a waterfall for the bridge, a matrix for state x step, stacked
bars and a gauge for utilization, a T-account and treemap for the 1793 settlement, a scatter
for the fairness test, and a diverging bar with a basis slicer for apportionment.

Reference: https://learn.microsoft.com/power-bi/developer/projects/projects-report
"""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "powerbi" / "hamilton_debt_assumption.Report" / "definition"
PAGES = REPORT / "pages"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
PAGE_W, PAGE_H = 1920, 1080
M = 48                     # page margin
GAP = 24                   # gap between visuals
BAND_H = 112               # header band height
TOP = BAND_H + 32          # first row of content
TOTAL_PAGES = 8

SUM, AVG, MIN, MAX = 0, 1, 3, 4   # Power BI aggregation codes

# ---- palette: ledger paper and ink. One colour for money, one for red ink.
NAVY = "#1F3A5F"           # ink
GOLD = "#8C6D1F"           # specie / relief
RED = "#9B2D20"            # red ink / debtor / does not foot
TEAL = "#2F7D6D"           # creditor / ties
GREY = "#7A8290"
INK = "#22262B"
WHITE = "#FFFFFF"
PAGE_BG = "#F3EFE6"        # ledger paper
GRID = "#D9D2C3"           # rule lines
PALE = "#EAE4D6"           # unused / muted
FONT = "Segoe UI"          # body
HFONT = "Georgia"          # headings, like a printed ledger
MONO = "Consolas"          # figures in tables
REGION_COLORS = [("New England", NAVY), ("Middle", GREY), ("Southern", RED)]
POSITION_COLORS = [("Creditor", TEAL), ("Debtor", RED)]
STATUS_COLORS = [("Ties", TEAL), ("Ties (rounded)", TEAL), ("Immaterial", GOLD), ("Does not foot", RED)]


# ---------------------------------------------------------------- primitives
def oid(label: str) -> str:
    """Deterministic 20-char hex object name, so re-runs don't churn file names."""
    return hashlib.md5(label.encode()).hexdigest()[:20]


def lit(value: str) -> dict:
    """A literal formatting value. Strings are 'quoted', ints end in L, doubles in D."""
    return {"expr": {"Literal": {"Value": value}}}


def color(hex_: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_}'")}}


def col(table: str, name: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def proj_col(table: str, name: str, active: bool = False, display: str | None = None) -> dict:
    p = {"field": col(table, name), "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if active:
        p["active"] = True
    if display:
        p["displayName"] = display
    return p


def proj_agg(table: str, name: str, display: str, fn: int = SUM) -> dict:
    tag = {SUM: "Sum", AVG: "Avg", MIN: "Min", MAX: "Max"}[fn]
    return {
        "field": {"Aggregation": {"Expression": col(table, name), "Function": fn}},
        "queryRef": f"{tag}({table}.{name})",
        "nativeQueryRef": f"{tag} of {name}",
        "displayName": display,
    }


# Column -> DAX measure defined in build_model.py. Tables, cards and totals rows read
# measures; where no measure exists, fall back to an implicit aggregation.
MEASURE_FOR = {
    ("states", "estimate_1790_usd"): "Hamilton estimate",
    ("states", "quota_usd"): "Act quota",
    ("states", "quota_usd_2025"): "Act quota (2025 $)",
    ("states", "quota_vs_estimate_usd"): "Quota less estimate",
    ("states", "subscribed_1792_usd"): "Subscribed Jan 1792",
    ("states", "assumed_usd"): "Assumed (final)",
    ("states", "assumed_usd_2025"): "Assumed (2025 $)",
    ("states", "quota_unused_usd"): "Unused quota",
    ("states", "takeup_pct"): "Take-up %",
    ("states", "settlement_usd"): "1793 settlement",
    ("states", "settlement_usd_2025"): "1793 settlement (2025 $)",
    ("states", "settlement_abs_usd"): "Settlement (absolute)",
    ("states", "net_position_usd"): "Net position",
    ("states", "net_position_usd_2025"): "Net position (2025 $)",
    ("states", "pop_total_1790"): "Population 1790",
    ("states", "pop_share_pct"): "Pop. share %",
    ("states", "quota_share_pct"): "Quota share %",
    ("states", "quota_per_capita"): "Quota per head",
    ("states", "assumed_per_capita"): "Relief per head",
    ("states", "settlement_per_capita"): "Settlement per head",
    ("states", "settlement_per_capita_2025"): "Settlement per head (2025 $)",
    ("states", "net_position_per_capita"): "Net per head",
    ("states", "net_position_per_capita_2025"): "Net per head (2025 $)",
    ("ledger_long", "usd_1790"): "GL 1790 $",
    ("ledger_long", "usd_2025"): "GL 2025 $",
    ("waterfall", "usd_1790_m"): "WF 1790 $ millions",
    ("rollforward", "usd_1790"): "RF 1790 $",
    ("rollforward", "usd_2025"): "RF 2025 $",
    ("counterfactual", "quota_usd"): "CF Act quota",
    ("counterfactual", "proportional_usd"): "CF per-head share",
    ("counterfactual", "gap_usd"): "CF quota less share",
    ("counterfactual", "gap_usd_2025"): "CF quota less share (2025 $)",
    ("stats", "p_value"): "p-value",
    ("tieout", "stated_usd"): "Stated",
    ("tieout", "computed_usd"): "Computed",
    ("tieout", "variance_usd"): "Variance",
    ("enclosure_d_tieout", "quota_usd"): "ED quota",
    ("enclosure_d_tieout", "subscribed_printed_usd"): "ED subscribed (as printed)",
    ("enclosure_d_tieout", "unsubscribed_printed_usd"): "ED unsubscribed (as printed)",
    ("enclosure_d_tieout", "unsubscribed_computed_usd"): "ED unsubscribed (computed)",
    ("enclosure_d_tieout", "variance_usd"): "ED variance",
    ("enclosure_d_tieout", "subscribed_reconciled_usd"): "ED subscribed (reconciled)",
}


def proj_measure(table: str, measure: str, display: str | None = None) -> dict:
    p = {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": measure}},
         "queryRef": f"{table}.{measure}", "nativeQueryRef": measure}
    if display:
        p["displayName"] = display
    return p


def proj_sum(table, name, display):
    m = MEASURE_FOR.get((table, name))
    return proj_measure(table, m, display) if m else proj_agg(table, name, display, SUM)


def proj_avg(table, name, display):
    m = MEASURE_FOR.get((table, name))
    return proj_measure(table, m, display) if m else proj_agg(table, name, display, AVG)


def series_colors(series: list[dict], colors: list[str]) -> list[dict]:
    return [{"properties": {"fill": color(c)}, "selector": {"metadata": s["queryRef"]}}
            for s, c in zip(series, colors)]


def category_colors(legend_field: dict, pairs: list[tuple[str, str]]) -> list[dict]:
    """Colour data points by the value of a legend column (e.g. region, creditor/debtor)."""
    entity = legend_field["field"]["Column"]["Expression"]["SourceRef"]["Entity"]
    prop = legend_field["field"]["Column"]["Property"]
    return [{"properties": {"fill": color(c)},
             "selector": {"data": [{"scopeId": {"Comparison": {
                 "ComparisonKind": 0,
                 "Left": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
                 "Right": {"Literal": {"Value": f"'{v}'"}}}}}]}}
            for v, c in pairs]


def in_filter(table: str, column: str, values: list, text: bool = False) -> dict:
    """Visual-level filter: table[column] IN values."""
    vals = [f"'{v}'" if text else f"{v}L" for v in values]
    return {
        "name": oid(f"filter-{table}-{column}-" + "-".join(map(str, values))),
        "field": col(table, column),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": table, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                                            "Property": column}}],
                "Values": [[{"Literal": {"Value": v}}] for v in vals],
            }}}],
        },
    }


def state_filter(states: list[str]) -> dict:
    return in_filter("states", "state", states, text=True)


# ---------------------------------------------------------------- visual shell
def container_style(title, subtitle, bg: str | None, title_color=NAVY, sub_color=GREY) -> dict:
    c = {
        "background": [{"properties": {"show": lit("true" if bg else "false"),
                                       "color": color(bg or WHITE), "transparency": lit("0L")}}],
        "border": [{"properties": {"show": lit("true" if bg else "false"), "color": color(GRID),
                                   "radius": lit("0L")}}],
        "dropShadow": [{"properties": {"show": lit("false")}}],
        "title": [{"properties": {"show": lit("true" if title else "false"),
                                  "text": lit(f"'{title or ''}'"),
                                  "fontFamily": lit(f"'{HFONT}'"), "fontSize": lit("13D"),
                                  "bold": lit("true"), "fontColor": color(title_color)}}],
        "subTitle": [{"properties": {"show": lit("true" if subtitle else "false"),
                                     "text": lit(f"'{subtitle or ''}'"),
                                     "fontFamily": lit(f"'{FONT}'"), "fontSize": lit("10D"),
                                     "fontColor": color(sub_color)}}],
    }
    if bg:
        c["padding"] = [{"properties": {"top": lit("12D"), "bottom": lit("12D"),
                                        "left": lit("14D"), "right": lit("14D")}}]
    return c


def visual(name, vtype, x, y, w, h, *, roles=None, title=None, subtitle=None, objects=None,
           filters=None, sort_by=None, sort_dir="Ascending", bg=WHITE, title_color=NAVY,
           sub_color=GREY) -> dict:
    v = {
        "$schema": f"{SCHEMA}/visualContainer/2.12.0/schema.json",
        "name": oid(name),
        "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0},
        "visual": {"visualType": vtype, "drillFilterOtherVisuals": True},
    }
    if roles:
        q = {"queryState": {r: {"projections": ps} for r, ps in roles.items()}}
        if sort_by:
            q["sortDefinition"] = {"sort": [{"field": sort_by, "direction": sort_dir}],
                                   "isDefaultSort": True}
        v["visual"]["query"] = q
    if objects:
        v["visual"]["objects"] = objects
    v["visual"]["visualContainerObjects"] = container_style(title, subtitle, bg, title_color, sub_color)
    if filters:
        v["filterConfig"] = {"filters": filters}
    return v


def textbox(name, x, y, w, h, runs, *, bg=None, spaced=False) -> dict:
    """runs = [(text, size_pt, bold, colour)] or (text, size, bold, colour, font); each its own paragraph."""
    paragraphs = []
    for run in runs:
        t, sz, b, c = run[:4]
        font = run[4] if len(run) > 4 else FONT
        paragraphs.append({"textRuns": [{"value": t, "textStyle": {
            "fontFamily": font, "fontSize": f"{sz}pt", "color": c,
            **({"fontWeight": "bold"} if b else {})}}]})
        if spaced:
            paragraphs.append({"textRuns": [{"value": " ", "textStyle": {"fontSize": "6pt"}}]})
    v = visual(name, "textbox", x, y, w, h, bg=bg)
    v["visual"]["objects"] = {"general": [{"properties": {"paragraphs": paragraphs}}]}
    return v


def axis_style(start=None, end=None, show_title=False, title=None) -> dict:
    p = {"showAxisTitle": lit("true" if show_title else "false"),
         "fontFamily": lit(f"'{FONT}'"), "fontSize": lit("10D"), "labelColor": color(GREY),
         "gridlineColor": color(GRID), "titleFontFamily": lit(f"'{FONT}'"),
         "titleColor": color(GREY), "titleFontSize": lit("10D")}
    if title:
        p["titleText"] = lit(f"'{title}'")
    if start is not None:
        p["start"] = lit(f"{start}L")
    if end is not None:
        p["end"] = lit(f"{end}L")
    return p


def legend(show=True, position="Top") -> list:
    return [{"properties": {"show": lit("true" if show else "false"), "position": lit(f"'{position}'"),
                            "showTitle": lit("false"), "fontFamily": lit(f"'{FONT}'"),
                            "fontSize": lit("10D"), "labelColor": color(INK)}}]


def data_labels(show=True, precision=1, units="1D") -> list:
    return [{"properties": {"show": lit("true" if show else "false"), "fontFamily": lit(f"'{MONO}'"),
                            "fontSize": lit("10D"), "color": color(INK),
                            "labelPrecision": lit(f"{precision}L"), "labelDisplayUnits": lit(units)}}]


def text_style(size=11, color_=INK, bold=False, font=FONT) -> dict:
    return {"fontFamily": lit(f"'{font}'"), "fontSize": lit(f"{size}D"), "fontColor": color(color_),
            **({"bold": lit("true")} if bold else {})}


def grid_style() -> dict:
    """Ledger rules: horizontal lines only, a heavier line under the header, no vertical rules."""
    return {"grid": [{"properties": {"rowPadding": lit("5L"), "gridHorizontal": lit("true"),
                                     "gridHorizontalColor": color(GRID), "gridHorizontalWeight": lit("1L"),
                                     "gridVertical": lit("false"), "outlineColor": color(NAVY),
                                     "outlineWeight": lit("2L")}}]}


# ---------------------------------------------------------------- visual builders
def bar_chart(name, x, y, w, h, *, category, series, title, subtitle=None, colors=None,
              legend_field=None, legend_pairs=None, filters=None, stacked=False, labels=True,
              x_title=None, sort_field=None, sort_dir="Descending", show_legend=None,
              precision=2) -> dict:
    """Horizontal bars. Colour by series (colors) or by a legend column (legend_field + pairs)."""
    roles = {"Category": [category], "Y": series}
    if legend_field is not None:
        roles["Series"] = [legend_field]
    objects = {
        "legend": legend(show_legend if show_legend is not None else (len(series) > 1 or legend_field is not None)),
        "categoryAxis": [{"properties": axis_style()}],
        "valueAxis": [{"properties": axis_style(show_title=bool(x_title), title=x_title)}],
        "labels": data_labels(labels, precision),
    }
    if legend_field is not None:
        objects["dataPoint"] = category_colors(legend_field, legend_pairs)
    elif colors:
        objects["dataPoint"] = series_colors(series, colors)
    sort = sort_field if sort_field is not None else series[0]["field"]
    return visual(name, "barChart" if stacked else "clusteredBarChart", x, y, w, h,
                  roles=roles, sort_by=sort, sort_dir=sort_dir, title=title, subtitle=subtitle,
                  filters=filters, objects=objects)


def column_chart(name, x, y, w, h, *, category, series, colors, title, subtitle=None,
                 filters=None, y_title=None, show_legend=True, sort_field=None) -> dict:
    return visual(
        name, "clusteredColumnChart", x, y, w, h,
        roles={"Category": [category], "Y": series},
        sort_by=sort_field if sort_field is not None else series[0]["field"], sort_dir="Descending",
        title=title, subtitle=subtitle, filters=filters,
        objects={"dataPoint": series_colors(series, colors),
                 "legend": legend(show_legend),
                 "categoryAxis": [{"properties": axis_style()}],
                 "valueAxis": [{"properties": axis_style(None, None, bool(y_title), y_title)}]})


def waterfall(name, x, y, w, h, *, category, value, title, subtitle=None, filters=None,
              precision=2) -> dict:
    return visual(
        name, "waterfallChart", x, y, w, h,
        roles={"Category": [category], "Y": [value]}, sort_by=category["field"],
        title=title, subtitle=subtitle, filters=filters,
        objects={"sentimentColors": [{"properties": {"increaseFill": color(TEAL),
                                                     "decreaseFill": color(RED),
                                                     "totalFill": color(NAVY)}}],
                 "categoryAxis": [{"properties": axis_style()}],
                 "valueAxis": [{"properties": axis_style(0)}],
                 "labels": data_labels(True, precision)})


def matrix(name, x, y, w, h, *, rows, columns, values, title, subtitle=None, filters=None,
           totals=True) -> dict:
    return visual(
        name, "pivotTable", x, y, w, h,
        roles={"Rows": [rows], "Columns": [columns], "Values": values},
        title=title, subtitle=subtitle, filters=filters,
        objects={**grid_style(),
                 "columnHeaders": [{"properties": {**text_style(10, NAVY, True, HFONT),
                                                   "alignment": lit("'Right'"), "wordWrap": lit("true")}}],
                 "rowHeaders": [{"properties": text_style(10, INK)}],
                 "values": [{"properties": text_style(10, INK, False, MONO)}],
                 "subTotals": [{"properties": {"rowSubtotals": lit("true" if totals else "false"),
                                               "columnSubtotals": lit("false"),
                                               **text_style(10, NAVY, True, MONO)}}]})


def table(name, x, y, w, h, *, values, title, subtitle=None, filters=None, sort_by=None,
          sort_dir="Descending", totals=True, status_field=None) -> dict:
    objects = {**grid_style(),
               "columnHeaders": [{"properties": {**text_style(10, NAVY, True, HFONT), "wordWrap": lit("true")}}],
               "values": [{"properties": {**text_style(10, INK, False, MONO), "wordWrap": lit("true")}}],
               "total": [{"properties": {"totals": lit("true" if totals else "false"),
                                         **text_style(10, NAVY, True, MONO)}}]}
    v = visual(name, "tableEx", x, y, w, h, roles={"Values": values}, sort_by=sort_by, sort_dir=sort_dir,
               title=title, subtitle=subtitle, filters=filters, objects=objects)
    return v


def card(name, x, y, w, h, *, field, title, filters=None, accent=NAVY, precision=1,
         units="1D") -> dict:
    return visual(
        name, "card", x, y, w, h,
        roles={"Values": [field]}, title=title, filters=filters, title_color=GREY,
        objects={"labels": [{"properties": {"labelPrecision": lit(f"{precision}L"),
                                            "labelDisplayUnits": lit(units),
                                            "fontFamily": lit(f"'{MONO}'"), "fontSize": lit("30D"),
                                            "color": color(accent)}}],
                 "categoryLabels": [{"properties": {"show": lit("false")}}]})


def gauge(name, x, y, w, h, *, value, target, maximum, title, subtitle=None) -> dict:
    return visual(
        name, "gauge", x, y, w, h,
        roles={"Y": [value], "TargetValue": [target], "MaxValue": [maximum]},
        title=title, subtitle=subtitle,
        objects={"dataPoint": [{"properties": {"fill": color(GOLD), "target": color(NAVY)}}],
                 "labels": data_labels(True, 0, "1000000D"),
                 "calloutValue": [{"properties": {"fontFamily": lit(f"'{MONO}'"), "fontSize": lit("26D"),
                                                  "color": color(NAVY), "labelDisplayUnits": lit("1000000D"),
                                                  "labelPrecision": lit("2L")}}],
                 "axis": [{"properties": {"min": lit("0D")}}]})


def filled_map(name, x, y, w, h, *, location, legend_field, legend_pairs, tooltips, title,
               subtitle=None) -> dict:
    return visual(
        name, "filledMap", x, y, w, h,
        roles={"Category": [location], "Series": [legend_field], "Tooltips": tooltips},
        title=title, subtitle=subtitle,
        objects={"dataPoint": category_colors(legend_field, legend_pairs),
                 "legend": legend(True, "Bottom"),
                 "mapControls": [{"properties": {"autoZoom": lit("true"), "zoomButtons": lit("false")}}],
                 "mapStyles": [{"properties": {"mapTheme": lit("'grayscale'")}}]})


def treemap(name, x, y, w, h, *, group, details, value, title, subtitle=None, colors=None) -> dict:
    objects = {"labels": data_labels(True, 0, "1000000D"),
               "categoryLabels": [{"properties": {"show": lit("true"), "fontFamily": lit(f"'{FONT}'"),
                                                  "fontSize": lit("10D"), "color": color(WHITE)}}],
               "legend": legend(True, "Bottom")}
    if colors:
        objects["dataPoint"] = category_colors(group, colors)
    return visual(name, "treemap", x, y, w, h,
                  roles={"Group": [group], "Details": [details], "Values": [value]},
                  title=title, subtitle=subtitle, objects=objects)


def scatter(name, x, y, w, h, *, category, xf, yf, title, subtitle=None, legend_field=None,
            legend_pairs=None, trend=True, x_title=None, y_title=None) -> dict:
    roles = {"Category": [category], "X": [xf], "Y": [yf]}
    if legend_field is not None:
        roles["Series"] = [legend_field]
    objects = {
        "categoryAxis": [{"properties": axis_style(show_title=bool(x_title), title=x_title)}],
        "valueAxis": [{"properties": axis_style(show_title=bool(y_title), title=y_title)}],
        "categoryLabels": [{"properties": {"show": lit("true"), "fontFamily": lit(f"'{FONT}'"),
                                           "fontSize": lit("9D"), "color": color(INK)}}],
        "legend": legend(legend_field is not None, "Bottom"),
        "trend": [{"properties": {"show": lit("true" if trend else "false"), "lineColor": color(GOLD),
                                  "style": lit("'dotted'"), "transparency": lit("0L")}}],
    }
    objects["dataPoint"] = (category_colors(legend_field, legend_pairs) if legend_field is not None
                            else [{"properties": {"fill": color(NAVY)}}])
    return visual(name, "scatterChart", x, y, w, h, roles=roles, title=title, subtitle=subtitle,
                  objects=objects)


def slicer(name, x, y, w, h, *, field, title, single=False) -> dict:
    return visual(
        name, "slicer", x, y, w, h, roles={"Values": [field]}, title=title, title_color=GREY,
        objects={"data": [{"properties": {"mode": lit("'Basic'")}}],
                 "general": [{"properties": {"orientation": lit("0L")}}],
                 "header": [{"properties": {"show": lit("false")}}],
                 "selection": [{"properties": {"singleSelect": lit("true" if single else "false"),
                                               "selectAllCheckboxEnabled": lit("false")}}],
                 "items": [{"properties": text_style(10, INK)}]})


def header(prefix: str, schedule: str, headline: str, caption: str, page_no: int) -> list[dict]:
    """Full-width band: schedule letter, the page's one-sentence takeaway, workpaper caption."""
    return [
        textbox(f"{prefix}-band", 0, 0, PAGE_W, BAND_H, [(" ", 4, False, NAVY)], bg=NAVY),
        textbox(f"{prefix}-schedule", M, 20, 120, BAND_H - 24,
                [(schedule, 30, True, "#C9B77A", HFONT)]),
        textbox(f"{prefix}-headline", M + 120, 18, PAGE_W - 2 * M - 300, BAND_H - 24,
                [(headline, 18, True, WHITE, HFONT), (caption, 10, False, "#C5CEDC")]),
        textbox(f"{prefix}-pageno", PAGE_W - M - 170, 22, 170, 70,
                [(f"Schedule {schedule}  ·  {page_no} of {TOTAL_PAGES}", 10, False, "#C5CEDC"),
                 ("Prepared by R. Barry", 10, False, "#C5CEDC"),
                 ("1790 $ · (2025 $ at 36.3x)", 10, False, "#C9B77A")]),
    ]


def kpi_row(prefix: str, cards: list[dict], y: int = TOP, h: int = 130) -> list[dict]:
    n = len(cards)
    w = (PAGE_W - 2 * M - (n - 1) * GAP) / n
    return [card(f"{prefix}-kpi-{i}", M + i * (w + GAP), y, w, h, **c) for i, c in enumerate(cards)]


def page(name: str, display: str, visuals: list[dict],
         no_filter: list[tuple[str, str]] | None = None) -> str:
    pname = oid("page-" + name)
    pdir = PAGES / pname
    pdir.mkdir(parents=True, exist_ok=True)
    pj = {
        "$schema": f"{SCHEMA}/page/2.1.0/schema.json",
        "name": pname, "displayName": display, "displayOption": "FitToPage",
        "height": PAGE_H, "width": PAGE_W,
        "objects": {"background": [{"properties": {"color": color(PAGE_BG),
                                                   "transparency": lit("0L")}}]},
    }
    if no_filter:
        pj["visualInteractions"] = [{"source": oid(s), "target": oid(t), "type": "NoFilter"}
                                    for s, t in no_filter]
    (pdir / "page.json").write_text(json.dumps(pj, indent=2), encoding="utf-8")
    for v in visuals:
        vdir = pdir / "visuals" / v["name"]
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
    return pname


# ---------------------------------------------------------------- shared fields
STATE = proj_col("states", "state", active=True, display="State")
REGION = proj_col("states", "region", display="Region")
POSITION = proj_col("states", "position_1793", display="1793 position")
QUOTA = proj_sum("states", "quota_usd", "Act quota")
QUOTA_25 = proj_sum("states", "quota_usd_2025", "Act quota (2025 $)")
ASSUMED = proj_sum("states", "assumed_usd", "Assumed (final)")
ASSUMED_25 = proj_sum("states", "assumed_usd_2025", "Assumed (2025 $)")
UNUSED = proj_sum("states", "quota_unused_usd", "Unused quota")
ESTIMATE = proj_sum("states", "estimate_1790_usd", "Hamilton estimate")
SUBSCRIBED = proj_sum("states", "subscribed_1792_usd", "Subscribed Jan 1792")
VARIANCE = proj_sum("states", "quota_vs_estimate_usd", "Quota less estimate")
SETTLEMENT = proj_sum("states", "settlement_usd", "1793 settlement")
SETTLEMENT_25 = proj_sum("states", "settlement_usd_2025", "1793 settlement (2025 $)")
NET = proj_sum("states", "net_position_usd", "Net position")
NET_25 = proj_sum("states", "net_position_usd_2025", "Net position (2025 $)")
QUOTA_PC = proj_avg("states", "quota_per_capita", "Quota per head")
ASSUMED_PC = proj_avg("states", "assumed_per_capita", "Relief per head")
SETTLEMENT_PC = proj_avg("states", "settlement_per_capita", "Settlement per head")
SETTLEMENT_PC_25 = proj_avg("states", "settlement_per_capita_2025", "Settlement per head (2025 $)")
NET_PC = proj_avg("states", "net_position_per_capita", "Net per head")
NET_PC_25 = proj_avg("states", "net_position_per_capita_2025", "Net per head (2025 $)")
TAKEUP = proj_avg("states", "takeup_pct", "Take-up %")
POP = proj_sum("states", "pop_total_1790", "Population 1790")
POP_SHARE = proj_sum("states", "pop_share_pct", "Pop. share %")
QUOTA_SHARE = proj_sum("states", "quota_share_pct", "Quota share %")


# ================================================================ Schedule A - summary & opinion
def page_summary() -> str:
    y0 = TOP + 130 + GAP
    h = PAGE_H - y0 - M
    left_w = (PAGE_W - 2 * M - GAP) * 0.40
    right_w = PAGE_W - 2 * M - GAP - left_w
    rx = M + left_w + GAP
    top_h = (h - GAP) * 0.5
    bot_h = h - GAP - top_h

    opinion = [
        ("Opinion", 15, True, NAVY, HFONT),
        ("Method: not defensible. Six of thirteen states filed returns. The two largest were cut "
         "by a quarter. Four states with no return got $3.1M by round number.", 11, False, INK),
        ("Outcome: defensible. 85% of the quota was used. The states that over-subscribed were the "
         "ones Hamilton said owed the most. The 1793 audit confirmed the biggest recipients (MA, SC) "
         "were the biggest creditors. Relief tracked contribution.", 11, False, INK),
        ("Madison: wrong on his own state. The audit he demanded found Virginia a net debtor, "
         "$100,879.", 11, False, INK),
        ("Basis of preparation", 13, True, NAVY, HFONT),
        ("Five primary ledgers, each footed before use (Schedule B). One does not foot: a $500,000 "
         "line error in the 1792 subscription table, reconciled and disclosed.", 10, False, GREY),
        ("1790 specie dollars; 2025 dollars at 36.3x CPI. $21.5M was ~11% of 1790 GDP, about "
         "$3.4 trillion in today's economy.", 10, False, GREY),
    ]
    vis = header(
        "p0", "A", "Was Hamilton's 1790 debt assumption fair?",
        "Reconciliation of $21.5M of assumed state war debt through five Treasury ledgers, 1790-1793. "
        "Sources: Founders Online (National Archives), U.S. Treasury, First Census. "
        "github.com/josephrbarry/hamilton-debt-assumption", 1,
    ) + kpi_row("p0", [
        dict(field=QUOTA, title="Authorized, Funding Act 1790", units="1000000D", precision=1),
        dict(field=ASSUMED, title="Assumed by 1793", units="1000000D", precision=2, accent=GOLD),
        dict(field=ASSUMED_25, title="Assumed, in 2025 $", units="1000000D", precision=0, accent=GOLD),
        dict(field=UNUSED, title="Quota unused", units="1000000D", precision=2, accent=RED),
        dict(field=proj_avg("states", "takeup_pct", "Utilization %"), title="Utilization, %", precision=0, accent=TEAL),
        dict(field=QUOTA_PC, title="South Carolina quota per head (mean $5.31)",
             filters=[state_filter(["South Carolina"])], precision=2, accent=RED),
    ]) + [
        textbox("p0-opinion", M, y0, left_w, h, opinion, bg=WHITE, spaced=True),
        waterfall("p0-bridge", rx, y0, right_w * 0.55 - GAP / 2, top_h,
                  category=proj_col("waterfall", "step", active=True),
                  value=proj_sum("waterfall", "usd_1790_m", "1790 $ millions"),
                  title="Bridge: authorized to assumed, 1790 $ millions",
                  subtitle="2025 $: $780M authorized -> $663M assumed."),
        table("p0-rollforward", rx + right_w * 0.55 + GAP / 2, y0, right_w * 0.45 - GAP / 2, top_h,
              values=[proj_col("rollforward", "line", display="Roll-forward"),
                      proj_sum("rollforward", "usd_1790", "1790 $"),
                      proj_sum("rollforward", "usd_2025", "2025 $")],
              title="Roll-forward schedule",
              subtitle="Foots to $18,271,786 assumed (Bayley).",
              sort_by=proj_col("rollforward", "line")["field"], sort_dir="Ascending", totals=True),
        table("p0-ledger", rx, y0 + top_h + GAP, right_w, bot_h,
              values=[STATE, ESTIMATE, QUOTA, ASSUMED, SETTLEMENT, NET, NET_25],
              title="Summary ledger by state, 1790 $ (net position also in 2025 $)",
              subtitle="Estimate = Schedule E, Jan 1790. Quota = Funding Act. Assumed = Treasury final. "
                       "Settlement = Commissioners, 1793. Net = assumed + settlement. Blank = no return filed.",
              sort_by=NET["field"], sort_dir="Descending", totals=True),
    ]
    return page("summary", "A · Summary & opinion", vis)


# ================================================================ Schedule B - tie-out
def page_tieout() -> str:
    h = PAGE_H - TOP - M
    top_h = (h - GAP) * 0.42
    bot_h = h - GAP - top_h
    left_w = (PAGE_W - 2 * M - GAP) * 0.66
    right_w = PAGE_W - 2 * M - GAP - left_w
    rx = M + left_w + GAP

    note = [
        ("Tie-out procedure", 13, True, NAVY, HFONT),
        ("1.  Foot every column of every source table and compare to the total the document prints.", 10, False, INK),
        ("2.  Where a total does not foot, tie each line: quota less subscribed must equal unsubscribed.", 10, False, INK),
        ("3.  Isolate the line, quantify the variance, decide materiality, disclose.", 10, False, INK),
        ("Finding", 13, True, RED, HFONT),
        ("Enclosure D (Treasury, 25 Jan 1792) prints subscriptions totalling $18,328,186.21. The column sums "
         "to $17,798,186.21. Line-level tie-out isolates the whole $500,000 in North Carolina: quota "
         "$2,400,000 less printed subscribed $1,166,355.57 gives $1,233,644.43 unsubscribed, but the "
         "document prints $733,644.43. The reconciled figure $1,666,355.57 is used throughout.", 10, False, INK),
        ("After correction the column is $30,000 short of the printed total; source not identified. Maryland "
         "is $30 out - immaterial. The document's own totals are internally consistent (quota less "
         "unsubscribed plus over-subscribed = $18,328,186), so the error sits in one printed line, not "
         "in the Treasury's arithmetic.", 10, False, INK),
        ("Every other document ties.", 10, True, TEAL),
    ]
    vis = header(
        "p1", "B", "Tie-out: four of five source documents foot. One does not.",
        "Each table was footed against its own printed total before any analysis. Ties = variance under $1. "
        "Ties (rounded) = under $5,000 and explained. Does not foot = investigated and disclosed below.", 2,
    ) + [
        table("p1-tieout", M, TOP, left_w, top_h,
              values=[proj_col("tieout", "document", display="Document"),
                      proj_col("tieout", "line", display="Line footed"),
                      proj_sum("tieout", "stated_usd", "Stated"),
                      proj_sum("tieout", "computed_usd", "Computed"),
                      proj_sum("tieout", "variance_usd", "Variance"),
                      proj_col("tieout", "status", display="Status")],
              title="Footing schedule", subtitle="Variance = computed less stated. Negatives in parentheses.",
              sort_by=proj_col("tieout", "line")["field"], sort_dir="Ascending", totals=False),
        bar_chart("p1-var", rx, TOP, right_w, top_h,
                  category=proj_col("tieout", "line", active=True), series=[proj_sum("tieout", "variance_usd", "Variance")],
                  legend_field=proj_col("tieout", "status"), legend_pairs=STATUS_COLORS,
                  title="Variance by line footed, 1790 $", subtitle="Red = does not foot.",
                  labels=True, precision=0, sort_field=proj_col("tieout", "line")["field"], sort_dir="Ascending",
                  show_legend=False),
        table("p1-encd", M, TOP + top_h + GAP, left_w, bot_h,
              values=[proj_col("enclosure_d_tieout", "state", display="State"),
                      proj_sum("enclosure_d_tieout", "quota_usd", "Quota"),
                      proj_sum("enclosure_d_tieout", "subscribed_printed_usd", "Subscribed (as printed)"),
                      proj_sum("enclosure_d_tieout", "unsubscribed_printed_usd", "Unsubscribed (as printed)"),
                      proj_sum("enclosure_d_tieout", "unsubscribed_computed_usd", "Unsubscribed (computed)"),
                      proj_sum("enclosure_d_tieout", "variance_usd", "Variance"),
                      proj_col("enclosure_d_tieout", "status", display="Status"),
                      proj_sum("enclosure_d_tieout", "subscribed_reconciled_usd", "Subscribed (reconciled)")],
              title="Enclosure D line-level tie-out: quota less subscribed = unsubscribed",
              subtitle="Statement of Subscriptions to the Loan, Treasury Department, 25 January 1792. Totals row "
                       "reproduces the document's footing problem.",
              sort_by=proj_col("enclosure_d_tieout", "state")["field"], sort_dir="Ascending", totals=True),
        textbox("p1-note", rx, TOP + top_h + GAP, right_w, bot_h, note, bg=WHITE, spaced=True),
    ]
    return page("tieout", "B · Tie-out", vis)


# ================================================================ Schedule C - the ledger
def page_ledger() -> str:
    h = PAGE_H - TOP - M
    left_w = (PAGE_W - 2 * M - GAP) * 0.56
    right_w = PAGE_W - 2 * M - GAP - left_w
    rx = M + left_w + GAP
    top_h = (h - GAP) * 0.5

    vis = header(
        "p2", "C", "The ledger: each state carried through estimate, quota, subscription, assumption and settlement.",
        "Columns are documents. Schedule E (Jan 1790), Funding Act sec. 14 (Aug 1790), Enclosure D (Jan 1792), "
        "Treasury final (Bayley, to 1793), Commissioners' settlement (Jun 1793). Blank = no return filed.", 3,
    ) + [
        matrix("p2-matrix", M, TOP, left_w, h,
               rows=STATE, columns=proj_col("ledger_long", "step", display="Step"),
               values=[proj_sum("ledger_long", "usd_1790", "1790 $")],
               title="General ledger: state x document, 1790 $",
               subtitle="Read across a row to follow one state. Totals row foots each column to its Schedule B figure.",
               totals=True),
        column_chart("p2-columns", rx, TOP, right_w, top_h,
                     category=STATE, series=[ESTIMATE, QUOTA, ASSUMED], colors=[PALE, NAVY, GOLD],
                     title="Estimate, quota, assumed - by state, 1790 $",
                     subtitle="No pale bar = no return on file. MA and SC reported $5.2M / $5.4M and were capped at $4.0M.",
                     sort_field=QUOTA["field"]),
        table("p2-variance", rx, TOP + top_h + GAP, right_w, h - top_h - GAP,
              values=[STATE, ESTIMATE, QUOTA, VARIANCE, QUOTA_25],
              title="Variance schedule: Act quota less Hamilton's estimate",
              subtitle="Congress cut ($3,144,950) from the four largest reported debts and wrote NH, PA, MD in at "
                       "exactly Hamilton's round numbers. Last column: quota in 2025 $.",
              sort_by=VARIANCE["field"], sort_dir="Ascending", totals=True),
    ]
    return page("ledger", "C · Ledger", vis)


# ================================================================ Schedule D - take-up
def page_takeup() -> str:
    h = PAGE_H - TOP - M
    left_w = (PAGE_W - 2 * M - GAP) * 0.55
    right_w = PAGE_W - 2 * M - GAP - left_w
    rx = M + left_w + GAP
    gauge_h = 280

    vis = header(
        "p3", "D", "Assumption was a ceiling, not a cheque: 85% of the $21.5M was taken up.",
        "Creditors had to bring state paper to a federal loan office and exchange it for federal stock. "
        "Utilization shows whether each quota matched real outstanding debt. Sources: Enclosure D (first window, "
        "Jan 1792); Bayley, History of the National Loans (Treasury) for final amounts.", 4,
    ) + [
        bar_chart("p3-stacked", M, TOP, left_w, h,
                  category=STATE, series=[ASSUMED, UNUSED], colors=[GOLD, PALE], stacked=True,
                  title="Quota used and unused, by state, 1790 $",
                  subtitle="Bar length = Act quota. Gold = assumed; pale = left on the table.",
                  sort_field=QUOTA["field"], labels=False, x_title="1790 $"),
        gauge("p3-gauge", rx, TOP, right_w, gauge_h,
              value=ASSUMED, target=QUOTA, maximum=QUOTA,
              title="Utilization: $18.27M assumed of $21.50M authorized ($663M of $780M in 2025 $)",
              subtitle="Needle = assumed; end of dial = authorized."),
        table("p3-table", rx, TOP + gauge_h + GAP, right_w, h - gauge_h - GAP,
              values=[STATE, QUOTA, SUBSCRIBED, ASSUMED, UNUSED, TAKEUP, ASSUMED_25],
              title="Take-up schedule by state",
              subtitle="Subscribed = first window to Sep 1791 (MA, RI, SC over-subscribed and were scaled back to "
                       "quota). Assumed = final after extension to 1793. Totals row foots to Schedule B.",
              sort_by=TAKEUP["field"], sort_dir="Descending", totals=True),
    ]
    return page("takeup", "D · Take-up", vis)


# ================================================================ Schedule E - settlement T-account
def page_settlement() -> str:
    h = PAGE_H - TOP - M
    map_w = (PAGE_W - 2 * M - 2 * GAP) * 0.34
    t_w = (PAGE_W - 2 * M - 2 * GAP - map_w) / 2
    lx = M + map_w + GAP
    rx = lx + t_w + GAP
    t_h = (h - GAP) * 0.62
    bar_h = h - GAP - t_h

    creditors = [f for f in ["New Hampshire", "Massachusetts", "Rhode Island", "Connecticut",
                             "New Jersey", "South Carolina", "Georgia"]]
    debtors = ["New York", "Pennsylvania", "Delaware", "Maryland", "Virginia", "North Carolina"]
    DEBIT = proj_sum("states", "settlement_usd", "Dr - due to state")
    CREDIT = proj_sum("states", "settlement_usd", "Cr - due from state")

    vis = header(
        "p4", "E", "The true-up: the 1793 settlement of war accounts, posted as a T-account. Both sides foot to $3,517,584.",
        "This is the audit Madison demanded before assumption. Each state's war expenditure was netted against "
        "its share of the common cost. Debit side = the Union owed the state (creditor). Credit side = the state "
        "owed the Union (debtor). Virginia is on the credit side. Source: Commissioners to Washington, 29 Jun 1793.", 5,
    ) + [
        treemap("p4-treemap", M, TOP, map_w, h,
                group=POSITION, details=STATE, value=proj_sum("states", "settlement_abs_usd", "Balance (absolute)"),
                title="The two sides of the account, to scale",
                subtitle="Tile area = absolute balance. The teal block and the red block are the same size: "
                         "$3,517,584 each. Massachusetts and South Carolina are two-thirds of the debit side; "
                         "New York is 59% of the credit side.",
                colors=POSITION_COLORS),
        table("p4-dr", lx, TOP, t_w, t_h,
              values=[STATE, DEBIT, SETTLEMENT_25, SETTLEMENT_PC],
              title="Dr  ·  Creditor states: balances due TO the state",
              subtitle="Seven states over-contributed to the common cost.",
              filters=[state_filter(creditors)], sort_by=DEBIT["field"], sort_dir="Descending", totals=True),
        table("p4-cr", rx, TOP, t_w, t_h,
              values=[STATE, CREDIT, SETTLEMENT_25, SETTLEMENT_PC],
              title="Cr  ·  Debtor states: balances due FROM the state",
              subtitle="Six states under-contributed. Negatives in parentheses.",
              filters=[state_filter(debtors)], sort_by=CREDIT["field"], sort_dir="Ascending", totals=True),
        bar_chart("p4-bars", lx, TOP + t_h + GAP, t_w * 2 + GAP, bar_h,
                  category=STATE, series=[SETTLEMENT_PC], legend_field=POSITION, legend_pairs=POSITION_COLORS,
                  title="Settlement balance per head, 1790 $",
                  subtitle="New York ($6.10) per head, about ($221) today. South Carolina $4.84, about $176. Virginia ($0.12).",
                  labels=True, precision=2, x_title="1790 $ per head"),
    ]
    return page("settlement", "E · 1793 T-account", vis)


# ================================================================ Schedule F - fairness
def page_fairness() -> str:
    h = PAGE_H - TOP - M
    half_w = (PAGE_W - 2 * M - GAP) / 2
    rx = M + half_w + GAP
    top_h = (h - GAP) * 0.55
    bot_h = h - GAP - top_h

    vis = header(
        "p5", "F", "Relief tracked contribution: creditor states received 2.3x the relief per head of debtor states.",
        "Hamilton's defence was that the state debts were incurred for a common cause, so relieving them was rough "
        "justice. If so, states the 1793 audit found had over-paid should have received more relief. They did: "
        "$6.12 vs $2.67 per head (exact permutation p = 0.047; Spearman rho = 0.55).", 6,
    ) + [
        scatter("p5-scatter", M, TOP, half_w, top_h,
                category=STATE, xf=ASSUMED_PC, yf=SETTLEMENT_PC,
                legend_field=POSITION, legend_pairs=POSITION_COLORS,
                title="Relief received vs. 1793 settlement, per head, 1790 $",
                subtitle="One point per state. Dotted line = linear trend.",
                x_title="Relief per head, 1790 $", y_title="Settlement per head, 1790 $"),
        bar_chart("p5-net", rx, TOP, half_w, top_h,
                  category=STATE, series=[NET_PC], legend_field=POSITION, legend_pairs=POSITION_COLORS,
                  title="Net position per head: relief plus settlement, 1790 $",
                  subtitle="Eleven of thirteen came out ahead. South Carolina $20.90 ($759 today); Delaware ($9.36); New York ($2.62).",
                  labels=True, precision=2, x_title="1790 $ per head"),
        table("p5-table", M, TOP + top_h + GAP, PAGE_W - 2 * M, bot_h,
              values=[STATE, REGION, POSITION, ASSUMED, SETTLEMENT, NET, NET_25, NET_PC, NET_PC_25, POP_SHARE],
              title="Net federal position schedule, 1790 $ and 2025 $",
              subtitle="Relief = finally assumed. Net = relief + settlement. Totals row: relief $18,271,786; settlement nil; net $18,271,786.",
              sort_by=NET_PC["field"], sort_dir="Descending", totals=True),
    ]
    return page("fairness", "F · Fairness test", vis)


# ================================================================ Schedule G - apportionment
def page_apportionment() -> str:
    h = PAGE_H - TOP - M
    left_w = (PAGE_W - 2 * M - GAP) * 0.6
    right_w = PAGE_W - 2 * M - GAP - left_w
    rx = M + left_w + GAP
    slicer_h = 140

    GAP_USD = proj_sum("counterfactual", "gap_usd", "Quota less per-head share")
    CF_STATE = proj_col("counterfactual", "state", active=True, display="State")
    CF_REGION = proj_col("counterfactual", "region", display="Region")
    vis = header(
        "p6", "G", "Not proportional to population: one dollar in five sits in a different state than a per-head split would put it.",
        "What each state would have received had $21.5M been split like congressional apportionment, versus the Act. "
        "Choose the population basis at right; the answer barely moves. The 'North vs South' story fails "
        "(permutation p = 0.78): South Carolina alone drives the Southern mean.", 7,
    ) + [
        bar_chart("p6-diverging", M, TOP, left_w, h,
                  category=CF_STATE, series=[GAP_USD],
                  legend_field=CF_REGION, legend_pairs=REGION_COLORS,
                  title="Quota less population-proportional share, 1790 $",
                  subtitle="Right of zero = more than its head-count share. Negatives in parentheses.",
                  labels=True, precision=0, x_title="1790 $"),
        slicer("p6-basis", rx, TOP, right_w, slicer_h,
               field=proj_col("counterfactual", "basis"), title="Population basis", single=True),
        table("p6-table", rx, TOP + slicer_h + GAP, right_w, h - slicer_h - GAP,
              values=[proj_col("counterfactual", "state", display="State"),
                      proj_sum("counterfactual", "quota_usd", "Act quota"),
                      proj_sum("counterfactual", "proportional_usd", "Per-head share"),
                      GAP_USD,
                      proj_sum("counterfactual", "gap_usd_2025", "Gap (2025 $)")],
              title="Apportionment schedule",
              subtitle="Gaps net to zero by construction. Dissimilarity: total population 20.2%, free population 19.1%, three-fifths basis 19.8%.",
              sort_by=GAP_USD["field"], sort_dir="Descending", totals=True),
    ]
    return page("apportionment", "G · Apportionment", vis)


# ================================================================ Schedule H - statistics & sources
def page_stats_about() -> str:
    h = PAGE_H - TOP - M
    col_w = (PAGE_W - 2 * M - 2 * GAP) / 3
    table_w = col_w * 2 + GAP
    H, B = 12, 10

    method = [
        ("Notes", H, True, NAVY, HFONT),
        ("Foot first. Every table tied to its printed total before analysis (Schedule B).", B, False, INK),
        ("Population, not sample. 13 states is the whole universe. With 4-7 per group, tests have "
         "little power. Effect sizes lead; p-values follow.", B, False, INK),
        ("Three tests, one answer. Welch t, Mann-Whitney U, exact permutation. All agree.", B, False, INK),
        ("Dissimilarity index. Share of the total that would have to move to match the benchmark. "
         "Same idea as budget variance.", B, False, INK),
        ("Two dollar figures. 1790 $ and 2025 $ at 36.3x CPI (MeasuringWorth). GDP share for scale.", B, False, INK),
        ("Boundaries. Maine in MA, Kentucky in VA, as in 1790. No ranking changes without them.", B, False, INK),
        ("Sources", H, True, NAVY, HFONT),
        ("Schedule E, Report Relative to a Provision for the Support of Public Credit, 9 Jan 1790 (Founders Online).", B, False, INK),
        ("An Act making provision for the Debt of the United States, 4 Aug 1790, 1 Stat. 138, sec. 14.", B, False, INK),
        ("Enclosure D, Statement of Subscriptions to the Loan, Treasury Department, 25 Jan 1792 (Founders Online).", B, False, INK),
        ("Bayley, History of the National Loans of the United States (U.S. Treasury, 1881), p. 33.", B, False, INK),
        ("Commissioners for Settling Accounts to George Washington, 29 Jun 1793 (Founders Online).", B, False, INK),
        ("Return of the Whole Number of Persons (First Census, 1790), U.S. Census Bureau.", B, False, INK),
        ("How it was built", H, True, NAVY, HFONT),
        ("Python (pandas, scipy) reads the five source tables, foots them, joins them to the census, runs the tests "
         "and writes a ledger CSV. This report is a Power BI project (.pbip): the semantic model and every page and "
         "visual are generated by src/build_model.py and src/build_pbir.py, so the dashboard is version-controlled "
         "like code.", B, False, INK),
        ("github.com/josephrbarry/hamilton-debt-assumption", B, True, NAVY),
    ]
    vis = header(
        "p7", "H", "Statistics, method and sources",
        "Every test in the write-up with its statistic, p-value and a plain-English reading. "
        "Prepared by Ryan Barry as an accounting portfolio project.", 8,
    ) + [
        table("p7-stats", M, TOP, table_w, h,
              values=[proj_col("stats", "question", display="Question"),
                      proj_col("stats", "test", display="Test"),
                      proj_col("stats", "statistic", display="Statistic"),
                      proj_avg("stats", "p_value", "p-value"),
                      proj_col("stats", "read", display="Reading")],
              title="Test schedule",
              subtitle="A: regional tilt in quotas? B: did relief track 1793 contribution? C: proportional to population?",
              sort_by=proj_col("stats", "test")["field"], sort_dir="Ascending", totals=False),
        textbox("p7-method", M + table_w + GAP, TOP, col_w, h, method, bg=WHITE, spaced=True),
    ]
    return page("stats", "H · Statistics & sources", vis)


def clear_desktop_cache() -> None:
    """Delete Power BI Desktop's per-user data cache so it rebuilds from the files on
    disk. Power BI Desktop must be closed."""
    for cache in (ROOT / "powerbi").glob("*.SemanticModel/.pbi/cache.abf"):
        cache.unlink()
        print(f"cleared {cache.relative_to(ROOT)}")


def main() -> None:
    clear_desktop_cache()
    if PAGES.exists():
        shutil.rmtree(PAGES)           # pages are fully generated; start clean
    order = [page_summary(), page_tieout(), page_ledger(), page_takeup(), page_settlement(),
             page_fairness(), page_apportionment(), page_stats_about()]
    assert len(order) == TOTAL_PAGES
    (PAGES / "pages.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
        "pageOrder": order, "activePageName": order[0],
    }, indent=2), encoding="utf-8")
    n = sum(1 for _ in PAGES.rglob("visual.json"))
    print(f"Wrote {len(order)} pages, {n} visuals to {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
