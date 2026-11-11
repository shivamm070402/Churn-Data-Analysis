"""
Generate a professional database design diagram (PNG) matching dbdiagram.io style.
Run: python generate_db_diagram.py  (from project root with venv active)
"""
import plotly.graph_objects as go
from pathlib import Path

OUT = Path("screenshots")
OUT.mkdir(exist_ok=True)

# ── colour palette ────────────────────────────────────────────
BG       = "#0F172A"
CARD     = "#1E293B"
HEADER_1 = "#1D4ED8"   # db_customer   - blue
HEADER_2 = "#059669"   # db_subscription - green
HEADER_3 = "#7C3AED"   # db_support    - purple
HEADER_4 = "#D97706"   # derived       - amber
BORDER   = "#334155"
TEXT     = "#F1F5F9"
MUTED    = "#94A3B8"
PK_COL   = "#FCD34D"   # gold for PK
FK_COL   = "#6EE7B7"   # teal for FK
TYPE_COL = "#93C5FD"   # blue for types
DROP_COL = "#F87171"   # red for dropped cols
ENG_COL  = "#C4B5FD"   # purple for engineered

fig = go.Figure()
fig.update_layout(
    width=1400, height=920,
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    margin=dict(l=0, r=0, t=0, b=0),
    xaxis=dict(visible=False, range=[0, 14]),
    yaxis=dict(visible=False, range=[0, 9.2]),
    showlegend=False,
)

# ── helper: draw a table card ────────────────────────────────
def table_card(x0, y0, w, header_color, title, subtitle, rows, note=None):
    """
    rows = list of (icon, name, type_str, note_str)
    icon: "PK"=primary key, "FK"=foreign key, "✕"=dropped, "★"=engineered, ""=normal
    """
    row_h    = 0.30
    head_h   = 0.52
    pad      = 0.08
    total_h  = head_h + len(rows) * row_h + pad
    if note:
        total_h += 0.32

    # outer card shadow
    fig.add_shape(type="rect",
        x0=x0+0.04, y0=y0-total_h-0.04, x1=x0+w+0.04, y1=y0+0.04,
        fillcolor="rgba(0,0,0,0.4)", line_width=0, layer="below")

    # card background
    fig.add_shape(type="rect",
        x0=x0, y0=y0-total_h, x1=x0+w, y1=y0,
        fillcolor=CARD, line=dict(color=BORDER, width=1.5), layer="below")

    # header band
    fig.add_shape(type="rect",
        x0=x0, y0=y0-head_h, x1=x0+w, y1=y0,
        fillcolor=header_color, line_width=0, layer="below")

    # title
    fig.add_annotation(x=x0+0.14, y=y0-0.17,
        text=f"<b>{title}</b>",
        showarrow=False, xanchor="left", yanchor="middle",
        font=dict(size=14, color="#FFFFFF", family="Arial Black"))

    # subtitle
    fig.add_annotation(x=x0+0.14, y=y0-0.38,
        text=subtitle,
        showarrow=False, xanchor="left", yanchor="middle",
        font=dict(size=10, color="rgba(255,255,255,0.75)", family="Arial"))

    # divider
    fig.add_shape(type="line",
        x0=x0, y0=y0-head_h, x1=x0+w, y1=y0-head_h,
        line=dict(color=BORDER, width=1))

    # rows
    for i, (icon, col_name, col_type, col_note) in enumerate(rows):
        ry = y0 - head_h - (i + 0.5) * row_h

        # alternating row bg
        if i % 2 == 0:
            fig.add_shape(type="rect",
                x0=x0+0.01, y0=ry - row_h*0.5,
                x1=x0+w-0.01, y1=ry + row_h*0.5,
                fillcolor="rgba(255,255,255,0.03)", line_width=0)

        # icon badge
        if icon == "PK":
            badge_clr, badge_txt = PK_COL, "PK"
        elif icon == "FK":
            badge_clr, badge_txt = FK_COL, "FK"
        elif icon == "✕":
            badge_clr, badge_txt = DROP_COL, "✕"
        elif icon == "★":
            badge_clr, badge_txt = ENG_COL, "★"
        else:
            badge_clr, badge_txt = MUTED, "·"

        fig.add_annotation(x=x0+0.22, y=ry,
            text=f"<b>{badge_txt}</b>",
            showarrow=False, xanchor="center", yanchor="middle",
            font=dict(size=9, color=badge_clr, family="Courier New"))

        # column name
        name_clr = DROP_COL if icon == "✕" else (PK_COL if icon == "PK" else TEXT)
        fig.add_annotation(x=x0+0.36, y=ry,
            text=col_name,
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=12, color=name_clr, family="Courier New"))

        # type
        fig.add_annotation(x=x0+w-0.12, y=ry,
            text=col_type,
            showarrow=False, xanchor="right", yanchor="middle",
            font=dict(size=10, color=TYPE_COL, family="Courier New"))

        # row separator
        if i < len(rows) - 1:
            fig.add_shape(type="line",
                x0=x0+0.1, y0=ry - row_h*0.5,
                x1=x0+w-0.1, y1=ry - row_h*0.5,
                line=dict(color=BORDER, width=0.5, dash="dot"))

    # note box at bottom
    if note:
        ny = y0 - head_h - len(rows) * row_h - 0.04
        fig.add_shape(type="rect",
            x0=x0+0.1, y0=ny-0.26, x1=x0+w-0.1, y1=ny,
            fillcolor="rgba(255,255,255,0.04)",
            line=dict(color=BORDER, width=0.8, dash="dot"))
        fig.add_annotation(x=x0+0.2, y=ny-0.13,
            text=note,
            showarrow=False, xanchor="left", yanchor="middle",
            font=dict(size=9.5, color=MUTED, family="Arial"))

    return x0, y0, x0+w, y0-total_h  # returns bbox


