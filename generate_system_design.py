"""
Generate a professional System Design diagram PNG  (Excalidraw-style)
Run: python generate_system_design.py  (from project root with venv active)
"""
import plotly.graph_objects as go
from pathlib import Path

OUT = Path("screenshots")
OUT.mkdir(exist_ok=True)

# ── palette ──────────────────────────────────────────────────
BG      = "#F8F9FA"
BLUE    = "#1971C2";  BLUE_L  = "#E7F5FF";  BLUE_B  = "#74C0FC"
GREEN   = "#2F9E44";  GREEN_L = "#EBFBEE";  GREEN_B = "#8CE99A"
PURPLE  = "#7048E8";  PURPLE_L= "#F3F0FF";  PURPLE_B= "#B197FC"
RED     = "#C92A2A";  RED_L   = "#FFF5F5";  RED_B   = "#FFA8A8"
AMBER   = "#E67700";  AMBER_L = "#FFF9DB";  AMBER_B = "#FFD43B"
DARK    = "#212529"
GRAY    = "#868E96"
WHITE   = "#FFFFFF"

W, H = 1500, 1000

fig = go.Figure()
fig.update_layout(
    width=W, height=H,
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    margin=dict(l=0, r=0, t=0, b=0),
    xaxis=dict(visible=False, range=[0, W]),
    yaxis=dict(visible=False, range=[0, H], scaleanchor="x", scaleratio=1),
    showlegend=False,
)

# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════
def rect(x0,y0,x1,y1, fill=WHITE, border=DARK, bw=1.5, dash="solid", radius=8, layer="below"):
    fig.add_shape(type="rect", x0=x0, y0=H-y1, x1=x1, y1=H-y0,
        fillcolor=fill, line=dict(color=border, width=bw, dash=dash),
        layer=layer)

def label(x, y, txt, size=12, color=DARK, bold=False, anchor="center", family="Arial"):
    weight = "<b>" if bold else ""
    weight_e = "</b>" if bold else ""
    fig.add_annotation(x=x, y=H-y, text=f"{weight}{txt}{weight_e}",
        showarrow=False, xanchor=anchor, yanchor="middle",
        font=dict(size=size, color=color, family=family))

def band(x0, y0, x1, y1, fill, border, title, icon, bw=2):
    rect(x0, y0, x1, y1, fill=fill, border=border, bw=bw)
    # top accent strip
    rect(x0, y0, x1, y0+28, fill=border, border=border, bw=0, layer="above")
    label((x0+x1)/2, y0+14, f"{icon}  {title}", size=13, color=WHITE, bold=True)

def card(x0, y0, x1, y1, fill, border, title, lines):
    # shadow
    rect(x0+4, y0+4, x1+4, y1+4, fill="rgba(0,0,0,0.12)", border="rgba(0,0,0,0)", bw=0)
    rect(x0, y0, x1, y1, fill=fill, border=border, bw=2)
    rect(x0, y0, x1, y0+32, fill=border, border=border, bw=0)
    label((x0+x1)/2, y0+16, title, size=12, color=WHITE, bold=True)
    for i, line in enumerate(lines):
        label(x0+12, y0+44+i*18, line, size=10.5, color=DARK, anchor="left", family="Courier New")

def arrow_h(x0, y0, x1, lbl=""):
    fig.add_annotation(x=x1, y=H-y0,
        ax=x0, ay=H-y0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.2,
        arrowwidth=2, arrowcolor=DARK)
    if lbl:
        label((x0+x1)/2, y0-10, lbl, size=9, color=GRAY, family="Courier New")

def arrow_v(x0, y0, y1, lbl=""):
    fig.add_annotation(x=x0, y=H-y1,
        ax=x0, ay=H-y0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True, arrowhead=2, arrowsize=1.2,
        arrowwidth=2, arrowcolor=DARK)
    if lbl:
        label(x0+8, (y0+y1)/2, lbl, size=9, color=GRAY, anchor="left", family="Courier New")

def tag(x0, y0, txt, fill, color):
    w = len(txt)*7+16
    rect(x0, y0, x0+w, y0+22, fill=fill, border=color, bw=1)
    label(x0+w/2, y0+11, txt, size=9.5, color=color, bold=True)
    return x0+w+6


# ════════════════════════════════════════════════════════════
# TITLE BAR
# ════════════════════════════════════════════════════════════
rect(0, 0, W, 50, fill=BLUE, border=BLUE, bw=0, layer="below")
label(W/2, 25, "Customer Churn Analysis — System Design", size=18, color=WHITE, bold=True)

# ════════════════════════════════════════════════════════════
# LAYER 1  —  DATA LAYER
# ════════════════════════════════════════════════════════════
band(20, 60, W-20, 240, fill=BLUE_L, border=BLUE, bw=2,
     title="DATA LAYER  —  customer_churn.db  (SQLite)", icon="📦")

