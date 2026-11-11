# 📋 Case Study: Customer Churn Analysis for a Subscription Business

---

## 1. Executive Summary

This case study documents an end-to-end data analysis engagement for a subscription-based business experiencing customer churn. Using a dataset of **21 customers** across three relational tables (customer demographics, subscription details, and support interactions), we identified key churn drivers, quantified business impact, and produced an interactive dashboard for ongoing monitoring.

**Key outcome:** Churn rate of **28.6%** with a strong correlation (0.77) between escalated support tickets and customer cancellation — indicating that support quality is a primary churn lever.

---

## 2. Business Context

### Company Profile
A subscription service (OTT/SaaS-style) operating across multiple Indian states, offering three plan tiers (Basic, Standard, Premium) on monthly or annual contracts. Customers are acquired through organic discovery, paid campaigns, and referrals.

### Business Problem
The business noticed increasing cancellations but lacked visibility into:
- **Who** is churning (demographics, plan type, geography)
- **Why** they are churning (support issues, pricing, competition)
- **When** they churn (tenure patterns, contract lifecycle)
- **How at-risk** the remaining customers are

### Business Questions
1. What is the overall churn rate and how does it vary by segment?
2. Which plan types, states, and subscription sources have the highest churn?
3. Is there a relationship between customer support interactions and churn?
4. What is the revenue impact of churn?
5. Which customers are at high risk of churning next?

---

## 3. Data Description

### Source
SQLite database (`customer_churn.db`) with three normalised tables:

| Table | Rows | Description |
|-------|------|-------------|
| `db_customer` | 21 | Demographics: name, state, country, gender, date of birth |
| `db_subscription` | 21 | Subscription: plan, contract, charges, CLTV, churn score, cancellation |
| `db_support` | 9 | Support: complaint dates, escalation flag, CSAT scores |

### Data Quality Issues Found
| Issue | Column | Fix Applied |
|-------|--------|------------|
| Inconsistent gender values | `gender` | `"Men" → "Male"`, `"Women" → "Female"` |
| Missing country (3 records) | `country` | Filled using state→country mapping from non-null rows |
| Duplicate support entries | `customerid` | Added `complaint_count`, kept latest complaint per customer |
| Junk columns | `interests`, `pincode`, `col_1`, `comment` | Dropped |
| Object-type dates | Multiple date columns | Cast to `datetime64` |

---

## 4. Methodology

### 4.1 Data Pipeline

```
Raw SQLite (3 tables)
       │
       ▼
  pandas.read_sql()          ← Extract
       │
       ▼
  Cleaning & Standardisation ← Transform
  (rename, drop, cast, fill)
       │
       ▼
  Feature Engineering        ← Enrich
  (churn_flag, tenure,
   customer_age, churn_risk)
       │
       ▼
  LEFT JOIN merge            ← Combine
  (subscription ← customer
               ← support)
       │
       ▼
  Master DataFrame (21 × 24) ← Analyse + Visualise
```

### 4.2 Feature Engineering

| New Feature | Derivation Logic |
|-------------|-----------------|
| `churn_flag` | `1` if `cancellation_date IS NOT NULL`, else `0` |
| `tenure_days` | `cancellation_date - subscription_start_date` (or today for active) |
| `customer_age` | `today.year - dob.year` minus birthday-not-yet correction |
| `escalation_flag` | `1` if `escalations == 'Y'`, else `0` |
| `complaint_count` | Count of support rows per `customerid` before dedup |
| `churn_risk` | `low` (score < 50) · `med` (50–69) · `high` (≥ 70) |

### 4.3 KPI Definitions

| KPI | Formula |
|-----|---------|
| Churn Rate | `churn_flag.mean() × 100` |
| Retention Rate | `100 − Churn Rate` |
| ARPU | `monthly_charges.mean()` |
| Revenue at Risk | `monthly_charges.sum()` where `churn_flag == 1` |
| Avg Tenure | `tenure_days.mean()` |
| Escalation Rate | `escalation_flag.mean() × 100` |
| Avg Complaints/User | `complaint_count.sum() / customerid.nunique()` |
| Escalation↔Churn Corr | `escalation_flag.corr(churn_flag)` |