# ── helper: draw relationship arrow ──────────────────────────
def rel_arrow(x1, y1, x2, y2, label=""):
    fig.add_shape(type="line", x0=x1, y0=y1, x1=x2, y1=y2,
        line=dict(color="#60A5FA", width=1.5, dash="dot"))
    # diamond at FK end
    fig.add_annotation(x=x1, y=y1,
        text="◇", showarrow=False,
        font=dict(size=12, color="#60A5FA"))
    # crow's foot at PK end
    fig.add_annotation(x=x2, y=y2,
        text="▶", showarrow=False,
        font=dict(size=10, color="#60A5FA"))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        fig.add_annotation(x=mx, y=my+0.14, text=label,
            showarrow=False,
            font=dict(size=9, color="#60A5FA"),
            bgcolor="rgba(15,23,42,0.85)",
            bordercolor="#1E293B", borderwidth=1, borderpad=3)


# ══════════════════════════════════════════════════════════════
# DRAW THE THREE TABLES
# ══════════════════════════════════════════════════════════════

# ── db_customer  (top-left) ───────────────────────────────────
table_card(
    x0=0.3, y0=8.9, w=3.9,
    header_color=HEADER_1,
    title="db_customer",
    subtitle="21 rows  •  Customer Demographics",
    rows=[
        ("PK", "customerid",   "TEXT",      ""),
        ("",   "name",         "TEXT",      "→ customer_name"),
        ("",   "country",      "TEXT",      "3 nulls → filled"),
        ("",   "state",        "TEXT",      ""),
        ("",   "gender",       "TEXT",      "Men/Women → Male/Female"),
        ("",   "dob",          "TIMESTAMP", "→ customer_age"),
        ("✕",  "interests",    "TEXT",      "DROPPED (sparse)"),
        ("✕",  "pincode",      "REAL",      "DROPPED (all null)"),
    ],
    note="🔑  Primary key table — joined by both other tables"
)

# ── db_subscription  (top-right) ─────────────────────────────
table_card(
    x0=5.0, y0=8.9, w=4.5,
    header_color=HEADER_2,
    title="db_subscription",
    subtitle="21 rows  •  One row per customer",
    rows=[
        ("FK", "customerid",            "TEXT",    "FK → db_customer"),
        ("",   "subscription_start_date","TEXT",   "→ datetime"),
        ("",   "subscription_type",     "TEXT",    "Organic|Paid|Refferal"),
        ("",   "renewal_date",          "TEXT",    "→ datetime"),
        ("",   "plan_type",             "TEXT",    "Basic|Standard|Premium"),
        ("",   "contract_type",         "TEXT",    "Monthly|Annual"),
        ("",   "cancellation_date",     "TEXT",    "NULL=active → datetime"),
        ("",   "cancellation_reason",   "TEXT",    "Free-text"),
        ("",   "monthly_charges",       "REAL",    "₹6.99 – ₹22.99"),
        ("",   "cltv",                  "INTEGER", "195 – 1725"),
        ("",   "churn_score",           "INTEGER", "0 – 100  → churn_risk"),
    ],
    note="📊  Core analytics table — churn_flag & tenure derived here"
)

# ── db_support  (bottom-right) ───────────────────────────────
table_card(
    x0=5.0, y0=3.9, w=4.5,
    header_color=HEADER_3,
    title="db_support",
    subtitle="9 rows  •  Multiple rows per customer",
    rows=[
        ("FK", "customerid",    "TEXT",      "FK → db_customer (non-unique)"),
        ("",   "complaint_date","TIMESTAMP", "→ datetime"),
        ("",   "escalations",   "TEXT",      "Y|N  → escalation_flag 1/0"),
        ("",   "csat_score",    "INTEGER",   "0–100  (lower=worse)"),
        ("✕",  "col_1",         "REAL",      "DROPPED (all null)"),
        ("✕",  "comment",       "TEXT",      "DROPPED (mostly null)"),
    ],
    note="⚠️  Deduped to 1 row/customer (keep latest complaint)"
)

