"""
Customer Churn Analysis Dashboard
Streamlit version of churn_analysis.ipynb
Run:  streamlit run app.py
Data: customer_churn.db  (same folder)
"""

import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Paths ──────────────────────────────────────────────────────────────────
HERE = Path(__file__).parent
DB   = HERE / "customer_churn.db"
CSV  = HERE / "exported_churn_data.csv"

# ── Colours ────────────────────────────────────────────────────────────────
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

RISK_CLR = {"low": GREEN, "med": AMBER, "high": RED, "unkown": MUTED}

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Churn Analysis Dashboard",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');

/* ── base ── */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT};
}}
.block-container {{
    padding: 2rem 2.5rem 4rem 2.5rem !important;
    max-width: 1400px !important;
}}

/* ── sidebar ── */
[data-testid="stSidebar"] {{
    background: {CARD} !important;
    border-right: 1px solid {BORDER} !important;
    padding-top: 1rem;
}}
[data-testid="stSidebar"] .stMarkdown h2 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1rem !important;
    color: {TEXT} !important;
    margin-bottom: 1rem;
}}
[data-testid="stSidebar"] label {{
    color: {MUTED} !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

/* ── metric cards ── */
[data-testid="stMetric"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 18px 20px !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 0.75rem !important;
    color: {MUTED} !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
[data-testid="stMetricValue"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    color: {TEXT} !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.75rem !important;
}}

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 5px 8px;
    gap: 4px;
    margin-bottom: 1.5rem;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: {MUTED} !important;
    border-radius: 7px !important;
    padding: 8px 20px !important;
    background: transparent !important;
    border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: {BLUE} !important;
    color: #FFFFFF !important;
}}

/* ── subheaders ── */
h2, h3 {{
    font-family: 'Space Grotesk', sans-serif !important;
    color: {TEXT} !important;
    padding-bottom: 6px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 1rem !important;
    margin-top: 1.5rem !important;
}}

/* ── dataframe ── */
.stDataFrame {{ border-radius: 10px !important; overflow: hidden !important; }}

/* ── divider ── */
hr {{ border-color: {BORDER} !important; margin: 1.5rem 0 !important; }}

/* ── hide footer ── */
footer, #MainMenu {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# DATA  (mirrors notebook sections 1-3)
# ══════════════════════════════════════════════════════════════════════════
def _load_db(path: Path) -> pd.DataFrame:
    conn = sqlite3.connect(path)
    cust = pd.read_sql("SELECT * FROM db_customer",     conn)
    sub  = pd.read_sql("SELECT * FROM db_subscription", conn)
    sup  = pd.read_sql("SELECT * FROM db_support",      conn)
    conn.close()

    # customer
    cust = cust.rename(columns={"name": "customer_name"})
    cust = cust.drop(columns=["interests", "pincode"], errors="ignore")
    cust["dob"]    = pd.to_datetime(cust["dob"])
    cust["gender"] = cust["gender"].replace({"Men": "Male", "Women": "Female"})
    sc_map = cust.dropna(subset=["country"]).set_index("state")["country"].to_dict()
    cust["country"] = cust["country"].fillna(cust["state"].map(sc_map))

    # subscription
    for c in ["subscription_start_date", "renewal_date", "cancellation_date"]:
        sub[c] = pd.to_datetime(sub[c])
    sub["churn_flag"] = np.where(sub["cancellation_date"].notna(), 1, 0)

    # support
    sup = sup.drop(columns=["col_1", "comment"], errors="ignore")
    sup["complaint_date"]  = pd.to_datetime(sup["complaint_date"])
    sup["complaint_count"] = sup.groupby("customerid")["customerid"].transform("count")
    sup = sup.sort_values("complaint_date").drop_duplicates("customerid", keep="last")

    return sub.merge(cust, on="customerid", how="left").merge(sup, on="customerid", how="left")


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    df    = df.copy()
    today = pd.Timestamp.today().normalize()

    for c in ["subscription_start_date", "cancellation_date", "dob"]:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    end = df["cancellation_date"].fillna(today)
    df["tenure_days"] = (end - df["subscription_start_date"]).dt.days

    df["customer_age"] = (
        today.year - df["dob"].dt.year
        - ((today.month < df["dob"].dt.month)
           | ((today.month == df["dob"].dt.month) & (today.day < df["dob"].dt.day))).astype(int)
    )
    df["escalation_flag"] = np.where(df["escalations"] == "Y", 1, 0)
    df["churn_risk"] = np.select(
        [df["churn_score"] < 50,
         (df["churn_score"] >= 50) & (df["churn_score"] < 70),
         df["churn_score"] >= 70],
        ["low", "med", "high"], default="unkown",
    )
    return df


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    if DB.exists():
        return _enrich(_load_db(DB))
    return _enrich(pd.read_csv(CSV))


