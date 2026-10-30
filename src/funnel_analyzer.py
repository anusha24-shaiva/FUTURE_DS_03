"""
Marketing Funnel & Conversion Performance Analyzer
Performs end-to-end mathematical and statistical analysis of marketing funnels,
including stage drop-offs, channel attribution, unit economics (CAC, LTV, ROAS),
conversion velocity, and revenue simulation.
"""

import os
import json
import pandas as pd
import numpy as np

class FunnelAnalyzer:
    def __init__(self, cleaned_data_path, cleaned_spend_path=None):
        self.df = pd.read_csv(cleaned_data_path)
        self.df_spend = pd.read_csv(cleaned_spend_path) if cleaned_spend_path and os.path.exists(cleaned_spend_path) else None
        self.stages = ['Visitor', 'Lead', 'MQL', 'SQL', 'Opportunity', 'Customer']
        self.stage_cols = ['is_visitor', 'is_lead', 'is_mql', 'is_sql', 'is_opportunity', 'is_customer']

    def compute_overall_funnel(self):
        """Calculates global stage counts, step conversion rates, cumulative conversions, and drop-offs."""
        counts = [int(self.df[col].sum()) for col in self.stage_cols]
        total_visitors = counts[0]

        funnel_rows = []
        for i, stage in enumerate(self.stages):
            count = counts[i]
            prev_count = counts[i-1] if i > 0 else count
            step_conv = (count / prev_count * 100.0) if prev_count > 0 else 100.0
            cum_conv = (count / total_visitors * 100.0) if total_visitors > 0 else 0.0
            
            # Drop-off from current to next stage
            if i < len(self.stages) - 1:
                next_count = counts[i+1]
                drop_count = count - next_count
                drop_rate = (drop_count / count * 100.0) if count > 0 else 0.0
            else:
                drop_count = 0
                drop_rate = 0.0

            funnel_rows.append({
                'stage_order': i + 1,
                'stage_name': stage,
                'count': count,
                'step_conversion_rate_pct': round(step_conv, 2),
                'cumulative_conversion_rate_pct': round(cum_conv, 2),
                'drop_off_count': drop_count,
                'drop_off_rate_pct': round(drop_rate, 2)
            })

        funnel_summary_df = pd.DataFrame(funnel_rows)
        return funnel_summary_df

    def compute_channel_performance(self):
        """Analyzes conversion efficiency, deal sizes, ad spend, CAC, LTV, and ROAS per channel."""
        grouped = self.df.groupby('marketing_channel')
        
        channel_rows = []
        for ch, g in grouped:
            visitors = int(g['is_visitor'].sum())
            leads = int(g['is_lead'].sum())
            mqls = int(g['is_mql'].sum())
            sqls = int(g['is_sql'].sum())
            opps = int(g['is_opportunity'].sum())
            customers = int(g['is_customer'].sum())
            total_arr = float(g['deal_arr_usd'].sum())
            avg_deal_arr = float(g[g['is_customer'] == 1]['deal_arr_usd'].mean()) if customers > 0 else 0.0

            # Conversion Rates
            traffic_to_lead_pct = round((leads / visitors * 100.0), 2) if visitors > 0 else 0.0
            lead_to_mql_pct = round((mqls / leads * 100.0), 2) if leads > 0 else 0.0
            mql_to_sql_pct = round((sqls / mqls * 100.0), 2) if mqls > 0 else 0.0
            sql_to_opp_pct = round((opps / sqls * 100.0), 2) if sqls > 0 else 0.0
            opp_to_cust_pct = round((customers / opps * 100.0), 2) if opps > 0 else 0.0
            overall_conversion_pct = round((customers / visitors * 100.0), 2) if visitors > 0 else 0.0
            lead_to_customer_pct = round((customers / leads * 100.0), 2) if leads > 0 else 0.0

            # Ad spend metrics if available
            spend = 0.0
            if self.df_spend is not None:
                spend_match = self.df_spend[self.df_spend['channel'] == ch]['monthly_budget_usd'].sum()
                spend = float(spend_match)

            cpl = round((spend / leads), 2) if leads > 0 and spend > 0 else 0.0
            cac = round((spend / customers), 2) if customers > 0 and spend > 0 else 0.0
            roas = round((total_arr / spend), 2) if spend > 0 else None
            # SaaS 3-year LTV estimate (Assuming 80% gross margin and 3-year lifespan)
            ltv = round(avg_deal_arr * 0.80 * 3.0, 2)
            ltv_cac_ratio = round((ltv / cac), 2) if cac > 0 else None

            channel_rows.append({
                'marketing_channel': ch,
                'visitors': visitors,
                'leads': leads,
                'mqls': mqls,
                'sqls': sqls,
                'opportunities': opps,
                'customers': customers,
                'traffic_to_lead_pct': traffic_to_lead_pct,
                'lead_to_mql_pct': lead_to_mql_pct,
                'mql_to_sql_pct': mql_to_sql_pct,
                'sql_to_opp_pct': sql_to_opp_pct,
                'opp_to_cust_pct': opp_to_cust_pct,
                'overall_conversion_pct': overall_conversion_pct,
                'lead_to_customer_pct': lead_to_customer_pct,
                'total_spend_usd': round(spend, 2),
                'cost_per_lead_cpl': cpl,
                'cpl': cpl,
                'customer_acquisition_cost_cac': cac,
                'cac': cac,
                'avg_deal_arr_usd': round(avg_deal_arr, 2),
                'total_arr_usd': round(total_arr, 2),
                'ltv_estimate_usd': ltv,
                'ltv_to_cac_ratio': ltv_cac_ratio,
                'roas': roas
            })

        df_channel = pd.DataFrame(channel_rows).sort_values(by='customers', ascending=False)
        return df_channel

    def compute_drop_off_reasons(self):
        """Extracts top reasons for user drop-offs at each funnel stage."""
        non_converted = self.df[self.df['drop_off_stage'] != 'None (Converted Customer)']
        reasons = non_converted.groupby(['drop_off_stage', 'drop_off_reason']).size().reset_index(name='count')
        
        # Calculate percentage within each drop-off stage
        stage_totals = reasons.groupby('drop_off_stage')['count'].transform('sum')
        reasons['pct_within_stage'] = round(reasons['count'] / stage_totals * 100.0, 2)
        return reasons.sort_values(by=['drop_off_stage', 'count'], ascending=[True, False])

    def compute_device_segment_performance(self):
        """Analyzes conversion performance segmented by Device and Customer Segment."""
        device_perf = self.df.groupby('device_type').agg(
            visitors=('is_visitor', 'sum'),
            leads=('is_lead', 'sum'),
            customers=('is_customer', 'sum'),
            total_arr=('deal_arr_usd', 'sum')
        ).reset_index()
        device_perf['traffic_to_lead_pct'] = round(device_perf['leads'] / device_perf['visitors'] * 100.0, 2)
        device_perf['overall_conv_pct'] = round(device_perf['customers'] / device_perf['visitors'] * 100.0, 2)

        segment_perf = self.df.groupby('customer_segment').agg(
            visitors=('is_visitor', 'sum'),
            leads=('is_lead', 'sum'),
            sqls=('is_sql', 'sum'),
            customers=('is_customer', 'sum'),
            total_arr=('deal_arr_usd', 'sum'),
            avg_deal_arr=('deal_arr_usd', lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0)
        ).reset_index()
        segment_perf['lead_to_customer_pct'] = round(segment_perf['customers'] / segment_perf['leads'] * 100.0, 2)
        segment_perf['overall_conv_pct'] = round(segment_perf['customers'] / segment_perf['visitors'] * 100.0, 2)
        segment_perf['avg_deal_arr'] = round(segment_perf['avg_deal_arr'], 2)

        return device_perf, segment_perf

    def compute_conversion_velocity(self):
        """Calculates stage transition durations (cycle time) in days."""
        velocity_metrics = {
            'visitor_to_lead_median_hours': round(float(self.df[self.df['is_lead'] == 1]['days_visitor_to_lead'].median() * 24.0), 1),
            'lead_to_mql_median_hours': round(float(self.df[self.df['is_mql'] == 1]['days_lead_to_mql'].median() * 24.0), 1),
            'mql_to_sql_median_days': round(float(self.df[self.df['is_sql'] == 1]['days_mql_to_sql'].median()), 1),
            'sql_to_opp_median_days': round(float(self.df[self.df['is_opportunity'] == 1]['days_sql_to_opp'].median()), 1),
            'opp_to_cust_median_days': round(float(self.df[self.df['is_customer'] == 1]['days_opp_to_cust'].median()), 1),
            'total_sales_cycle_median_days': round(float(self.df[self.df['is_customer'] == 1]['total_sales_cycle_days'].median()), 1),
            'total_sales_cycle_mean_days': round(float(self.df[self.df['is_customer'] == 1]['total_sales_cycle_days'].mean()), 1)
        }

        # Velocity by channel for won customers
        cust_df = self.df[self.df['is_customer'] == 1]
        channel_velocity = cust_df.groupby('marketing_channel')['total_sales_cycle_days'].agg(
            median_days='median',
            mean_days='mean',
            count='count'
        ).reset_index()
        channel_velocity['median_days'] = round(channel_velocity['median_days'], 1)
        channel_velocity['mean_days'] = round(channel_velocity['mean_days'], 1)

        return velocity_metrics, channel_velocity

    def compute_monthly_cohort_trends(self):
        """Monthly trends of top-of-funnel through bottom-of-funnel metrics."""
        cohorts = self.df.groupby('visitor_cohort_month').agg(
            visitors=('is_visitor', 'sum'),
            leads=('is_lead', 'sum'),
            mqls=('is_mql', 'sum'),
            sqls=('is_sql', 'sum'),
            opps=('is_opportunity', 'sum'),
            customers=('is_customer', 'sum'),
            total_arr=('deal_arr_usd', 'sum')
        ).reset_index()

        cohorts['traffic_to_lead_pct'] = round(cohorts['leads'] / cohorts['visitors'] * 100.0, 2)
        cohorts['lead_to_customer_pct'] = round(cohorts['customers'] / cohorts['leads'] * 100.0, 2)
        cohorts['overall_conv_pct'] = round(cohorts['customers'] / cohorts['visitors'] * 100.0, 2)
        return cohorts

    def simulate_conversion_uplift(self):
        """
        Calculates the revenue sensitivity model:
        What happens if we optimize specific funnel stages by +5%, +10%, +15%?
        """
        counts = [int(self.df[col].sum()) for col in self.stage_cols]
        v, l, m, s, o, c = counts
        avg_arr = float(self.df[self.df['is_customer'] == 1]['deal_arr_usd'].mean())

        # Baseline step conversion rates
        conv_v_l = l / v
        conv_l_m = m / l
        conv_m_s = s / m
        conv_s_o = o / s
        conv_o_c = c / o

        scenarios = []

        # Scenario 1: +10% relative improvement in Visitor -> Lead (Landing Page Optimization)
        l_sim = v * (conv_v_l * 1.10)
        m_sim = l_sim * conv_l_m
        s_sim = m_sim * conv_m_s
        o_sim = s_sim * conv_s_o
        c_sim1 = int(o_sim * conv_o_c)
        rev_uplift1 = (c_sim1 - c) * avg_arr
        scenarios.append({
            'initiative': 'Landing Page & CTA UX Optimization (+10% Visitor->Lead)',
            'targeted_stage': 'Visitor -> Lead',
            'baseline_customers': c,
            'simulated_customers': c_sim1,
            'net_new_customers': c_sim1 - c,
            'additional_arr_usd': round(rev_uplift1, 2)
        })

        # Scenario 2: +15% relative improvement in Lead -> MQL (Faster BDR response, automated lead qualification)
        m_sim2 = l * (conv_l_m * 1.15)
        s_sim2 = m_sim2 * conv_m_s
        o_sim2 = s_sim2 * conv_s_o
        c_sim2 = int(o_sim2 * conv_o_c)
        rev_uplift2 = (c_sim2 - c) * avg_arr
        scenarios.append({
            'initiative': 'Lead Scoring & Automated Nurturing (+15% Lead->MQL)',
            'targeted_stage': 'Lead -> MQL',
            'baseline_customers': c,
            'simulated_customers': c_sim2,
            'net_new_customers': c_sim2 - c,
            'additional_arr_usd': round(rev_uplift2, 2)
        })

        # Scenario 3: +10% relative improvement in Opportunity -> Customer (Sales enablement, demo coaching, pricing flexibility)
        c_sim3 = int(o * (conv_o_c * 1.10))
        rev_uplift3 = (c_sim3 - c) * avg_arr
        scenarios.append({
            'initiative': 'Sales Enablement & Deal Acceleration (+10% Opp->Customer)',
            'targeted_stage': 'Opportunity -> Customer',
            'baseline_customers': c,
            'simulated_customers': c_sim3,
            'net_new_customers': c_sim3 - c,
            'additional_arr_usd': round(rev_uplift3, 2)
        })

        # Scenario 4: Full-Funnel Compounding Optimization (+5% uplift across each stage)
        v_c = v
        l_comp = v_c * (conv_v_l * 1.05)
        m_comp = l_comp * (conv_l_m * 1.05)
        s_comp = m_comp * (conv_m_s * 1.05)
        o_comp = s_comp * (conv_s_o * 1.05)
        c_comp = int(o_comp * (conv_o_c * 1.05))
        rev_comp = (c_comp - c) * avg_arr
        scenarios.append({
            'initiative': 'Full-Funnel Compounding Growth (+5% uplift at every stage)',
            'targeted_stage': 'All Stages (1.05^5 = +27.6% compounding)',
            'baseline_customers': c,
            'simulated_customers': c_comp,
            'net_new_customers': c_comp - c,
            'additional_arr_usd': round(rev_comp, 2)
        })

        return pd.DataFrame(scenarios)

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(__file__))
    clean_data = os.path.join(base_dir, 'data', 'processed', 'cleaned_funnel_journeys.csv')
    clean_spend = os.path.join(base_dir, 'data', 'processed', 'cleaned_ad_spend_by_channel.csv')
    
    if os.path.exists(clean_data):
        analyzer = FunnelAnalyzer(clean_data, clean_spend)
        funnel_summary = analyzer.compute_overall_funnel()
        print("--- OVERALL FUNNEL STAGES ---")
        print(funnel_summary.to_string(index=False))
        
        channel_perf = analyzer.compute_channel_performance()
        print("\n--- CHANNEL PERFORMANCE & ROI ---")
        print(channel_perf[['marketing_channel', 'visitors', 'leads', 'customers', 'overall_conversion_pct', 'cac', 'total_arr_usd', 'roas']].to_string(index=False))
