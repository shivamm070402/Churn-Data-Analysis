# 📉 Customer Churn Analysis

> End-to-end data analysis project: SQLite → Pandas → Streamlit interactive dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67-red?logo=streamlit)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-7.1-lightblue?logo=plotly)](https://plotly.com)
[![Pandas](https://img.shields.io/badge/Pandas-3.1-purple?logo=pandas)](https://pandas.pydata.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 📌 Project Overview

This project simulates a real-world **customer churn analysis pipeline** for a subscription business (think OTT / SaaS). Starting from a raw SQLite database with three normalised tables, it walks through every stage a data analyst would perform:

1. **Data Import** — extract 3 tables from SQLite into Pandas
2. **Data Cleaning** — rename columns, drop junk, fix dtypes, standardise gender, impute missing countries
3. **Feature Engineering** — derive churn flag, tenure, customer age, escalation flag, churn risk bucket
4. **Analytics** — 10 KPI calculations + multi-dimensional segmentation
5. **Visualisation** — Matplotlib/Seaborn in notebook → Plotly in Streamlit dashboard
6. **Interactive Dashboard** — fully filterable Streamlit app served locally

---

## 🗂️ Repository Structure

```
customer-churn-analysis/
│
├── churn_analysis.ipynb          # Main Jupyter notebook (all 4 sections)
├── customer_churn.db             # Source SQLite database (3 tables)
├── exported_churn_data.csv       # Pre-merged CSV fallback
│
├── files/
│   └── app.py                    # Streamlit dashboard
│
├── architecture.md               # System design & data flow diagrams
├── case_study.md                 # Full business case study write-up
├── README.md                     # This file
└── .gitignore
```

---

## 🗃️ Database Schema

```
customer_churn.db
├── db_customer       (21 rows)
│   ├── customerid    PK
│   ├── name
│   ├── country / state
│   ├── gender
│   └── dob
│
├── db_subscription   (21 rows)
│   ├── customerid    FK → db_customer
│   ├── subscription_start_date
│   ├── subscription_type   (Organic / Paid / Refferal)
│   ├── renewal_date
│   ├── plan_type           (Basic / Standard / Premium)
│   ├── contract_type       (Monthly / Annual)
│   ├── cancellation_date / cancellation_reason
│   ├── monthly_charges
│   ├── cltv
│   └── churn_score
│
└── db_support        (9 rows → 7 unique customers)
    ├── customerid    FK → db_customer
    ├── complaint_date
    ├── escalations   (Y / N)
    └── csat_score
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10 or higher
- pip

### Step 1 — Clone the repository
```bash
git clone https://github.com/<your-username>/customer-churn-analysis.git
cd customer-churn-analysis
```

### Step 2 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install streamlit pandas numpy plotly
```

### Step 4 — Copy the database next to app.py
```bash
# Windows PowerShell
Copy-Item customer_churn.db files\customer_churn.db
Copy-Item exported_churn_data.csv files\exported_churn_data.csv
```

### Step 5 — Run the Streamlit dashboard
```bash
cd files
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

### Step 6 — Run the Jupyter notebook (optional)
```bash
pip install jupyter matplotlib seaborn
jupyter notebook churn_analysis.ipynb
```

---

## 📊 Dashboard Tabs

| Tab | Charts & Features |
|-----|-------------------|
| **🏠 Overview** | 10 KPI metric cards · Churned vs Retained donut · Plan churn bar · Summary pivot table · Tenure histogram |
| **📊 Segments** | Churn by State · by Subscription Source · by Contract Type · by Gender · Monthly Charges vs Churn Score scatter |
| **⚠️ Churn Risk** | Risk bucket bar (Low/Med/High) · Age distribution · CLTV vs Churn Score bubble · Risk deep-dive table · Cancellation reasons |
| **🎧 Support** | Escalation split pie · Escalation vs Churn rate · CSAT distribution · Churn by CSAT band · Support activity table |
| **🗄️ Data & SQL** | Full merged dataset · CSV download · Live SQL playground against SQLite DB |

---

## 📐 System Architecture

See [`architecture.md`](architecture.md) for the full data flow and component diagram.

**High-level flow:**
```
SQLite DB (3 tables)
    └──▶ Pandas (clean + enrich)
              └──▶ @st.cache_data
                        └──▶ Sidebar filters (reactive)
                                  └──▶ Plotly charts + st.metric KPIs
```

---

## 🔑 Key Findings

| Metric | Value |
|--------|-------|
| Overall Churn Rate | **28.6%** |
| Retention Rate | **71.4%** |
| Highest Churn Plan | **Basic (60%)** |
| Highest Churn State | **Karnataka (100%)** |
| Highest Churn Source | **Referral (83%)** |
| Escalation ↔ Churn Correlation | **0.77 (strong positive)** |
| Avg Customer Tenure | **1,580 days** |
| Revenue at Risk | **₹73.94/month** |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| Notebook | Jupyter / JupyterLab |
| Data | SQLite · Pandas · NumPy |
| Visualisation | Plotly Express · Plotly Graph Objects |
| Dashboard | Streamlit 1.67 |
| Version Control | Git / GitHub |

---

## 📖 Case Study

See [`case_study.md`](case_study.md) for the full business case study including problem statement, methodology, insights, and recommendations.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 👤 Author

Made with ❤️ as a data analytics portfolio project.