with st.spinner("Loading data…"):
    df_all = load_data()


# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ══════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("## 🔎 Filters")

def _ms(label, col):
    opts = sorted(df_all[col].dropna().unique().tolist())
    return st.sidebar.multiselect(label, opts, default=opts)

f_plan     = _ms("Plan type",          "plan_type")
f_contract = _ms("Contract type",      "contract_type")
f_sub      = _ms("Subscription source","subscription_type")
f_gender   = _ms("Gender",             "gender")
f_state    = _ms("State",              "state")

a_min = int(df_all["customer_age"].min())
a_max = int(df_all["customer_age"].max())
f_age = st.sidebar.slider("Age range", a_min, a_max, (a_min, a_max)) if a_min < a_max else (a_min, a_max)

df = df_all[
    df_all["plan_type"].isin(f_plan)
    & df_all["contract_type"].isin(f_contract)
    & df_all["subscription_type"].isin(f_sub)
    & df_all["gender"].isin(f_gender)
    & df_all["state"].isin(f_state)
    & df_all["customer_age"].between(*f_age)
].copy()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(df)}** of **{len(df_all)}** customers")


# ══════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<h1 style='font-family:Space Grotesk,sans-serif;font-size:2.2rem;"
    f"font-weight:700;color:{TEXT};margin:0 0 4px 0;'>📉 Customer Churn Analysis</h1>"
    f"<p style='color:{MUTED};font-size:0.9rem;margin:0 0 1.5rem 0;'>"
    f"Interactive dashboard &nbsp;·&nbsp; Use sidebar filters to slice every chart</p>",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No customers match the filters — please widen a selection in the sidebar.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
def fig_style(fig: go.Figure, h: int = 380) -> go.Figure:
    fig.update_layout(
        height=h,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color=TEXT, size=12),
        margin=dict(l=16, r=16, t=48, b=16),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT, size=11)),
        title_font=dict(family="Space Grotesk", size=14, color=TEXT),
        title_x=0.01,
    )
    fig.update_xaxes(gridcolor=BORDER, zeroline=False, tickfont=dict(color=MUTED, size=11))
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, tickfont=dict(color=MUTED, size=11))
    return fig


def seg_table(col: str) -> pd.DataFrame:
    return (
        df.groupby(col)
        .agg(
            churn_rate_pct=("churn_flag",      lambda x: round(x.mean() * 100, 1)),
            total_revenue =("monthly_charges", "sum"),
            user_count    =("customerid",      "nunique"),
        )
        .reset_index()
        .sort_values("churn_rate_pct", ascending=False)
        .assign(total_revenue=lambda d: d["total_revenue"].round(2))
    )


def seg_bar(tbl: pd.DataFrame, col: str, title: str, h: int = 360) -> go.Figure:
    clrs = [RED if v >= 50 else AMBER if v > 20 else GREEN for v in tbl["churn_rate_pct"]]
    fig = go.Figure(go.Bar(
        x=tbl[col], y=tbl["churn_rate_pct"],
        marker=dict(color=clrs, cornerradius=6),
        text=[f"{r:.0f}%  ({n} users)" for r, n in zip(tbl["churn_rate_pct"], tbl["user_count"])],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        customdata=tbl["total_revenue"],
        hovertemplate="<b>%{x}</b><br>Churn: %{y:.1f}%<br>Revenue: ₹%{customdata:.2f}<extra></extra>",
    ))
    fig.update_layout(title=title, yaxis=dict(range=[0, 120], title="Churn rate (%)"), xaxis_title=None)
    return fig_style(fig, h)


