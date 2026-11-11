"""
Generate dashboard screenshots for GitHub README.
Run from project root with the venv python.
"""
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

OUT = Path("screenshots")
OUT.mkdir(exist_ok=True)

DB = Path("customer_churn.db")

# ── colours ────────────────────────────────────────────────────
RED    = "#FF4B4B"
GREEN  = "#00C9A7"
BLUE   = "#4C8BF5"
AMBER  = "#FFA94D"
PURPLE = "#A78BFA"
BG     = "#0E1525"
CARD   = "#162032"
BORDER = "#1E2D45"
TEXT   = "#E2EAF4"
MUTED  = "#64748B"

# ── load data ─────────────────────────────────────────────────
conn = sqlite3.connect(DB)
cust = pd.read_sql("SELECT * FROM db_customer",     conn)
sub  = pd.read_sql("SELECT * FROM db_subscription", conn)
sup  = pd.read_sql("SELECT * FROM db_support",      conn)
conn.close()

cust = cust.rename(columns={"name": "customer_name"})
cust = cust.drop(columns=["interests", "pincode"], errors="ignore")
cust["dob"]    = pd.to_datetime(cust["dob"])
cust["gender"] = cust["gender"].replace({"Men": "Male", "Women": "Female"})
sc   = cust.dropna(subset=["country"]).set_index("state")["country"].to_dict()
cust["country"] = cust["country"].fillna(cust["state"].map(sc))

for c in ["subscription_start_date", "renewal_date", "cancellation_date"]:
    sub[c] = pd.to_datetime(sub[c])
sub["churn_flag"] = np.where(sub["cancellation_date"].notna(), 1, 0)

sup = sup.drop(columns=["col_1", "comment"], errors="ignore")
sup["complaint_date"]  = pd.to_datetime(sup["complaint_date"])
sup["complaint_count"] = sup.groupby("customerid")["customerid"].transform("count")
sup = sup.sort_values("complaint_date").drop_duplicates("customerid", keep="last")

df = sub.merge(cust, on="customerid", how="left").merge(sup, on="customerid", how="left")

today = pd.Timestamp.today().normalize()
end = df["cancellation_date"].fillna(today)
df["tenure_days"]     = (end - df["subscription_start_date"]).dt.days
df["customer_age"]    = (today.year - df["dob"].dt.year
                         - ((today.month < df["dob"].dt.month)
                          | ((today.month == df["dob"].dt.month)
                           & (today.day < df["dob"].dt.day))).astype(int))
df["escalation_flag"] = np.where(df["escalations"] == "Y", 1, 0)
df["churn_risk"]      = np.select(
    [df["churn_score"] < 50,
     (df["churn_score"] >= 50) & (df["churn_score"] < 70),
     df["churn_score"] >= 70],
    ["low", "med", "high"], default="unkown")


def base(fig, h=420):
    fig.update_layout(
        height=h, width=900,
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="Arial", color=TEXT, size=13),
        margin=dict(l=50, r=30, t=60, b=50),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
        title_font=dict(size=17, color=TEXT),
    )
    fig.update_xaxes(gridcolor=BORDER, zeroline=False, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, tickfont=dict(color=MUTED))
    return fig


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 1 — KPI Overview (multi-panel)
# ══════════════════════════════════════════════════════════════
churn_rate     = df["churn_flag"].mean() * 100
retention_rate = 100 - churn_rate
arpu           = df["monthly_charges"].mean()
rev_at_risk    = df.loc[df["churn_flag"] == 1, "monthly_charges"].sum()
avg_tenure     = df["tenure_days"].mean()
corr_val       = df[["escalation_flag","churn_flag"]].dropna()["escalation_flag"].corr(
                     df.loc[df[["escalation_flag","churn_flag"]].dropna().index,"churn_flag"])

fig1 = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "domain"}, {"type": "xy"}]],
    subplot_titles=["Churned vs Retained", "Churn Rate by Plan Type"],
)