# db_customer
card(40, 95, 310, 228, fill=WHITE, border=BLUE, title="🗂  db_customer",
     lines=["🔑 customerid  TEXT (PK)",
             "   name        TEXT",
             "   country     TEXT (3 nulls)",
             "   state       TEXT",
             "   gender      TEXT",
             "   dob         TIMESTAMP",
             "✕  interests   TEXT  (DROPPED)",
             "✕  pincode     REAL  (DROPPED)",
             "──────────────────────",
             "   21 rows"])

# db_subscription
card(360, 95, 700, 228, fill=WHITE, border=GREEN, title="💳  db_subscription",
     lines=["🔗 customerid          TEXT (FK)",
             "   subscription_start  TEXT→date",
             "   subscription_type   TEXT",
             "   renewal_date        TEXT→date",
             "   plan_type           TEXT",
             "   contract_type       TEXT",
             "   cancellation_date   TEXT→date",
             "   monthly_charges     REAL",
             "   cltv                INTEGER",
             "   churn_score         INTEGER  •  21 rows"])

# db_support
card(750, 95, 1050, 228, fill=WHITE, border=PURPLE, title="🎧  db_support",
     lines=["🔗 customerid   TEXT (FK, non-unique)",
             "   complaint_date TIMESTAMP",
             "   escalations    TEXT  (Y / N)",
             "   csat_score     INTEGER  (0–100)",
             "✕  col_1          REAL  (DROPPED)",
             "✕  comment        TEXT  (DROPPED)",
             "──────────────────────────────",
             "   9 rows  →  7 unique customers",
             "   Dedup: keep latest complaint/customer"])

# SQLite badge
rect(1090, 100, 1460, 230, fill=AMBER_L, border=AMBER, bw=2, dash="dash")
label(1275, 118, "🗄  SQLite Database", size=14, color=AMBER, bold=True)
label(1275, 145, "customer_churn.db", size=12, color=DARK, family="Courier New")
label(1275, 165, "Fallback →", size=11, color=GRAY)
label(1275, 183, "exported_churn_data.csv", size=11, color=DARK, family="Courier New")

# ── relationships ────────────────────────────────────────────
# FK lines inside data layer
fig.add_shape(type="line", x0=360, y0=H-162, x1=310, y1=H-162,
    line=dict(color=GREEN, width=1.5, dash="dot"))
fig.add_annotation(x=335, y=H-150, text="FK", showarrow=False,
    font=dict(size=9, color=GREEN, family="Arial Bold"))

fig.add_shape(type="line", x0=750, y0=H-162, x1=700, y1=H-162,
    line=dict(color=PURPLE, width=1.5, dash="dot"))
fig.add_annotation(x=725, y=H-150, text="FK", showarrow=False,
    font=dict(size=9, color=PURPLE, family="Arial Bold"))