def seg_block(col: str, title: str):
    tbl = seg_table(col)
    st.plotly_chart(seg_bar(tbl, col, title), use_container_width=True)
    st.dataframe(
        tbl, hide_index=True, width='stretch',
        column_config={
            "churn_rate_pct": st.column_config.ProgressColumn(
                "Churn %", min_value=0, max_value=100, format="%.1f%%"),
            "total_revenue":  st.column_config.NumberColumn("Revenue (₹)", format="₹%.2f"),
            "user_count":     st.column_config.NumberColumn("Users"),
        },
    )


# ══════════════════════════════════════════════════════════════════════════
# KPI METRICS  (notebook section 3 – 10 metrics)
# ══════════════════════════════════════════════════════════════════════════
churn_rate      = df["churn_flag"].mean() * 100
retention_rate  = 100 - churn_rate
arpu            = df["monthly_charges"].mean()
rev_at_risk     = df.loc[df["churn_flag"] == 1, "monthly_charges"].sum()
avg_tenure      = df["tenure_days"].mean()
avg_age         = df["customer_age"].mean()
esc_rate        = df["escalation_flag"].mean() * 100
avg_complaints  = df["complaint_count"].sum() / max(df["customerid"].nunique(), 1)
corr_val        = (df[["escalation_flag", "churn_flag"]].dropna()
                   ["escalation_flag"].corr(
                       df.loc[df[["escalation_flag", "churn_flag"]].dropna().index, "churn_flag"]))
total_rev       = df["monthly_charges"].sum()

# Row 1
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("👥 Total Customers",   f"{len(df):,}")
c2.metric("📉 Churn Rate",         f"{churn_rate:.1f}%")
c3.metric("💚 Retention Rate",     f"{retention_rate:.1f}%")
c4.metric("💰 ARPU",               f"₹{arpu:.2f}")
c5.metric("🔥 Revenue at Risk",    f"₹{rev_at_risk:.2f}")

st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

# Row 2
c6, c7, c8, c9, c10 = st.columns(5)
c6.metric("📅 Avg Tenure",         f"{avg_tenure:.0f} days")
c7.metric("🎂 Avg Age",            f"{avg_age:.1f} yrs")
c8.metric("⚡ Escalation Rate",    f"{esc_rate:.1f}%")
c9.metric("📋 Complaints/User",    f"{avg_complaints:.2f}")
c10.metric("🔗 Esc↔Churn Corr",   f"{corr_val:.2f}")

st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠  Overview",
    "📊  Segments",
    "⚠️  Churn Risk",
    "🎧  Support",
    "🗄️  Data & SQL",
])


# ════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════
with tab1:

    left, right = st.columns([1, 1.6])

    # --- Donut ---
    with left:
        churned  = int(df["churn_flag"].sum())
        retained = len(df) - churned
        fig_d = go.Figure(go.Pie(
            labels=["Churned", "Retained"],
            values=[churned, retained],
            hole=0.65,
            marker_colors=[RED, GREEN],
            sort=False,
            textinfo="label+percent",
            textfont=dict(color="#fff", size=13),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
        ))
        fig_d.update_layout(
            title="Churned vs Retained",
            showlegend=False,
            annotations=[dict(
                text=f"<b>{churn_rate:.1f}%</b><br><span style='font-size:12px'>churn</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=22, color=TEXT, family="Space Grotesk"),
            )],
        )
        st.plotly_chart(fig_style(fig_d, 400), use_container_width=True)

    # --- Plan churn bar ---
    with right:
        pt = seg_table("plan_type")
        st.plotly_chart(seg_bar(pt, "plan_type", "Churn Rate by Plan Type", 400), use_container_width=True)

    # --- Summary pivot table ---
    st.subheader("Plan Type Summary")
    pivot = (
        df.groupby("plan_type")
        .agg(
            Users         = ("customerid",      "nunique"),
            Revenue       = ("monthly_charges", "sum"),
            Churn_Rate    = ("churn_flag",       lambda x: round(x.mean() * 100, 1)),
            Avg_CLTV      = ("cltv",             "mean"),
            Avg_ChurnScore= ("churn_score",      "mean"),
        )
        .rename(columns={
            "Revenue":        "Monthly Revenue (₹)",
            "Churn_Rate":     "Churn Rate %",
            "Avg_CLTV":       "Avg CLTV",
            "Avg_ChurnScore": "Avg Churn Score",
        })
        .reset_index()
    )
    st.dataframe(
        pivot, hide_index=True, width='stretch',
        column_config={
            "Churn Rate %":        st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%"),
            "Monthly Revenue (₹)": st.column_config.NumberColumn(format="₹%.2f"),
            "Avg CLTV":            st.column_config.NumberColumn(format="%.0f"),
            "Avg Churn Score":     st.column_config.NumberColumn(format="%.1f"),
        },
    )

    # --- Tenure histogram ---
    st.subheader("Customer Tenure Distribution")
    fig_t = px.histogram(
        df, x="tenure_days",
        color=df["churn_flag"].map({0: "Retained", 1: "Churned"}),
        nbins=15, barmode="overlay",
        color_discrete_map={"Retained": GREEN, "Churned": RED},
        labels={"tenure_days": "Tenure (days)", "color": "Status"},
        title="Tenure Distribution — Churned vs Retained",
    )
    fig_t.update_traces(opacity=0.78)
    fig_t.update_layout(xaxis_title="Tenure (days)", yaxis_title="Customers")
    st.plotly_chart(fig_style(fig_t, 360), use_container_width=True)


