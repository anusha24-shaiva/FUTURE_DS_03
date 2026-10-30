import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.funnel_analyzer import FunnelAnalyzer

def export_dashboard_payload(cleaned_data_path, cleaned_spend_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    analyzer = FunnelAnalyzer(cleaned_data_path, cleaned_spend_path)

    overall_funnel = analyzer.compute_overall_funnel().to_dict(orient='records')
    channel_perf = analyzer.compute_channel_performance().to_dict(orient='records')
    drop_reasons = analyzer.compute_drop_off_reasons().to_dict(orient='records')
    device_perf, segment_perf = analyzer.compute_device_segment_performance()
    velocity_metrics, channel_velocity = analyzer.compute_conversion_velocity()
    monthly_trends = analyzer.compute_monthly_cohort_trends().to_dict(orient='records')
    scenarios = analyzer.simulate_conversion_uplift().to_dict(orient='records')

    # Executive KPIs
    total_visitors = int(analyzer.df['is_visitor'].sum())
    total_leads = int(analyzer.df['is_lead'].sum())
    total_mqls = int(analyzer.df['is_mql'].sum())
    total_sqls = int(analyzer.df['is_sql'].sum())
    total_opps = int(analyzer.df['is_opportunity'].sum())
    total_customers = int(analyzer.df['is_customer'].sum())
    total_arr = float(analyzer.df['deal_arr_usd'].sum())
    avg_deal = float(analyzer.df[analyzer.df['is_customer'] == 1]['deal_arr_usd'].mean()) if total_customers > 0 else 0
    total_spend = float(analyzer.df_spend['monthly_budget_usd'].sum()) if analyzer.df_spend is not None else 0
    blended_cac = round(total_spend / total_customers, 2) if total_customers > 0 else 0
    blended_roas = round(total_arr / total_spend, 2) if total_spend > 0 else 0

    payload = {
        'kpis': {
            'total_visitors': total_visitors,
            'total_leads': total_leads,
            'traffic_to_lead_pct': round(total_leads / total_visitors * 100, 2),
            'total_mqls': total_mqls,
            'total_sqls': total_sqls,
            'total_opps': total_opps,
            'total_customers': total_customers,
            'overall_conversion_pct': round(total_customers / total_visitors * 100, 2),
            'lead_to_customer_pct': round(total_customers / total_leads * 100, 2),
            'total_arr_usd': round(total_arr, 2),
            'avg_deal_arr_usd': round(avg_deal, 2),
            'total_marketing_spend_usd': round(total_spend, 2),
            'blended_cac_usd': blended_cac,
            'blended_roas': blended_roas
        },
        'funnel_stages': overall_funnel,
        'channel_performance': channel_perf,
        'drop_off_reasons': drop_reasons,
        'device_performance': device_perf.to_dict(orient='records'),
        'segment_performance': segment_perf.to_dict(orient='records'),
        'velocity': {
            'metrics': velocity_metrics,
            'channel_velocity': channel_velocity.to_dict(orient='records')
        },
        'monthly_trends': monthly_trends,
        'revenue_scenarios': scenarios
    }

    # Save as JSON
    json_path = os.path.join(output_dir, 'funnel_dashboard_data.json')
    with open(json_path, 'w') as f:
        json.dump(payload, f, indent=2)

    # Save as JS file for direct local browser execution without CORS restrictions
    js_path = os.path.join(output_dir, 'funnel_dashboard_data.js')
    with open(js_path, 'w') as f:
        f.write("window.FUNNEL_DASHBOARD_DATA = " + json.dumps(payload, indent=2) + ";\n")

    print(f"Exported dashboard data to {json_path} and {js_path}")
    return payload

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(__file__))
    clean_data = os.path.join(base_dir, 'data', 'processed', 'cleaned_funnel_journeys.csv')
    clean_spend = os.path.join(base_dir, 'data', 'processed', 'cleaned_ad_spend_by_channel.csv')
    dash_data_dir = os.path.join(base_dir, 'dashboard', 'data')

    export_dashboard_payload(clean_data, clean_spend, dash_data_dir)