# donut
churned  = int(df["churn_flag"].sum())
retained = len(df) - churned
fig1.add_trace(go.Pie(
    labels=["Churned", "Retained"], values=[churned, retained],
    hole=0.65, marker_colors=[RED, GREEN], sort=False,
    textinfo="label+percent", textfont=dict(color="#fff", size=13),
    hoverinfo="skip",
), row=1, col=1)

# plan bar
pt = (df.groupby("plan_type")["churn_flag"]
        .mean().mul(100).round(1).reset_index())
pt.columns = ["plan_type", "churn_rate_pct"]
clrs = [RED if v >= 50 else AMBER if v > 20 else GREEN for v in pt["churn_rate_pct"]]
fig1.add_trace(go.Bar(
    x=pt["plan_type"], y=pt["churn_rate_pct"],
    marker=dict(color=clrs, cornerradius=6),
    text=[f"{v}%" for v in pt["churn_rate_pct"]],
    textposition="outside", textfont=dict(color=TEXT, size=13),
), row=1, col=2)

fig1.update_layout(
    height=440, width=1100,
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Arial", color=TEXT, size=13),
    showlegend=False,
    margin=dict(l=40, r=40, t=70, b=50),
    title=dict(
        text="📉  Customer Churn Dashboard  —  Overview",
        font=dict(size=20, color=TEXT), x=0.01,
    ),
    annotations=[
        dict(text=f"<b>{churn_rate:.1f}%</b><br>churn",
             x=0.21, y=0.5, showarrow=False,
             font=dict(size=18, color=TEXT)),
    ] + [dict(text=t, font=dict(color=TEXT, size=13),
              showarrow=False, x=x, y=1.08, xref="paper", yref="paper")
         for t, x in zip(["Churned vs Retained", "Churn Rate by Plan Type"], [0.21, 0.72])],
)
fig1.update_yaxes(range=[0, 85], gridcolor=BORDER, row=1, col=2)
fig1.update_xaxes(gridcolor=BORDER, row=1, col=2)
for ann in fig1.layout.annotations:
    ann.font.color = TEXT

fig1.write_image(str(OUT / "01_overview.png"), scale=2)
print("✅  01_overview.png")


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 2 — Segments
# ══════════════════════════════════════════════════════════════
fig2 = make_subplots(
    rows=1, cols=2,
    subplot_titles=["Churn Rate by State", "Churn Rate by Subscription Source"],
)
for col_name, col_idx in [("state", 1), ("subscription_type", 2)]:
    tbl = (df.groupby(col_name)["churn_flag"]
             .mean().mul(100).round(1).reset_index()
             .sort_values("churn_flag", ascending=False))
    tbl.columns = [col_name, "churn_rate"]
    clrs2 = [RED if v >= 50 else AMBER if v > 20 else GREEN for v in tbl["churn_rate"]]
    fig2.add_trace(go.Bar(
        x=tbl[col_name], y=tbl["churn_rate"],
        marker=dict(color=clrs2, cornerradius=5),
        text=[f"{v}%" for v in tbl["churn_rate"]],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ), row=1, col=col_idx)

fig2.update_layout(
    height=440, width=1100,
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Arial", color=TEXT, size=13),
    showlegend=False,
    margin=dict(l=40, r=40, t=70, b=60),
    title=dict(text="📊  Segment Analysis", font=dict(size=20, color=TEXT), x=0.01),
)
fig2.update_yaxes(range=[0, 125], gridcolor=BORDER)
fig2.update_xaxes(gridcolor=BORDER, tickangle=-20)
for ann in fig2.layout.annotations:
    ann.font.color = TEXT

fig2.write_image(str(OUT / "02_segments.png"), scale=2)
print("✅  02_segments.png")


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 3 — Churn Risk
# ══════════════════════════════════════════════════════════════
fig3 = make_subplots(
    rows=1, cols=2,
    subplot_titles=["Customers by Churn Risk Level", "CLTV vs Churn Score"],
    specs=[[{"type": "xy"}, {"type": "xy"}]],
)