# ════════════════════════════
# TAB 2 — SEGMENTS
# ════════════════════════════
with tab2:

    col_a, col_b = st.columns(2)
    with col_a:
        seg_block("state",             "Churn Rate by State")
    with col_b:
        seg_block("subscription_type", "Churn Rate by Subscription Source")

    col_c, col_d = st.columns(2)
    with col_c:
        seg_block("contract_type", "Churn Rate by Contract Type")
    with col_d:
        seg_block("gender", "Churn Rate by Gender")

    st.subheader("Monthly Charges vs Churn Score")
    fig_sc = px.scatter(
        df,
        x="monthly_charges", y="churn_score",
        color=df["churn_flag"].map({0: "Retained", 1: "Churned"}),
        color_discrete_map={"Retained": GREEN, "Churned": RED},
        size=[10] * len(df),
        hover_data={"customer_name": True, "plan_type": True, "state": True,
                    "monthly_charges": True, "churn_score": True},
        title="Monthly Charges vs Churn Score  (each dot = 1 customer)",
        labels={"monthly_charges": "Monthly Charges (₹)", "churn_score": "Churn Score"},
    )
    fig_sc.update_traces(marker=dict(size=11, opacity=0.85, line=dict(width=1, color="#fff")))
    st.plotly_chart(fig_style(fig_sc, 420), use_container_width=True)


