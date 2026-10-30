"""
Marketing Funnel Data Generator
Generates realistic multi-channel marketing and sales funnel data with
intentional real-world data quality anomalies for cleaning and analysis.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_funnel_data(num_visitors=50000, random_seed=42):
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    start_date = datetime(2025, 1, 1, 0, 0, 0)
    end_date = datetime(2025, 12, 31, 23, 59, 59)
    total_seconds = int((end_date - start_date).total_seconds())

    # Marketing Channels and raw UTM variations (simulating real-world messy tracking)
    channel_configs = {
        'Organic Search': {
            'weight': 0.28,
            'sources': ['google', 'Google', 'google_organic', 'bing', 'yahoo', None],
            'mediums': ['organic', 'search', 'seo', None],
            'campaigns': ['brand_seo', 'non_brand_blog', 'seo_guides', None],
            'lead_conv_rate': 0.095,
            'mql_rate': 0.48,
            'sql_rate': 0.52,
            'opp_rate': 0.65,
            'win_rate': 0.38,
            'avg_deal': 14500
        },
        'Paid Search (Google)': {
            'weight': 0.22,
            'sources': ['google_ads', 'GOOGLE_PPC', 'google-cpc', 'Google_Search', 'g_ads'],
            'mediums': ['cpc', 'ppc', 'paid_search', 'paid'],
            'campaigns': ['high_intent_saas', 'competitor_terms', 'product_keywords', 'retargeting_search'],
            'lead_conv_rate': 0.135,
            'mql_rate': 0.54,
            'sql_rate': 0.58,
            'opp_rate': 0.70,
            'win_rate': 0.34,
            'avg_deal': 18500
        },
        'Social Media - Paid': {
            'weight': 0.16,
            'sources': ['linkedin_ads', 'LI_sponsor', 'meta_ads', 'facebook_cpc', 'instagram'],
            'mediums': ['paid_social', 'cpc', 'social_ad', 'sponsored'],
            'campaigns': ['b2b_executive_ebook', 'case_study_carousel', 'saas_demo_promo', 'event_webinar'],
            'lead_conv_rate': 0.105,
            'mql_rate': 0.42,
            'sql_rate': 0.40,
            'opp_rate': 0.55,
            'win_rate': 0.26,
            'avg_deal': 22000
        },
        'Email Marketing': {
            'weight': 0.12,
            'sources': ['newsletter', 'hubspot_email', 'product_update', 'email_nurture', 'drip_campaign'],
            'mediums': ['email', 'Email', 'newsletter_link', 'marketing_mail'],
            'campaigns': ['q1_newsletter', 'product_v2_launch', 'webinar_invite', 'reactivation_q3', 'black_friday'],
            'lead_conv_rate': 0.180,
            'mql_rate': 0.68,
            'sql_rate': 0.64,
            'opp_rate': 0.74,
            'win_rate': 0.45,
            'avg_deal': 16000
        },
        'Referral / Partner': {
            'weight': 0.08,
            'sources': ['partner_portal', 'g2_crowd', 'capterra', 'affiliate_link', 'tech_directory'],
            'mediums': ['referral', 'partner', 'review_site', 'affiliate'],
            'campaigns': ['g2_badge_review', 'partner_cobrand', 'capterra_ppc', 'affiliate_tier1'],
            'lead_conv_rate': 0.165,
            'mql_rate': 0.62,
            'sql_rate': 0.72,
            'opp_rate': 0.80,
            'win_rate': 0.48,
            'avg_deal': 24000
        },
        'Direct': {
            'weight': 0.14,
            'sources': ['(direct)', 'direct', None],
            'mediums': ['(none)', 'none', None],
            'campaigns': ['(not set)', None],
            'lead_conv_rate': 0.065,
            'mql_rate': 0.44,
            'sql_rate': 0.48,
            'opp_rate': 0.60,
            'win_rate': 0.32,
            'avg_deal': 12000
        }
    }

    channels = list(channel_configs.keys())
    weights = [channel_configs[ch]['weight'] for ch in channels]
    assigned_channels = np.random.choice(channels, size=num_visitors, p=weights)

    devices = ['Desktop', 'Mobile', 'Tablet']
    device_weights = [0.62, 0.33, 0.05]
    
    regions = ['North America', 'EMEA', 'APAC', 'LATAM']
    region_weights = [0.48, 0.28, 0.18, 0.06]

    segments = ['Enterprise', 'Mid-Market', 'SMB', 'Startup']
    segment_weights = [0.18, 0.32, 0.35, 0.15]

    company_sizes = ['1-10', '11-50', '51-200', '201-1000', '1000+']
    company_size_weights = [0.20, 0.30, 0.25, 0.15, 0.10]

    drop_reasons_visitor = ['Bounced within 10s', 'Irrelevant landing page', 'Slow page load', 'No clear CTA']
    drop_reasons_lead = ['Form abandonment', 'Email validation failure', 'Unqualified intent', 'Competitor research']
    drop_reasons_mql = ['Low lead score', 'Non-business email', 'No decision-maker authority', 'Inactive company']
    drop_reasons_sql = ['Budget unavailable', 'No current project', 'Unresponsive to BDR calls', 'Chose internal solution']
    drop_reasons_opp = ['Price too high / Budget freeze', 'Competitor won on features', 'Security / Compliance blocker', 'Project postponed', 'Lack of executive buy-in']

    rows = []

    for i in range(num_visitors):
        visitor_id = f"VIS-{100000 + i}"
        ch_name = assigned_channels[i]
        cfg = channel_configs[ch_name]

        # Device, Region, Segment
        device = np.random.choice(devices, p=device_weights)
        region = np.random.choice(regions, p=region_weights)
        segment = np.random.choice(segments, p=segment_weights)
        company_size = np.random.choice(company_sizes, p=company_size_weights)

        # UTM parameters (incorporate messy real-world tracking)
        utm_source = random.choice(cfg['sources'])
        utm_medium = random.choice(cfg['mediums'])
        utm_campaign = random.choice(cfg['campaigns'])

        # Introduce occasional missing values in tracking
        if random.random() < 0.05:
            utm_medium = None
        if random.random() < 0.08:
            utm_campaign = None

        # Visitor Timestamp
        offset_sec = np.random.randint(0, total_seconds)
        # Add slight seasonal surge in Q3/Q4
        month_boost = np.random.choice([0, 1, 2], p=[0.6, 0.25, 0.15])
        ts_visitor = start_date + timedelta(seconds=offset_sec)
        
        # Adjust conversion rates slightly based on device & segment
        device_factor = 1.15 if device == 'Desktop' else (0.75 if device == 'Mobile' else 0.85)
        segment_factor = 1.25 if segment in ['Enterprise', 'Mid-Market'] else 0.90

        # Stage 1 -> Stage 2: Visitor -> Lead
        lead_prob = min(0.95, cfg['lead_conv_rate'] * device_factor)
        reached_lead = 1 if (np.random.random() < lead_prob) else 0

        ts_lead = None
        reached_mql = 0
        ts_mql = None
        reached_sql = 0
        ts_sql = None
        reached_opp = 0
        ts_opp = None
        reached_cust = 0
        ts_cust = None
        deal_arr = 0.0
        drop_stage = 'Visitor'
        drop_reason = None
        lead_score = None

        if reached_lead:
            # Lead converted within 0 to 48 hours of visit
            ts_lead = ts_visitor + timedelta(minutes=int(np.random.exponential(scale=60) + 2))
            lead_score = int(np.clip(np.random.normal(55, 18), 10, 99))
            if segment == 'Enterprise':
                lead_score = min(99, lead_score + 15)

            # Stage 2 -> Stage 3: Lead -> MQL
            mql_prob = min(0.95, cfg['mql_rate'] * (lead_score / 60.0))
            if np.random.random() < mql_prob:
                reached_mql = 1
                # MQL qualified within 4 to 96 hours
                ts_mql = ts_lead + timedelta(hours=int(np.random.gamma(shape=2, scale=12) + 2))

                # Stage 3 -> Stage 4: MQL -> SQL
                sql_prob = min(0.95, cfg['sql_rate'] * segment_factor)
                if np.random.random() < sql_prob:
                    reached_sql = 1
                    # SQL demo scheduled within 1 to 7 days
                    ts_sql = ts_mql + timedelta(days=float(np.random.gamma(shape=1.5, scale=2.5) + 0.5))

                    # Stage 4 -> Stage 5: SQL -> Opportunity
                    opp_prob = cfg['opp_rate']
                    if np.random.random() < opp_prob:
                        reached_opp = 1
                        # Opportunity pipeline created within 2 to 14 days
                        ts_opp = ts_sql + timedelta(days=float(np.random.gamma(shape=2, scale=3) + 1))

                        # Stage 5 -> Stage 6: Opportunity -> Customer (Closed-Won)
                        win_prob = cfg['win_rate']
                        if np.random.random() < win_prob:
                            reached_cust = 1
                            # Deal closed won in 7 to 45 days
                            ts_cust = ts_opp + timedelta(days=float(np.random.gamma(shape=3, scale=8) + 4))
                            
                            # ARR calculation based on segment and channel baseline
                            base_deal = cfg['avg_deal']
                            multiplier = {
                                'Enterprise': 3.2,
                                'Mid-Market': 1.6,
                                'SMB': 0.8,
                                'Startup': 0.5
                            }[segment]
                            noise = np.random.uniform(0.85, 1.3)
                            deal_arr = round(base_deal * multiplier * noise, 2)
                            drop_stage = 'None (Converted Customer)'
                            drop_reason = 'Successfully Closed Won'
                        else:
                            drop_stage = 'Opportunity'
                            drop_reason = np.random.choice(drop_reasons_opp)
                    else:
                        drop_stage = 'SQL'
                        drop_reason = np.random.choice(drop_reasons_sql)
                else:
                    drop_stage = 'MQL'
                    drop_reason = np.random.choice(drop_reasons_mql)
            else:
                drop_stage = 'Lead'
                drop_reason = np.random.choice(drop_reasons_lead)
        else:
            drop_stage = 'Visitor'
            drop_reason = np.random.choice(drop_reasons_visitor)

        # Build raw record
        rows.append({
            'visitor_id': visitor_id,
            'session_id': f"SES-{random.randint(10000000, 99999999)}",
            'channel_raw': ch_name if random.random() > 0.04 else ch_name.lower().replace(' ', '_'),
            'utm_source_raw': utm_source,
            'utm_medium_raw': utm_medium,
            'utm_campaign_raw': utm_campaign,
            'device_type': device if random.random() > 0.02 else device.lower(),
            'region': region,
            'customer_segment': segment,
            'company_size': company_size if random.random() > 0.05 else None,
            'lead_score_raw': lead_score,
            'visitor_timestamp': ts_visitor.strftime('%Y-%m-%d %H:%M:%S'),
            'lead_timestamp': ts_lead.strftime('%Y-%m-%d %H:%M:%S') if ts_lead else None,
            'mql_timestamp': ts_mql.strftime('%Y-%m-%d %H:%M:%S') if ts_mql else None,
            'sql_timestamp': ts_sql.strftime('%Y-%m-%d %H:%M:%S') if ts_sql else None,
            'opp_timestamp': ts_opp.strftime('%Y-%m-%d %H:%M:%S') if ts_opp else None,
            'customer_timestamp': ts_cust.strftime('%Y-%m-%d %H:%M:%S') if ts_cust else None,
            'stage_reached': 'Customer' if reached_cust else ('Opportunity' if reached_opp else ('SQL' if reached_sql else ('MQL' if reached_mql else ('Lead' if reached_lead else 'Visitor')))),
            'drop_off_stage': drop_stage,
            'drop_off_reason': drop_reason,
            'deal_arr_usd': deal_arr
        })

    df = pd.DataFrame(rows)

    # Inject intentional duplicates (approx 1.5% duplicates to simulate tracking re-triggers)
    duplicate_rows = df.sample(n=int(num_visitors * 0.015), random_state=random_seed)
    df_with_dups = pd.concat([df, duplicate_rows], ignore_index=True)

    # Inject a few out-of-bounds or whitespace anomalies
    sample_indices = np.random.choice(df_with_dups.index, size=100, replace=False)
    for idx in sample_indices:
        if df_with_dups.loc[idx, 'channel_raw']:
            df_with_dups.loc[idx, 'channel_raw'] = f"  {df_with_dups.loc[idx, 'channel_raw']}  "

    return df_with_dups

def generate_ad_spend_data():
    """Generates monthly ad spend and channel acquisition costs."""
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    channels = [
        'Paid Search (Google)',
        'Social Media - Paid',
        'Organic Search',
        'Email Marketing',
        'Referral / Partner',
        'Direct'
    ]

    spend_profiles = {
        'Paid Search (Google)': {'base_spend': 28000, 'spend_growth': 1.02, 'cpc': 2.85},
        'Social Media - Paid': {'base_spend': 22000, 'spend_growth': 1.03, 'cpc': 3.10},
        'Organic Search': {'base_spend': 8000, 'spend_growth': 1.01, 'cpc': 0.00},   # SEO tooling, agency retainer
        'Email Marketing': {'base_spend': 4500, 'spend_growth': 1.00, 'cpc': 0.00},   # ESP software cost
        'Referral / Partner': {'base_spend': 7500, 'spend_growth': 1.02, 'cpc': 0.00}, # Partner commissions
        'Direct': {'base_spend': 1000, 'spend_growth': 1.00, 'cpc': 0.00}            # Domain / Brand maintenance
    }

    spend_records = []
    for i, month in enumerate(months):
        for ch in channels:
            cfg = spend_profiles[ch]
            spend = cfg['base_spend'] * (cfg['spend_growth'] ** i) * np.random.uniform(0.94, 1.08)
            spend_records.append({
                'month': month,
                'channel': ch,
                'monthly_budget_usd': round(spend, 2),
                'cost_model': 'CPC/PPC' if 'Paid' in ch else 'Fixed/Retainer',
                'target_cpa_usd': 150.0 if 'Paid' in ch else 50.0
            })

    return pd.DataFrame(spend_records)

if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    os.makedirs(data_dir, exist_ok=True)
    
    print("Generating raw marketing funnel dataset (50,000 visitors + real-world anomalies)...")
    funnel_df = generate_funnel_data(num_visitors=50000, random_seed=42)
    raw_path = os.path.join(data_dir, 'raw_marketing_funnel.csv')
    funnel_df.to_csv(raw_path, index=False)
    print(f"Saved raw funnel data to: {raw_path} ({len(funnel_df)} rows)")

    print("Generating monthly ad spend and channel budget dataset...")
    spend_df = generate_ad_spend_data()
    spend_path = os.path.join(data_dir, 'raw_ad_spend_by_channel.csv')
    spend_df.to_csv(spend_path, index=False)
    print(f"Saved ad spend data to: {spend_path} ({len(spend_df)} rows)")