risk_clr = {"low": GREEN, "med": AMBER, "high": RED, "unkown": MUTED}
rc = (df["churn_risk"].value_counts()
        .reindex(["low", "med", "high"], fill_value=0).reset_index())
rc.columns = ["churn_risk", "customers"]
fig3.add_trace(go.Bar(
    x=rc["churn_risk"], y=rc["customers"],
    marker=dict(color=[risk_clr[r] for r in rc["churn_risk"]], cornerradius=6),
    text=rc["customers"], textposition="outside", textfont=dict(color=TEXT),
), row=1, col=1)

colors_bubble = [RED if f == 1 else GREEN for f in df["churn_flag"]]
fig3.add_trace(go.Scatter(
    x=df["cltv"], y=df["churn_score"],
    mode="markers",
    marker=dict(size=df["monthly_charges"] * 2.5, color=colors_bubble,
                opacity=0.8, line=dict(width=1, color="#fff")),
    text=df["customer_name"],
    hovertemplate="<b>%{text}</b><br>CLTV: %{x}<br>Score: %{y}<extra></extra>",
), row=1, col=2)

fig3.update_layout(
    height=440, width=1100,
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Arial", color=TEXT, size=13),
    showlegend=False,
    margin=dict(l=40, r=40, t=70, b=50),
    title=dict(text="⚠️  Churn Risk Analysis", font=dict(size=20, color=TEXT), x=0.01),
)
fig3.update_yaxes(gridcolor=BORDER)
fig3.update_xaxes(gridcolor=BORDER)
for ann in fig3.layout.annotations:
    ann.font.color = TEXT

fig3.write_image(str(OUT / "03_risk.png"), scale=2)
print("✅  03_risk.png")


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 4 — Support & Escalation
# ══════════════════════════════════════════════════════════════
fig4 = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "domain"}, {"type": "xy"}]],
    subplot_titles=["Escalation Split", f"Churn Rate: Escalated vs Not (corr={corr_val:.2f})"],
)

ec = (df["escalation_flag"].map({0: "No Escalation", 1: "Escalated"})
        .value_counts().reset_index())
ec.columns = ["status", "count"]
fig4.add_trace(go.Pie(
    labels=ec["status"], values=ec["count"],
    hole=0.58,
    marker_colors=[BLUE, RED],
    textinfo="label+percent", textfont=dict(color="#fff", size=13),
), row=1, col=1)

esc_c = (df.groupby("escalation_flag")
           .agg(churn_rate=("churn_flag", lambda x: round(x.mean() * 100, 1)))
           .reset_index()
           .assign(group=lambda d: d["escalation_flag"].map({0: "No Escalation", 1: "Escalated"})))
fig4.add_trace(go.Bar(
    x=esc_c["group"], y=esc_c["churn_rate"],
    marker=dict(color=[BLUE, RED], cornerradius=6),
    text=[f"{v}%" for v in esc_c["churn_rate"]],
    textposition="outside", textfont=dict(color=TEXT, size=14),
), row=1, col=2)

fig4.update_layout(
    height=440, width=1100,
    paper_bgcolor=BG, plot_bgcolor=BG,
    font=dict(family="Arial", color=TEXT, size=13),
    showlegend=False,
    margin=dict(l=40, r=40, t=70, b=50),
    title=dict(text="🎧  Support & Escalation Analysis", font=dict(size=20, color=TEXT), x=0.01),
)
fig4.update_yaxes(range=[0, 120], gridcolor=BORDER, row=1, col=2)
fig4.update_xaxes(gridcolor=BORDER, row=1, col=2)
for ann in fig4.layout.annotations:
    ann.font.color = TEXT