# ════════════════════════════
# TAB 3 — CHURN RISK
# ════════════════════════════
with tab3:

    r1, r2 = st.columns(2)

    with r1:
        rc = (df["churn_risk"]
              .value_counts()
              .reindex(["low", "med", "high"], fill_value=0)
              .reset_index())
        rc.columns = ["churn_risk", "customers"]
        fig_risk = px.bar(
            rc, x="churn_risk", y="customers",
            color="churn_risk",
            color_discrete_map=RISK_CLR,
            text="customers",
            title="Customers by Churn Risk  (Low < 50 · Med 50–69 · High ≥ 70)",
        )
        fig_risk.update_traces(textposition="outside", textfont_size=12)
        fig_risk.update_layout(showlegend=False, xaxis_title="Risk Level", yaxis_title="Customers",
                               yaxis=dict(range=[0, rc["customers"].max() * 1.3]))
        st.plotly_chart(fig_style(fig_risk, 380), use_container_width=True)

    with r2:
        fig_age = px.histogram(
            df, x="customer_age",
            color=df["churn_flag"].map({0: "Retained", 1: "Churned"}),
            nbins=10, barmode="overlay",
            color_discrete_map={"Retained": GREEN, "Churned": RED},
            title="Customer Age Distribution by Churn Status",
            labels={"customer_age": "Age (years)"},
        )
        fig_age.update_traces(opacity=0.78)
        fig_age.update_layout(xaxis_title="Age (years)", yaxis_title="Customers")
        st.plotly_chart(fig_style(fig_age, 380), use_container_width=True)

    st.subheader("CLTV vs Churn Score")
    fig_b = px.scatter(
        df, x="cltv", y="churn_score",
        color=df["churn_flag"].map({0: "Retained", 1: "Churned"}),
        size="monthly_charges",
        color_discrete_map={"Retained": GREEN, "Churned": RED},
        hover_data={"customer_name": True, "plan_type": True, "churn_risk": True,
                    "cltv": True, "churn_score": True},
        title="CLTV vs Churn Score  (bubble size = monthly charge)",
        labels={"cltv": "Customer Lifetime Value", "churn_score": "Churn Score"},
    )
    fig_b.update_traces(marker=dict(opacity=0.78, line=dict(width=1, color="#fff")))
    st.plotly_chart(fig_style(fig_b, 420), use_container_width=True)

    st.subheader("Risk Level Deep-Dive")
    rd = (
        df.groupby("churn_risk")
        .agg(
            Customers       = ("customerid",      "nunique"),
            Avg_Churn_Score = ("churn_score",     "mean"),
            Already_Churned = ("churn_flag",      "sum"),
            Avg_Monthly     = ("monthly_charges", "mean"),
            Avg_CLTV        = ("cltv",            "mean"),
        )
        .reindex(["low", "med", "high"])
        .reset_index()
        .rename(columns={
            "churn_risk":      "Risk Level",
            "Avg_Churn_Score": "Avg Churn Score",
            "Already_Churned": "Already Churned",
            "Avg_Monthly":     "Avg Monthly (₹)",
            "Avg_CLTV":        "Avg CLTV",
        })
    )
    st.dataframe(rd, hide_index=True, width='stretch',
                 column_config={
                     "Avg Churn Score": st.column_config.NumberColumn(format="%.1f"),
                     "Avg Monthly (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                     "Avg CLTV":        st.column_config.NumberColumn(format="%.0f"),
                 })

    if df["churn_flag"].sum() > 0:
        st.subheader("Cancellation Reasons")
        cr = (df.loc[df["churn_flag"] == 1, "cancellation_reason"]
                .value_counts().reset_index())
        cr.columns = ["reason", "count"]
        if not cr.empty:
            fig_cr = px.bar(
                cr, x="count", y="reason", orientation="h",
                color_discrete_sequence=[RED], text="count",
                title="Why Customers Cancel",
            )
            fig_cr.update_traces(textposition="outside")
            fig_cr.update_layout(yaxis=dict(autorange="reversed", title=None),
                                 xaxis_title="Customers")
            st.plotly_chart(fig_style(fig_cr, 300), use_container_width=True)