# ── Derived Features  (bottom-left) ──────────────────────────
table_card(
    x0=0.3, y0=5.5, w=3.9,
    header_color=HEADER_4,
    title="derived_features",
    subtitle="Engineered in Pandas pipeline  •  Not in SQLite",
    rows=[
        ("★", "churn_flag",      "INTEGER", "1=Churned 0=Active"),
        ("★", "tenure_days",     "INTEGER", "cancel/today − start"),
        ("★", "customer_age",    "INTEGER", "today − dob (years)"),
        ("★", "escalation_flag", "INTEGER", "1=Y  0=N"),
        ("★", "complaint_count", "INTEGER", "groupby count (pre-dedup)"),
        ("★", "churn_risk",      "TEXT",    "low|med|high from score"),
    ],
    note="🔧  Added to master DataFrame after merge"
)

# ══════════════════════════════════════════════════════════════
# RELATIONSHIP ARROWS
# ══════════════════════════════════════════════════════════════
# db_subscription.customerid → db_customer.customerid
rel_arrow(5.0, 8.4, 4.2, 8.4, "many-to-one")

# db_support.customerid → db_customer.customerid
fig.add_shape(type="line", x0=5.0, y0=3.65, x1=4.5, y1=3.65,
    line=dict(color="#60A5FA", width=1.5, dash="dot"))
fig.add_shape(type="line", x0=4.5, y0=3.65, x1=4.5, y1=8.4,
    line=dict(color="#60A5FA", width=1.5, dash="dot"))
fig.add_shape(type="line", x0=4.5, y0=8.4, x1=4.2, y1=8.4,
    line=dict(color="#60A5FA", width=1.5, dash="dot"))
fig.add_annotation(x=4.85, y=3.65, text="◇", showarrow=False,
    font=dict(size=12, color="#60A5FA"))
fig.add_annotation(x=4.22, y=8.4, text="▶", showarrow=False,
    font=dict(size=10, color="#60A5FA"))
fig.add_annotation(x=4.5, y=6.0, text="many-to-one",
    showarrow=False, font=dict(size=9, color="#60A5FA"),
    bgcolor="rgba(15,23,42,0.85)",
    bordercolor="#1E293B", borderwidth=1, borderpad=3,
    textangle=-90)

# ══════════════════════════════════════════════════════════════
# MERGE FLOW ANNOTATION
# ══════════════════════════════════════════════════════════════
fig.add_shape(type="rect",
    x0=9.9, y0=8.1, x1=13.6, y1=5.3,
    fillcolor="#0F172A", line=dict(color="#334155", width=1.5))

fig.add_annotation(x=10.1, y=8.0,
    text="<b>🔀  Merge Strategy  (Pandas)</b>",
    showarrow=False, xanchor="left",
    font=dict(size=13, color=TEXT, family="Arial Black"))

merge_code = (
    "df = db_subscription<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;.merge(db_customer,<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    "on='customerid',<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    "how='LEFT')<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;.merge(db_support,<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    "on='customerid',<br>"
    "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    "how='LEFT')<br><br>"
    "Result: 21 rows × 24 columns"
)
fig.add_annotation(x=10.1, y=7.6,
    text=f"<span style='font-family:Courier New;font-size:11px;"
         f"color:{TYPE_COL}'>{merge_code}</span>",
    showarrow=False, xanchor="left", yanchor="top",
    font=dict(size=11, color=TYPE_COL, family="Courier New"),
    align="left")

# ══════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════
fig.add_shape(type="rect",
    x0=9.9, y0=4.9, x1=13.6, y1=3.3,
    fillcolor="#0F172A", line=dict(color="#334155", width=1.5))

fig.add_annotation(x=10.1, y=4.8,
    text="<b>Legend</b>",
    showarrow=False, xanchor="left",
    font=dict(size=13, color=TEXT, family="Arial Black"))

legend_items = [
    (PK_COL,  "PK",  "Primary Key"),
    (FK_COL,  "FK",  "Foreign Key"),
    (DROP_COL,"✕",   "Dropped column (cleaning)"),
    (ENG_COL, "★",   "Engineered feature (pipeline)"),
]
for i, (clr, icon, label) in enumerate(legend_items):
    y = 4.5 - i * 0.33
    fig.add_annotation(x=10.3, y=y, text=f"<b>{icon}</b>",
        showarrow=False, xanchor="center",
        font=dict(size=12, color=clr, family="Courier New"))
    fig.add_annotation(x=10.6, y=y, text=label,
        showarrow=False, xanchor="left",
        font=dict(size=11, color=MUTED))

# ── title banner ──────────────────────────────────────────────
fig.add_shape(type="rect",
    x0=0, y0=9.05, x1=14, y1=9.2,
    fillcolor="#1E3A5F", line_width=0)
fig.add_annotation(x=7, y=9.125,
    text="<b>Customer Churn Analysis  —  Database Design  |  dbdiagram.io</b>",
    showarrow=False, xanchor="center",
    font=dict(size=14, color="#E2EAF4", family="Arial"))

fig.write_image(str(OUT / "07_database_design.png"), scale=2)
print("✅  07_database_design.png")