# ════════════════════════════════════════════════════════════
# ARROW  Layer 1 → Layer 2
# ════════════════════════════════════════════════════════════
arrow_v(W//2, 240, 268, "pandas.read_sql()")

# ════════════════════════════════════════════════════════════
# LAYER 2  —  DATA PIPELINE
# ════════════════════════════════════════════════════════════
band(20, 275, W-20, 480, fill=GREEN_L, border=GREEN, bw=2,
     title="DATA PIPELINE  (churn_analysis.ipynb)", icon="⚙️")

card(40, 310, 290, 465, fill=WHITE, border=BLUE,  title="§1  IMPORT",
     lines=["sqlite3.connect()",
             "pd.read_sql()",
             "3 tables → 3 DFs",
             "Schema inspection"])

card(310, 310, 600, 465, fill=WHITE, border=AMBER, title="§2  CLEANING",
     lines=["Rename: name→customer_name",
             "Drop: interests, pincode",
             "        col_1, comment",
             "Cast dates → datetime64",
             "Gender: Men/Women→M/F",
             "Fill country via state map",
             "Dedup support (keep last)"])

card(620, 310, 950, 465, fill=WHITE, border=PURPLE, title="§3  FEATURE ENG.",
     lines=["churn_flag  (cancel≠NULL)",
             "tenure_days (cancel–start)",
             "customer_age (today–dob)",
             "escalation_flag (Y→1,N→0)",
             "complaint_count (groupby)",
             "churn_risk (<50=low,",
             "   50-69=med, ≥70=high)"])

card(970, 310, 1260, 465, fill=WHITE, border=RED, title="MERGE  (LEFT JOIN)",
     lines=["sub.merge(customer,",
             "   on='customerid',",
             "   how='LEFT')",
             ".merge(support,",
             "   on='customerid',",
             "   how='LEFT')",
             "Result: 21 rows × 24 cols"])

# pipeline arrows
arrow_h(290, 388, 310, "")
arrow_h(600, 388, 620, "")
arrow_h(950, 388, 970, "")

# cache badge
rect(1280, 320, 1460, 400, fill=WHITE, border=GREEN, bw=1.5)
label(1370, 346, "⚡ @st.cache_data", size=11, color=GREEN, bold=True)
label(1370, 365, "Cached on first load", size=10, color=GRAY)
label(1370, 382, "Reactive on filter change", size=10, color=GRAY)

# ════════════════════════════════════════════════════════════
# ARROW  Layer 2 → Layer 3
# ════════════════════════════════════════════════════════════
arrow_v(W//2, 480, 510, "Master DataFrame  (21 × 24)")

# ════════════════════════════════════════════════════════════
# LAYER 3  —  ANALYTICS
# ════════════════════════════════════════════════════════════
band(20, 517, W-20, 660, fill=RED_L, border=RED, bw=2,
     title="ANALYTICS LAYER  —  10 KPIs + Segmentation", icon="📊")

for i, (title, lines, clr) in enumerate([
    ("📈  KPIs",
     ["Churn Rate 28.6%", "Retention 71.4%",
      "ARPU ₹18.85", "Rev at Risk ₹73.94",
      "Avg Tenure 1,580d"], RED),
    ("🔀  Segmentation",
     ["By plan_type", "By state",
      "By subscription_type", "By contract_type",
      "By gender"], AMBER),
    ("⚠️  Churn Risk",
     ["low  < 50 score", "med  50 – 69",
      "high ≥ 70", "CLTV analysis",
      "Cancellation reasons"], PURPLE),
    ("🎧  Support",
     ["Escalation rate 19%", "Corr esc↔churn 0.77",
      "CSAT analysis", "Complaint count",
      "Support activity"], GREEN),
]):
    x0 = 40 + i*365
    x1 = x0 + 340
    card(x0, 550, x1, 648, fill=WHITE, border=clr, title=title, lines=lines)


# ════════════════════════════════════════════════════════════
# ARROW  Layer 3 → Layer 4
# ════════════════════════════════════════════════════════════
arrow_v(W//2, 660, 690, "Plotly charts + st.metric")

# ════════════════════════════════════════════════════════════
# LAYER 4  —  PRESENTATION
# ════════════════════════════════════════════════════════════
band(20, 697, W-20, 975, fill=PURPLE_L, border=PURPLE, bw=2,
     title="PRESENTATION LAYER  —  Streamlit Dashboard  (app.py)", icon="🖥️")

# sidebar
rect(40, 730, 185, 962, fill=WHITE, border=PURPLE, bw=2, dash="dash")
rect(40, 730, 185, 760, fill=PURPLE, border=PURPLE, bw=2)
label(112, 745, "🔎  Sidebar", size=11, color=WHITE, bold=True)
for i, f in enumerate(["Plan type","Contract type","Sub. source","Gender","State","Age range"]):
    label(70, 775 + i*28, f"▸  {f}", size=10, color=DARK, anchor="left")

# 5 tabs
tabs = [
    ("🏠 Overview", BLUE,   BLUE_L,
     ["10 KPI cards", "Donut chart", "Plan bar", "Pivot table", "Tenure hist"]),
    ("📊 Segments", GREEN,  GREEN_L,
     ["By State", "By Source", "By Contract", "By Gender", "Scatter plot"]),
    ("⚠️ Risk",     RED,    RED_L,
     ["Risk bars", "Age dist", "CLTV bubble", "Risk table", "Cancel rsns"]),
    ("🎧 Support",  PURPLE, PURPLE_L,
     ["Esc pie", "Corr bar", "CSAT dist", "CSAT bands", "Activity tbl"]),
    ("🗄️ Data+SQL", AMBER,  AMBER_L,
     ["Full table", "CSV export", "SQL editor", "Live query", "vs SQLite"]),
]
for i, (title, clr, clr_l, items) in enumerate(tabs):
    x0 = 200 + i*258
    x1 = x0 + 240
    card(x0, 730, x1, 962, fill=clr_l, border=clr, title=title, lines=items)

# tech stack strip
rect(20, 968, W-20, 1000, fill="#212529", border="#212529", bw=0)
label(W/2-250, 984, "Tech Stack:", size=11, color=WHITE, bold=True, anchor="left")
tx = W/2-170
for txt, clr in [("Python 3.10+",BLUE_B),("Pandas 3.1",GREEN_B),("NumPy",GREEN_B),
                 ("Plotly 7.1",PURPLE_B),("Streamlit 1.67",RED_B),("SQLite3",AMBER_B),("Kaleido",GRAY)]:
    tx = tag(tx, 976, txt, "rgba(255,255,255,0.08)", clr)

fig.write_image(str(OUT / "08_system_design.png"), scale=2)
print("✅  08_system_design.png")