# ════════════════════════════
# TAB 4 — SUPPORT
# ════════════════════════════
with tab4:

    s1, s2 = st.columns(2)

    with s1:
        ec = (df["escalation_flag"]
              .map({0: "No Escalation", 1: "Escalated"})
              .value_counts().reset_index())
        ec.columns = ["status", "count"]
        fig_ep = px.pie(
            ec, names="status", values="count",
            color="status",
            color_discrete_map={"No Escalation": BLUE, "Escalated": RED},
            hole=0.58,
            title="Escalation Split",
        )
        fig_ep.update_traces(textinfo="label+percent", textfont_size=13)
        st.plotly_chart(fig_style(fig_ep, 380), use_container_width=True)

    with s2:
        esc_c = (
            df.groupby("escalation_flag")
            .agg(churn_rate=("churn_flag", lambda x: round(x.mean() * 100, 1)),
                 customers =("customerid", "nunique"))
            .reset_index()
            .assign(group=lambda d: d["escalation_flag"].map({0: "No Escalation", 1: "Escalated"}))
        )
        fig_ec2 = px.bar(
            esc_c, x="group", y="churn_rate",
            color="group",
            color_discrete_map={"No Escalation": BLUE, "Escalated": RED},
            text=[f"{v}%" for v in esc_c["churn_rate"]],
            title=f"Churn Rate: Escalated vs Not  (correlation = {corr_val:.2f})",
        )
        fig_ec2.update_traces(textposition="outside", textfont_size=13)
        fig_ec2.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Churn Rate %",
                              yaxis=dict(range=[0, 120]))
        st.plotly_chart(fig_style(fig_ec2, 380), use_container_width=True)

    if "csat_score" in df.columns and df["csat_score"].notna().sum() > 0:
        st.subheader("CSAT Analysis")
        s3, s4 = st.columns(2)

        with s3:
            fig_cs = px.histogram(
                df.dropna(subset=["csat_score"]), x="csat_score", nbins=10,
                color_discrete_sequence=[PURPLE],
                title="CSAT Score Distribution",
            )
            fig_cs.update_layout(xaxis_title="CSAT Score", yaxis_title="Customers")
            st.plotly_chart(fig_style(fig_cs, 340), use_container_width=True)

        with s4:
            csat_df = df.dropna(subset=["csat_score"]).copy()
            csat_df["csat_band"] = pd.cut(
                csat_df["csat_score"],
                bins=[0, 30, 60, 100],
                labels=["Low (0–30)", "Mid (31–60)", "High (61–100)"],
                include_lowest=True,
            )
            cb = (csat_df.groupby("csat_band", observed=False)
                  .agg(churn_rate=("churn_flag", lambda x: round(x.mean() * 100, 1)),
                       customers =("customerid", "nunique"))
                  .reset_index())
            fig_cb = px.bar(
                cb, x="csat_band", y="churn_rate",
                color_discrete_sequence=[PURPLE],
                text=[f"{v}%" for v in cb["churn_rate"]],
                title="Churn Rate by CSAT Band",
            )
            fig_cb.update_traces(textposition="outside")
            fig_cb.update_layout(xaxis_title="CSAT Band", yaxis_title="Churn Rate %",
                                 yaxis=dict(range=[0, 120]))
            st.plotly_chart(fig_style(fig_cb, 340), use_container_width=True)

    st.subheader("Support Activity by Customer")
    sup_cols = ["customer_name", "state", "plan_type", "escalation_flag",
                "csat_score", "complaint_count", "churn_flag", "churn_risk"]
    avail = [c for c in sup_cols if c in df.columns]
    st.dataframe(
        df[avail].sort_values("escalation_flag", ascending=False).reset_index(drop=True),
        hide_index=True, use_container_width=True,
        column_config={
            "escalation_flag": st.column_config.CheckboxColumn("Escalated?"),
            "churn_flag":      st.column_config.CheckboxColumn("Churned?"),
        },
    )


# ════════════════════════════
# TAB 5 — DATA & SQL
# ════════════════════════════
with tab5:

    st.subheader("Full Merged Dataset")
    st.dataframe(df.reset_index(drop=True), hide_index=True, use_container_width=True)
    st.download_button(
        "⬇️  Download filtered CSV",
        df.to_csv(index=False).encode(),
        "churn_filtered.csv",
        "text/csv",
    )

    st.markdown("---")
    st.subheader("SQL Playground")
    st.caption("Read-only queries against **customer_churn.db** · Tables: `db_customer`, `db_subscription`, `db_support`")

    default_sql = (
        "SELECT plan_type,\n"
        "       COUNT(*)                                             AS users,\n"
        "       ROUND(SUM(monthly_charges), 2)                      AS monthly_revenue,\n"
        "       ROUND(AVG(cancellation_date IS NOT NULL) * 100, 1)  AS churn_pct\n"
        "FROM   db_subscription\n"
        "GROUP  BY plan_type\n"
        "ORDER  BY churn_pct DESC"
    )
    query = st.text_area("SQL query", default_sql, height=180)

    if st.button("▶️  Run Query", type="primary"):
        q = query.strip().rstrip(";")
        if not DB.exists():
            st.error("`customer_churn.db` not found next to app.py.")
        elif not re.match(r"^(select|with)\b", q, re.IGNORECASE) or ";" in q:
            st.error("Only a single SELECT / WITH query is allowed.")
        else:
            try:
                conn   = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
                result = pd.read_sql(q, conn)
                conn.close()
                st.success(f"{len(result)} row(s) returned")
                st.dataframe(result, hide_index=True, width='stretch')
            except Exception as e:
                st.error(f"Query failed: {e}")