fig4.write_image(str(OUT / "04_support.png"), scale=2)
print("✅  04_support.png")


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 5 — Architecture / System Design (text-based visual)
# ══════════════════════════════════════════════════════════════
arch_text = (
    "SQLite DB (customer_churn.db)\n"
    "  ├── db_customer   (21 rows)  →  Demographics\n"
    "  ├── db_subscription (21 rows) →  Plan, charges, churn score\n"
    "  └── db_support     (9 rows)  →  Complaints, escalations, CSAT\n\n"
    "              ▼  pandas.read_sql()  ▼\n\n"
    "Data Cleaning  →  Feature Engineering  →  Master DataFrame (21 × 24)\n"
    "  • Fix dtypes       • churn_flag              churn_flag, tenure_days,\n"
    "  • Standardise      • tenure_days             customer_age, churn_risk,\n"
    "  • Fill nulls        • customer_age            escalation_flag ...\n"
    "  • Dedup support    • churn_risk\n\n"
    "              ▼  @st.cache_data  ▼\n\n"
    "Streamlit Dashboard (app.py)\n"
    "  ├── Sidebar Filters (plan · contract · source · gender · state · age)\n"
    "  ├── 🏠  Overview   →  KPI strip, donut, plan bar, pivot table\n"
    "  ├── 📊  Segments   →  State, source, contract, gender, scatter\n"
    "  ├── ⚠️  Risk        →  Risk bars, age dist, CLTV bubble, table\n"
    "  ├── 🎧  Support    →  Escalation pie, CSAT analysis, activity table\n"
    "  └── 🗄️  Data & SQL →  Full table, CSV export, live SQL editor"
)

fig5 = go.Figure()
fig5.add_annotation(
    text=arch_text.replace("\n", "<br>"),
    x=0.5, y=0.5, xref="paper", yref="paper",
    showarrow=False,
    font=dict(family="Courier New, monospace", size=13, color=GREEN),
    align="left",
    bgcolor=CARD,
    bordercolor=BORDER,
    borderwidth=1,
    borderpad=20,
    xanchor="center", yanchor="middle",
)
fig5.update_layout(
    height=520, width=1100,
    paper_bgcolor=BG,
    margin=dict(l=20, r=20, t=70, b=20),
    title=dict(text="📐  System Architecture & Data Flow", font=dict(size=20, color=TEXT), x=0.01),
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
)
fig5.write_image(str(OUT / "05_architecture.png"), scale=2)
print("✅  05_architecture.png")


# ══════════════════════════════════════════════════════════════
# SCREENSHOT 6 — KPI Summary banner
# ══════════════════════════════════════════════════════════════
kpis = [
    ("👥 Customers", "21"),
    ("📉 Churn Rate", f"{churn_rate:.1f}%"),
    ("💚 Retention", f"{retention_rate:.1f}%"),
    ("💰 ARPU", f"₹{arpu:.2f}"),
    ("🔥 Rev at Risk", f"₹{rev_at_risk:.2f}"),
    ("📅 Avg Tenure", f"{avg_tenure:.0f}d"),
    ("🔗 Esc↔Churn", f"{corr_val:.2f}"),
]

fig6 = go.Figure()
n = len(kpis)
for i, (label, value) in enumerate(kpis):
    x = (i + 0.5) / n
    fig6.add_shape(type="rect",
        x0=i/n + 0.01, x1=(i+1)/n - 0.01,
        y0=0.05, y1=0.95,
        fillcolor=CARD, line=dict(color=BORDER, width=1),
        xref="paper", yref="paper",
    )
    fig6.add_annotation(
        x=x, y=0.72, text=f"<b>{value}</b>",
        showarrow=False, xref="paper", yref="paper",
        font=dict(size=22, color=TEXT, family="Arial Black"),
        xanchor="center",
    )
    fig6.add_annotation(
        x=x, y=0.32, text=label,
        showarrow=False, xref="paper", yref="paper",
        font=dict(size=12, color=MUTED, family="Arial"),
        xanchor="center",
    )

fig6.update_layout(
    height=160, width=1100,
    paper_bgcolor=BG,
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis=dict(visible=False), yaxis=dict(visible=False),
)
fig6.write_image(str(OUT / "06_kpi_strip.png"), scale=2)
print("✅  06_kpi_strip.png")

print("\n🎉  All screenshots saved to screenshots/")
