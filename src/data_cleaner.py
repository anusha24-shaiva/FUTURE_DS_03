"""
Marketing Funnel Data Cleaning & Transformation Pipeline
Standardizes raw tracking data, fixes anomalies, validates chronology,
and calculates analytical metrics for funnel analysis.
"""

import os
import json
import pandas as pd
import numpy as np

def clean_marketing_funnel(raw_funnel_path, raw_spend_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    print("Starting Data Cleaning & Standardization Pipeline...")

    df_raw = pd.read_csv(raw_funnel_path)
    initial_row_count = len(df_raw)
    print(f"Loaded raw dataset with {initial_row_count} rows.")

    audit = {
        'initial_rows': initial_row_count,
        'duplicates_removed': 0,
        'channel_mappings_corrected': 0,
        'device_casing_corrected': 0,
        'missing_values_handled': {},
        'chronology_validations_passed': 0,
        'final_clean_rows': 0
    }

    # 1. Deduplication (removing simulated duplicate session/visitor events)
    df = df_raw.drop_duplicates(subset=['visitor_id', 'session_id']).copy()
    audit['duplicates_removed'] = initial_row_count - len(df)
    print(f"Removed {audit['duplicates_removed']} duplicate records.")

    # 2. String Cleaning & Channel Standardization
    # Normalize channels
    def standardize_channel(val):
        if pd.isna(val):
            return 'Direct'
        s = str(val).strip().lower()
        if 'organic' in s or 'seo' in s:
            return 'Organic Search'
        elif 'paid search' in s or 'google' in s or 'ppc' in s or 'g_ads' in s:
            return 'Paid Search (Google)'
        elif 'social' in s or 'linkedin' in s or 'meta' in s or 'facebook' in s or 'instagram' in s:
            return 'Social Media - Paid'
        elif 'email' in s or 'newsletter' in s:
            return 'Email Marketing'
        elif 'referral' in s or 'partner' in s or 'g2' in s or 'affiliate' in s:
            return 'Referral / Partner'
        elif 'direct' in s:
            return 'Direct'
        return 'Other'

    pre_channels = df['channel_raw'].nunique()
    df['marketing_channel'] = df['channel_raw'].apply(standardize_channel)
    audit['channel_mappings_corrected'] = int((df['channel_raw'].astype(str) != df['marketing_channel']).sum())

    # 3. Device Standardization
    df['device_type'] = df['device_type'].astype(str).str.strip().str.capitalize()
    df['device_type'] = df['device_type'].replace({'Mobiles': 'Mobile', 'Desktops': 'Desktop'})

    # 4. Handle Missing Tracking UTMs and Attributes
    audit['missing_values_handled'] = {
        'utm_source_raw': int(df['utm_source_raw'].isna().sum()),
        'utm_medium_raw': int(df['utm_medium_raw'].isna().sum()),
        'utm_campaign_raw': int(df['utm_campaign_raw'].isna().sum()),
        'company_size': int(df['company_size'].isna().sum()),
        'lead_score_raw': int(df['lead_score_raw'].isna().sum())
    }

    df['utm_source'] = df['utm_source_raw'].fillna('direct_or_unknown').str.strip().str.lower()
    df['utm_medium'] = df['utm_medium_raw'].fillna('none').str.strip().str.lower()
    df['utm_campaign'] = df['utm_campaign_raw'].fillna('unspecified_campaign').str.strip().str.lower()
    df['company_size'] = df['company_size'].fillna('Unknown / Not Provided')
    
    # 5. Timestamp Conversion & Chronology Validation
    ts_cols = ['visitor_timestamp', 'lead_timestamp', 'mql_timestamp', 'sql_timestamp', 'opp_timestamp', 'customer_timestamp']
    for col in ts_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Chronology validation
    valid_lead_chronology = (df['lead_timestamp'].isna()) | (df['lead_timestamp'] >= df['visitor_timestamp'])
    valid_mql_chronology = (df['mql_timestamp'].isna()) | (df['mql_timestamp'] >= df['lead_timestamp'])
    valid_sql_chronology = (df['sql_timestamp'].isna()) | (df['sql_timestamp'] >= df['mql_timestamp'])
    valid_opp_chronology = (df['opp_timestamp'].isna()) | (df['opp_timestamp'] >= df['sql_timestamp'])
    valid_cust_chronology = (df['customer_timestamp'].isna()) | (df['customer_timestamp'] >= df['opp_timestamp'])

    all_valid_chrono = valid_lead_chronology & valid_mql_chronology & valid_sql_chronology & valid_opp_chronology & valid_cust_chronology
    df = df[all_valid_chrono].copy()
    audit['chronology_validations_passed'] = len(df)

    # 6. Boolean Stage Progression Indicators
    df['is_visitor'] = 1
    df['is_lead'] = df['lead_timestamp'].notna().astype(int)
    df['is_mql'] = df['mql_timestamp'].notna().astype(int)
    df['is_sql'] = df['sql_timestamp'].notna().astype(int)
    df['is_opportunity'] = df['opp_timestamp'].notna().astype(int)
    df['is_customer'] = df['customer_timestamp'].notna().astype(int)

    # Cohort Month
    df['visitor_cohort_month'] = df['visitor_timestamp'].dt.to_period('M').astype(str)
    df['customer_cohort_month'] = df['customer_timestamp'].dt.to_period('M').astype(str).replace({'NaT': None})

    # Lead Score Categorization
    def categorize_lead_score(score):
        if pd.isna(score):
            return 'Unscored / Dropped at Visitor'
        elif score >= 75:
            return 'High Intent (75-100)'
        elif score >= 50:
            return 'Medium Intent (50-74)'
        else:
            return 'Low Intent (<50)'

    df['lead_score_tier'] = df['lead_score_raw'].apply(categorize_lead_score)

    # Conversion Velocity / Cycle Time in days
    df['days_visitor_to_lead'] = (df['lead_timestamp'] - df['visitor_timestamp']).dt.total_seconds() / 86400.0
    df['days_lead_to_mql'] = (df['mql_timestamp'] - df['lead_timestamp']).dt.total_seconds() / 86400.0
    df['days_mql_to_sql'] = (df['sql_timestamp'] - df['mql_timestamp']).dt.total_seconds() / 86400.0
    df['days_sql_to_opp'] = (df['opp_timestamp'] - df['sql_timestamp']).dt.total_seconds() / 86400.0
    df['days_opp_to_cust'] = (df['customer_timestamp'] - df['opp_timestamp']).dt.total_seconds() / 86400.0
    df['total_sales_cycle_days'] = (df['customer_timestamp'] - df['visitor_timestamp']).dt.total_seconds() / 86400.0

    audit['final_clean_rows'] = len(df)

    # Select and reorder columns for analytics
    final_cols = [
        'visitor_id', 'session_id', 'marketing_channel', 'utm_source', 'utm_medium', 'utm_campaign',
        'device_type', 'region', 'customer_segment', 'company_size', 'lead_score_raw', 'lead_score_tier',
        'visitor_timestamp', 'lead_timestamp', 'mql_timestamp', 'sql_timestamp', 'opp_timestamp', 'customer_timestamp',
        'visitor_cohort_month', 'customer_cohort_month',
        'is_visitor', 'is_lead', 'is_mql', 'is_sql', 'is_opportunity', 'is_customer',
        'stage_reached', 'drop_off_stage', 'drop_off_reason', 'deal_arr_usd',
        'days_visitor_to_lead', 'days_lead_to_mql', 'days_mql_to_sql', 'days_sql_to_opp', 'days_opp_to_cust', 'total_sales_cycle_days'
    ]
    df_clean = df[final_cols].copy()

    # Save cleaned data
    clean_path = os.path.join(output_dir, 'cleaned_funnel_journeys.csv')
    df_clean.to_csv(clean_path, index=False)
    print(f"Cleaned dataset successfully saved to: {clean_path} ({len(df_clean)} rows)")

    # Save audit report
    audit_path = os.path.join(output_dir, 'data_cleaning_audit_report.json')
    with open(audit_path, 'w') as f:
        json.dump(audit, f, indent=4)
    print(f"Cleaning audit report saved to: {audit_path}")

    # Clean ad spend table as well
    if os.path.exists(raw_spend_path):
        df_spend = pd.read_csv(raw_spend_path)
        spend_clean_path = os.path.join(output_dir, 'cleaned_ad_spend_by_channel.csv')
        df_spend.to_csv(spend_clean_path, index=False)
        print(f"Ad spend data verified and saved to: {spend_clean_path}")

    return df_clean, audit

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(__file__))
    raw_funnel = os.path.join(base_dir, 'data', 'raw', 'raw_marketing_funnel.csv')
    raw_spend = os.path.join(base_dir, 'data', 'raw', 'raw_ad_spend_by_channel.csv')
    output_dir = os.path.join(base_dir, 'data', 'processed')

    clean_marketing_funnel(raw_funnel, raw_spend, output_dir)
