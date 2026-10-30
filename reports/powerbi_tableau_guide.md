# Power BI & Tableau Implementation Guide
## Marketing Funnel & Conversion Performance Analytics
**Task 3: Data Science & Analytics (2026)** • Future Interns

This guide provides step-by-step instructions, Star-Schema data models, DAX measures (Power BI), and Calculated Fields (Tableau) to recreate the executive funnel dashboard in enterprise BI tools.

---

## 1. Data Model Architecture (Star Schema)

The processed data exported in `data/processed/` is structured for seamless ingestion into Power BI or Tableau.

```
       ┌───────────────────────────┐
       │     dim_channel           │
       ├───────────────────────────┤
       │ channel_id (PK)           │
       │ marketing_channel         │
       │ cost_model                │
       └─────────────┬─────────────┘
                     │ 1
                     │
                     │ *
       ┌─────────────┴─────────────┐         ┌───────────────────────────┐
       │   fact_funnel_journeys    │ *     1 │        dim_date           │
       ├───────────────────────────┼─────────┤───────────────────────────┤
       │ visitor_id (PK)           │         │ date_id (PK)              │
       │ session_id                │         │ date                      │
       │ marketing_channel (FK)    │         │ month_year (YYYY-MM)      │
       │ visitor_timestamp (FK)    │         │ quarter                   │
       │ customer_timestamp        │         └───────────────────────────┘
       │ is_visitor (1)            │
       │ is_lead (0/1)             │
       │ is_mql (0/1)              │
       │ is_sql (0/1)              │
       │ is_opportunity (0/1)      │
       │ is_customer (0/1)         │
       │ deal_arr_usd              │
       └─────────────┬─────────────┘
                     │ *
                     │
                     │ 1
       ┌─────────────┴─────────────┐
       │   fact_ad_spend           │
       ├───────────────────────────┤
       │ month (FK)                │
       │ channel (FK)              │
       │ monthly_budget_usd        │
       └───────────────────────────┘
```

---

## 2. Power BI Setup & DAX Measures

### Step-by-Step Power BI Setup:
1. Open **Power BI Desktop**.
2. Click **Get Data** → **Text/CSV** → Select `data/processed/cleaned_funnel_journeys.csv`.
3. Click **Get Data** → **Text/CSV** → Select `data/processed/cleaned_ad_spend_by_channel.csv`.
4. Go to **Model View** and establish relationships:
   - `cleaned_funnel_journeys[marketing_channel]` $\longleftrightarrow$ `cleaned_ad_spend_by_channel[channel]` (Many-to-Many or connect via bridge table).

### Essential DAX Measures:

#### 1. Funnel Stage Counts
```dax
Total Visitors = COUNTROWS('cleaned_funnel_journeys')

Total Leads = CALCULATE(COUNTROWS('cleaned_funnel_journeys'), 'cleaned_funnel_journeys'[is_lead] = 1)

Total MQLs = CALCULATE(COUNTROWS('cleaned_funnel_journeys'), 'cleaned_funnel_journeys'[is_mql] = 1)

Total SQLs = CALCULATE(COUNTROWS('cleaned_funnel_journeys'), 'cleaned_funnel_journeys'[is_sql] = 1)

Total Opportunities = CALCULATE(COUNTROWS('cleaned_funnel_journeys'), 'cleaned_funnel_journeys'[is_opportunity] = 1)

Total Customers Won = CALCULATE(COUNTROWS('cleaned_funnel_journeys'), 'cleaned_funnel_journeys'[is_customer] = 1)
```

#### 2. Conversion Rates (%)
```dax
Traffic-to-Lead Rate = 
DIVIDE([Total Leads], [Total Visitors], 0)

Lead-to-Customer Rate = 
DIVIDE([Total Customers Won], [Total Leads], 0)

Overall Conversion Rate = 
DIVIDE([Total Customers Won], [Total Visitors], 0)

MQL Qualification Rate = 
DIVIDE([Total MQLs], [Total Leads], 0)

Opportunity Win Rate = 
DIVIDE([Total Customers Won], [Total Opportunities], 0)
```

#### 3. Financial Metrics & Unit Economics
```dax
Total Closed ARR = 
SUM('cleaned_funnel_journeys'[deal_arr_usd])

Total Marketing Spend = 
SUM('cleaned_ad_spend_by_channel'[monthly_budget_usd])

Cost Per Lead (CPL) = 
DIVIDE([Total Marketing Spend], [Total Leads], 0)

Customer Acquisition Cost (CAC) = 
DIVIDE([Total Marketing Spend], [Total Customers Won], 0)

Average Deal Size = 
DIVIDE([Total Closed ARR], [Total Customers Won], 0)

Return on Ad Spend (ROAS) = 
DIVIDE([Total Closed ARR], [Total Marketing Spend], 0)

Customer LTV (3-Year 80% Margin) = 
[Average Deal Size] * 0.80 * 3.0

LTV to CAC Ratio = 
DIVIDE([Customer LTV (3-Year 80% Margin)], [Customer Acquisition Cost (CAC)], 0)
```

### Recommended Power BI Visualizations:
- **Funnel Visual / Ribbon Chart:** Map stages `Visitor` → `Lead` → `MQL` → `SQL` → `Opportunity` → `Customer`.
- **Matrix Visual:** Rows = `marketing_channel`, Values = `[Total Leads]`, `[Total Customers Won]`, `[Overall Conversion Rate]`, `[CAC]`, `[ROAS]`.
- **Scatter Plot (4 Quadrants):** X-Axis = `[CAC]`, Y-Axis = `[Customer LTV]`, Size = `[Total Closed ARR]`, Play Axis = `[visitor_cohort_month]`.

---

## 3. Tableau Setup & Calculated Fields

### Step-by-Step Tableau Setup:
1. Open **Tableau Desktop**.
2. Connect to **Text File** → Select `cleaned_funnel_journeys.csv`.
3. Add a Relationship to `cleaned_ad_spend_by_channel.csv` matching on `marketing_channel = channel`.

### Tableau Calculated Fields:

#### 1. Conversion Metrics
```tableau
// [Traffic to Lead %]
SUM([is_lead]) / SUM([is_visitor])

// [Lead to Customer %]
SUM([is_customer]) / SUM([is_lead])

// [Overall Conversion %]
SUM([is_customer]) / SUM([is_visitor])

// [Step Conv: Opp to Customer]
SUM([is_customer]) / SUM([is_opportunity])
```

#### 2. Financial Metrics
```tableau
// [Total Closed ARR]
SUM([deal_arr_usd])

// [Customer Acquisition Cost (CAC)]
SUM([monthly_budget_usd]) / SUM([is_customer])

// [Return on Ad Spend (ROAS)]
[Total Closed ARR] / SUM([monthly_budget_usd])

// [Estimated LTV]
([Total Closed ARR] / SUM([is_customer])) * 0.80 * 3
```

### Recommended Tableau Dashboard Layout:
1. **Funnel Progression Sheet:** Horizontal Bar chart with Stage Measure Names and dual-axis conversion labels.
2. **Channel Efficiency Treemap:** Size = `[Total Closed ARR]`, Color = `[ROAS]`.
3. **Drop-off Waterfall Sheet:** Stage transitions with negative drop-off bars.
4. **Cohort Analysis Sheet:** Columns = `[visitor_cohort_month]`, Rows = `[marketing_channel]`, Color = `[Overall Conversion %]`.