---

## 5. Analysis & Findings

### 5.1 Overall Churn

| Metric | Value |
|--------|-------|
| Total Customers | 21 |
| Churned | 6 (28.6%) |
| Retained | 15 (71.4%) |
| Revenue at Risk | ₹73.94/month |

**Interpretation:** More than 1 in 4 customers has cancelled. At ₹73.94/month in lost revenue from just 21 customers, extrapolating to a larger base makes retention a critical business priority.

---

### 5.2 Churn by Plan Type

| Plan | Churn Rate | Users | Monthly Revenue |
|------|-----------|-------|----------------|
| Basic | **60.0%** | 5 | ₹41.94 |
| Standard | 22.2% | 9 | ₹125.91 |
| Premium | **14.3%** | 7 | ₹227.87 |

**Key Insight:** The Basic plan has 4× the churn rate of Premium. Basic customers are either price-sensitive, getting less value, or represent trial/low-commitment customers. The Premium plan — despite higher cost — retains customers better, suggesting perceived value is high.

**Recommendation:** Introduce a value-add or upsell nudge for Basic customers at the 90-day mark. Consider a "Basic+ trial" to Premium to reduce churn.

---

### 5.3 Churn by Geography (State)

| State | Churn Rate | Users |
|-------|-----------|-------|
| Karnataka | **100%** | 2 |
| Meghalaya | **66.7%** | 3 |
| Telangana | 50.0% | 2 |
| Delhi | 25.0% | 4 |
| Kathmandu | 0% | 2 |
| Maharashtra | 0% | 3 |
| Uttar Pradesh | 0% | 2 |

**Key Insight:** Karnataka and Meghalaya have alarmingly high churn rates. This could indicate regional competition, service quality issues, or demographic misalignment.

**Recommendation:** Investigate Karnataka and Meghalaya for regional service issues or competitor activity. Run targeted retention campaigns in these states.

---

### 5.4 Churn by Subscription Source

| Source | Churn Rate | Users |
|--------|-----------|-------|
| Referral | **83.3%** | 6 |
| Paid | 16.7% | 6 |
| Organic | **0.0%** | 9 |

**Key Insight:** Referral customers churn at a dramatically higher rate (83%) compared to organic (0%). This counter-intuitive finding suggests the referral program may be attracting low-intent customers — possibly driven by referral incentives rather than genuine product interest.

**Recommendation:** Audit the referral program. Add a minimum tenure gate (e.g., 60 days) before referral rewards are paid out. Focus acquisition on organic channels which show zero churn.

---

### 5.5 Churn by Contract Type

| Contract | Churn Rate |
|----------|-----------|
| Monthly | Higher |
| Annual | Lower |

**Key Insight:** Monthly contract customers churn at a higher rate — consistent with industry norms where annual commitments create stickiness.

**Recommendation:** Offer a discount (10–15%) to incentivise monthly customers to switch to annual plans.

---

### 5.6 Support & Escalation Analysis

| Metric | Value |
|--------|-------|
| Escalation Rate | 19.0% |
| Escalation ↔ Churn Correlation | **0.77** |
| Avg Complaints per User | 0.43 |

**Key Insight:** The 0.77 correlation between escalation and churn is the **strongest predictor** found in this dataset. Customers who escalate their complaints are highly likely to cancel. This is a leading indicator — escalations happen *before* churn, making them actionable.

**Recommendation:**
1. Create a **churn prevention trigger**: when a complaint is escalated, automatically flag the customer for priority retention intervention (discount offer, senior support rep, executive callback).
2. Set a KPI target to resolve escalations within 24 hours.
3. Track escalation rate monthly — it is a leading indicator of next month's churn rate.

---

### 5.7 Churn Risk Distribution

