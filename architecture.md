# System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     CUSTOMER CHURN ANALYSIS SYSTEM                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                              │
│                                                                          │
│   ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│   │  db_customer     │    │  db_subscription │    │  db_support      │  │
│   │─────────────────│    │──────────────────│    │──────────────────│  │
│   │ customerid (PK) │    │ customerid (FK)  │    │ customerid (FK)  │  │
│   │ customer_name   │    │ subscription_    │    │ complaint_date   │  │
│   │ country         │───▶│   start_date     │◀───│ escalations      │  │
│   │ state           │    │ renewal_date     │    │ csat_score       │  │
│   │ gender          │    │ plan_type        │    │ complaint_count  │  │
│   │ dob             │    │ contract_type    │    └──────────────────┘  │
│   └─────────────────┘    │ cancellation_    │                          │
│                           │   date/reason    │                          │
│        SQLite DB          │ monthly_charges  │                          │
│   customer_churn.db       │ cltv             │                          │
│                           │ churn_score      │                          │
│                           └──────────────────┘                          │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  DATA PIPELINE  (churn_analysis.ipynb → app.py)                          │
│                                                                          │
│  ┌────────────┐   ┌─────────────────┐   ┌──────────────────────────┐   │
│  │  IMPORT    │──▶│  DATA CLEANING  │──▶│  FEATURE ENGINEERING     │   │
│  │            │   │                 │   │                          │   │
│  │ SQLite →   │   │ • Rename cols   │   │ • churn_flag             │   │
│  │ Pandas DF  │   │ • Drop cols     │   │   (cancellation ≠ NULL)  │   │
│  │            │   │ • Fix dtypes    │   │ • tenure_days            │   │
│  │ 3 tables   │   │ • Standardise   │   │   (cancel_date - start)  │   │
│  │ → merged   │   │   gender        │   │ • customer_age           │   │
│  │   master   │   │ • Fill missing  │   │   (today - dob)          │   │
│  │   (21 rows)│   │   country via   │   │ • escalation_flag (Y/N)  │   │
│  └────────────┘   │   state map     │   │ • churn_risk bucket      │   │
│                   │ • Dedup support │   │   Low(<50)/Med/High(≥70) │   │
│                   │   keep latest   │   │ • complaint_count        │   │
│                   └─────────────────┘   └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  ANALYTICS LAYER                                                         │
│                                                                          │
│   KPI Metrics           Segmentation           Statistical               │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────────┐     │
│   │ Churn Rate   │      │ By Plan Type │      │ Corr: Escalation │     │
│   │ 28.6%        │      │ By State     │      │ vs Churn = 0.77  │     │
│   │ Retention    │      │ By Contract  │      │                  │     │
│   │ 71.4%        │      │ By Gender    │      │ CSAT → Churn     │     │
│   │ ARPU ₹18.85  │      │ By Sub.Type  │      │ band analysis    │     │
│   │ Rev at Risk  │      └──────────────┘      └──────────────────┘     │
│   │ ₹73.94       │                                                      │
│   │ Avg Tenure   │                                                      │
│   │ 1,580 days   │                                                      │
│   └──────────────┘                                                      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER  (Streamlit Dashboard — app.py)                      │
│                                                                          │
│  ┌─────────────┐                                                         │
│  │   Sidebar   │  Filters: Plan · Contract · Source · Gender · State     │
│  │   Filters   │  → All charts and KPIs update reactively                │
│  └─────────────┘                                                         │
│                                                                          │
│  ┌────────────┬────────────┬────────────┬────────────┬────────────┐     │
│  │ 🏠Overview │📊Segments  │⚠️Churn Risk│🎧Support   │🗄️Data+SQL │     │
│  ├────────────┼────────────┼────────────┼────────────┼────────────┤     │
│  │ KPI strip  │ By State   │ Risk bars  │ Escalation │ Full table │     │
│  │ Donut chart│ By Source  │ Age dist.  │ pie chart  │ CSV export │     │
│  │ Plan bars  │ By Contract│ CLTV bubble│ CSAT dist. │ SQL editor │     │
│  │ Summary tbl│ By Gender  │ Risk table │ Support tbl│ Live query │     │
│  │ Tenure hist│ Scatter    │ Cancel rsn │            │            │     │
│  └────────────┴────────────┴────────────┴────────────┴────────────┘     │
│                                                                          │
│  Tech: Streamlit 1.67 · Plotly 7.1 · Pandas 3.1 · Python 3.14          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
customer_churn.db
      │
      ├──▶ db_customer      ──┐
      ├──▶ db_subscription  ──┼──▶ Merge (LEFT JOIN on customerid) ──▶ Master DF
      └──▶ db_support       ──┘         │
                                        │
                              Clean + Feature Engineer
                                        │
                                        ▼
                              @st.cache_data (cached load)
                                        │
                                        ▼
                              Sidebar Filters (reactive)
                                        │
                               ┌────────┴────────┐
                               │  Filtered df    │
                               └────────┬────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
                 KPI Metrics        Plotly Charts       Dataframes
                (st.metric)      (px / go figures)   (st.dataframe)
```

## Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Data Import | `churn_analysis.ipynb` §1 | Load 3 SQLite tables into pandas |
| Data Cleaning | `churn_analysis.ipynb` §2 | Rename, drop, cast, standardise, fill nulls |
| Feature Eng. | `churn_analysis.ipynb` §3 | churn_flag, tenure, age, risk, escalation |
| Analysis | `churn_analysis.ipynb` §3 | 10 KPI calculations, segmentation |
| Visualisation | `churn_analysis.ipynb` §4 | Matplotlib/Seaborn charts (notebook only) |
| Dashboard | `files/app.py` | Full Streamlit interactive dashboard |
| Database | `customer_churn.db` | Source-of-truth SQLite (3 tables) |
| Fallback CSV | `exported_churn_data.csv` | Pre-merged export if DB unavailable |