| Risk Level | Score Range | Customers |
|------------|------------|-----------|
| Low | < 50 | Majority |
| Medium | 50–69 | Minority |
| High | ≥ 70 | Small group |

**Key Insight:** High-risk customers (churn_score ≥ 70) are the immediate intervention priority. Cross-referencing with escalation_flag = 1 identifies the highest-risk cohort.

---

### 5.8 CLTV vs Churn

Higher CLTV customers tend to have lower churn scores. Premium plan customers combine high CLTV with low churn — they are the most valuable and most loyal cohort and should receive VIP treatment (dedicated support, early feature access).

---

## 6. Revenue Impact Quantification

| Scenario | Monthly Revenue Impact |
|----------|----------------------|
| Current churn (6 customers) | −₹73.94/month |
| If churn reduced to 15% (industry avg) | Save ~₹37/month |
| If referral churn fixed (save 4 customers) | Recover ~₹52/month |
| If Basic plan churn halved | Save ~₹20/month |

**Lifetime value at risk:** With avg tenure of 1,580 days (~4.3 years), each churned customer represents approximately `monthly_charges × 52 months` of lost future revenue.

---

## 7. Recommendations Summary

| Priority | Recommendation | Expected Impact |
|----------|---------------|----------------|
| 🔴 HIGH | Escalation → auto-flag for retention team | Reduce churn by 15–20% |
| 🔴 HIGH | Audit and reform referral programme | Reduce referral churn from 83% |
| 🟡 MED | Upsell/upgrade Basic customers at 90 days | Reduce Basic churn from 60% |
| 🟡 MED | Annual contract incentive for monthly customers | Increase contract stickiness |
| 🟢 LOW | Regional investigation: Karnataka, Meghalaya | Reduce geographic churn |
| 🟢 LOW | CSAT score tracking with <30 alert | Early complaint detection |

---

## 8. Dashboard & Monitoring

The interactive Streamlit dashboard (`files/app.py`) enables ongoing monitoring:

- **Real-time filtering** by plan, contract, source, gender, state, and age
- **KPI strip** shows all 10 metrics updating reactively
- **Segment analysis** identifies which cohorts need attention
- **SQL playground** allows ad-hoc queries without code changes
- **CSV export** for sharing filtered data with stakeholders

**Suggested review cadence:**
- Weekly: Churn rate, new cancellations, escalation rate
- Monthly: Segment analysis, CLTV trends, risk distribution
- Quarterly: Cohort comparison, referral programme ROI

---

## 9. Limitations & Next Steps

### Current Limitations
- Small dataset (21 customers) — findings are directional, not statistically significant
- No time-series data to identify trends over time
- No cohort analysis (customers acquired at different times)
- No A/B test data to validate recommendations

### Next Steps
1. **Scale the dataset** — connect to production CRM/billing database
2. **Build a predictive model** — logistic regression or XGBoost on churn_score features
3. **Automate pipeline** — schedule daily refresh with Airflow or cron
4. **Add cohort analysis** — month-of-acquisition vs churn rate
5. **Integrate with CRM** — push high-risk flags directly into sales/support tools
6. **Email alerts** — notify retention team when escalation_flag = 1

---

## 10. Technical Appendix

### Tools Used
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Core language |
| Pandas | 3.1 | Data manipulation |
| NumPy | 2.5 | Numerical operations |
| Plotly | 7.1 | Interactive charts |
| Streamlit | 1.67 | Dashboard framework |
| SQLite3 | stdlib | Database connectivity |
| Jupyter | - | Exploratory analysis |

### Notebook Sections
| Section | Content |
|---------|---------|
| §1 Import | SQLite connection, table extraction, schema inspection |
| §2 Cleaning | Rename, drop, dtype cast, gender standardise, country fill, dedup |
| §3 Feature Eng. | churn_flag, tenure, age, escalation, churn_risk, 10 KPIs |
| §4 Visualisation | Matplotlib/Seaborn charts matching dashboard charts |

---

*Case study prepared as part of a data analytics portfolio project.*
