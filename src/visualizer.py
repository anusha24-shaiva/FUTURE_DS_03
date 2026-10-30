"""
Marketing Funnel Data Visualizer
Generates high-resolution publication-quality charts (PNG) and interactive
visualizations for the executive report and presentations.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import numpy as np
import pandas as pd

# Set styling
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cbd5e1'
plt.rcParams['axes.linewidth'] = 1.0

PALETTE = {
    'primary': '#2563eb',    # Royal Blue
    'secondary': '#7c3aed',  # Purple
    'success': '#059669',    # Green
    'warning': '#d97706',    # Amber
    'danger': '#dc2626',     # Red
    'dark': '#0f172a',       # Dark Slate
    'gray': '#64748b',       # Muted Gray
    'bg': '#f8fafc',         # Off-white
    'card_bg': '#ffffff'
}

def plot_funnel_waterfall(funnel_df, output_path):
    """Plots a funnel waterfall showing counts, conversion rates, and drop-offs."""
    fig, ax1 = plt.subplots(figsize=(12, 6.5), dpi=300)
    fig.patch.set_facecolor(PALETTE['bg'])
    ax1.set_facecolor('#ffffff')

    stages = funnel_df['stage_name'].tolist()
    counts = funnel_df['count'].tolist()
    step_rates = funnel_df['step_conversion_rate_pct'].tolist()
    cum_rates = funnel_df['cumulative_conversion_rate_pct'].tolist()
    drop_rates = funnel_df['drop_off_rate_pct'].tolist()

    x = np.arange(len(stages))
    width = 0.55

    # Gradient-like bars
    colors = ['#1e40af', '#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#10b981']
    bars = ax1.bar(x, counts, width, color=colors, edgecolor='#1e293b', linewidth=1.2, zorder=3)

    # Annotate bar counts and rates
    for i, bar in enumerate(bars):
        h = bar.get_height()
        # Stage volume
        ax1.text(bar.get_x() + bar.get_width() / 2., h + (max(counts) * 0.015),
                 f"{h:,}\n({cum_rates[i]}%)",
                 ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1e293b')
        
        # Step conversion and drop-off badge between bars
        if i > 0:
            step_val = step_rates[i]
            drop_val = drop_rates[i-1]
            # Connecting indicator
            ax1.annotate(f"Conv: {step_val}%\nDrop: -{drop_val}%",
                         xy=(x[i] - width/2, (counts[i] + counts[i-1])/2.2),
                         xytext=(x[i] - width - 0.05, (counts[i] + counts[i-1])/2.2),
                         ha='center', va='center',
                         fontsize=8, fontweight='semibold',
                         color=PALETTE['danger'] if drop_val > 50 else PALETTE['dark'],
                         bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2" if drop_val > 50 else "#f1f5f9", ec="#fca5a5" if drop_val > 50 else "#cbd5e1", lw=0.8),
                         zorder=4)

    ax1.set_xticks(x)
    ax1.set_xticklabels(stages, fontsize=11, fontweight='bold', color='#0f172a')
    ax1.set_ylabel('Users / Leads in Stage', fontsize=11, fontweight='bold', color='#334155')
    ax1.set_title('End-to-End Marketing & Sales Funnel: Stage Progression & Drop-off Rates',
                  fontsize=14, fontweight='bold', pad=20, color='#0f172a')
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: f'{int(y):,}'))
    ax1.set_ylim(0, max(counts) * 1.18)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_channel_performance(channel_df, output_path):
    """Plots comparative channel conversion rates and deal metrics."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
    fig.patch.set_facecolor(PALETTE['bg'])
    ax1.set_facecolor('#ffffff')
    ax2.set_facecolor('#ffffff')

    sorted_df = channel_df.sort_values(by='overall_conversion_pct', ascending=True)

    # 1. Overall Conversion Rate (%)
    y_pos = np.arange(len(sorted_df))
    bars1 = ax1.barh(y_pos, sorted_df['overall_conversion_pct'], height=0.55,
                     color=['#dc2626' if x < 0.5 else ('#d97706' if x < 1.5 else '#059669') for x in sorted_df['overall_conversion_pct']],
                     edgecolor='#334155', linewidth=0.8)

    for bar in bars1:
        w = bar.get_width()
        ax1.text(w + 0.08, bar.get_y() + bar.get_height() / 2, f"{w:.2f}%",
                 ha='left', va='center', fontsize=9, fontweight='bold', color='#0f172a')

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(sorted_df['marketing_channel'], fontsize=10, fontweight='bold', color='#1e293b')
    ax1.set_xlabel('Overall Visitor-to-Customer Conversion Rate (%)', fontsize=10, fontweight='bold', color='#334155')
    ax1.set_title('Channel Conversion Efficiency (End-to-End)', fontsize=12, fontweight='bold', color='#0f172a')
    ax1.set_xlim(0, max(sorted_df['overall_conversion_pct']) * 1.25)

    # 2. Total ARR vs Spend
    sorted_rev = channel_df.sort_values(by='total_arr_usd', ascending=True)
    y_pos2 = np.arange(len(sorted_rev))
    
    width = 0.35
    b_rev = ax2.barh(y_pos2 + width/2, sorted_rev['total_arr_usd'] / 1e6, width, label='Total ARR ($M)', color='#2563eb', edgecolor='#1e40af')
    b_spend = ax2.barh(y_pos2 - width/2, sorted_rev['total_spend_usd'] / 1e6, width, label='Marketing Spend ($M)', color='#94a3b8', edgecolor='#64748b')

    for bar in b_rev:
        w = bar.get_width()
        ax2.text(w + 0.08, bar.get_y() + bar.get_height() / 2, f"${w:.2f}M",
                 ha='left', va='center', fontsize=8.5, fontweight='bold', color='#1e40af')

    ax2.set_yticks(y_pos2)
    ax2.set_yticklabels(sorted_rev['marketing_channel'], fontsize=10, fontweight='bold', color='#1e293b')
    ax2.set_xlabel('Amount ($ Millions USD)', fontsize=10, fontweight='bold', color='#334155')
    ax2.set_title('Revenue (ARR) Generated vs Marketing Spend', fontsize=12, fontweight='bold', color='#0f172a')
    ax2.legend(loc='lower right', frameon=True)
    ax2.set_xlim(0, max(sorted_rev['total_arr_usd'] / 1e6) * 1.25)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_cac_vs_ltv_bubble(channel_df, output_path):
    """Plots a 4-quadrant strategic bubble chart: CAC vs LTV with ARR bubble sizes."""
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor('#ffffff')

    # Filter out direct/unpaid if spend is 0 or very small
    df_plot = channel_df[channel_df['total_spend_usd'] > 0].copy()

    x = df_plot['customer_acquisition_cost_cac']
    y = df_plot['ltv_estimate_usd']
    sizes = (df_plot['total_arr_usd'] / 1e5) * 45  # Scale bubble size
    
    # 3:1 LTV:CAC target line
    max_cac = x.max() * 1.15
    ax.plot([0, max_cac], [0, max_cac * 3], linestyle='--', color='#059669', linewidth=1.8, label='Healthy SaaS 3:1 LTV:CAC Frontier')
    ax.fill_between([0, max_cac], [0, max_cac * 3], color='#dcfce7', alpha=0.3, label='Highly Profitable Growth Zone')

    scatter = ax.scatter(x, y, s=sizes, c=df_plot['roas'], cmap='viridis', alpha=0.85, edgecolors='#0f172a', linewidth=1.5, zorder=4)

    # Annotate labels
    for _, row in df_plot.iterrows():
        offset_y = 1500 if row['marketing_channel'] != 'Paid Search (Google)' else -2500
        ax.annotate(f"{row['marketing_channel']}\nCAC: ${row['cac']:,.0f} | LTV: ${row['ltv_estimate_usd']:,.0f}\nROAS: {row['roas']}x",
                    xy=(row['cac'], row['ltv_estimate_usd']),
                    xytext=(row['cac'] + 200, row['ltv_estimate_usd'] + offset_y),
                    fontsize=8.5, fontweight='bold', color='#0f172a',
                    bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec="#cbd5e1", alpha=0.9),
                    zorder=5)

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Return on Ad Spend (ROAS)', fontsize=10, fontweight='bold')

    ax.set_xlabel('Customer Acquisition Cost (CAC in USD)', fontsize=11, fontweight='bold', color='#334155')
    ax.set_ylabel('Estimated 3-Year Customer LTV (USD)', fontsize=11, fontweight='bold', color='#334155')
    ax.set_title('Channel Unit Economics: Customer Acquisition Cost (CAC) vs Lifetime Value (LTV)',
                 fontsize=13, fontweight='bold', pad=15, color='#0f172a')
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f'${int(val):,}'))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f'${int(val):,}'))
    ax.legend(loc='upper left', frameon=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_drop_off_reasons(reasons_df, output_path):
    """Plots top drop-off reasons across funnel stages."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    fig.patch.set_facecolor(PALETTE['bg'])
    
    stages_to_plot = ['Visitor', 'Lead', 'SQL', 'Opportunity']
    colors_map = {
        'Visitor': '#3b82f6',
        'Lead': '#8b5cf6',
        'SQL': '#f59e0b',
        'Opportunity': '#ef4444'
    }

    for i, stage in enumerate(stages_to_plot):
        ax = axes[i // 2, i % 2]
        ax.set_facecolor('#ffffff')
        stage_data = reasons_df[reasons_df['drop_off_stage'] == stage].sort_values(by='count', ascending=True)

        y = np.arange(len(stage_data))
        bars = ax.barh(y, stage_data['count'], height=0.55, color=colors_map[stage], edgecolor='#1e293b', linewidth=0.8)

        for bar in bars:
            w = bar.get_width()
            ax.text(w + (stage_data['count'].max() * 0.02), bar.get_y() + bar.get_height() / 2,
                    f"{int(w):,}", ha='left', va='center', fontsize=9, fontweight='bold', color='#0f172a')

        ax.set_yticks(y)
        ax.set_yticklabels(stage_data['drop_off_reason'], fontsize=9, fontweight='semibold', color='#1e293b')
        ax.set_xlabel('Drop-off Volume', fontsize=9, fontweight='bold', color='#475569')
        ax.set_title(f'Drop-off Drivers at Stage: {stage}', fontsize=11, fontweight='bold', color='#0f172a')
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda val, _: f'{int(val):,}'))
        ax.set_xlim(0, stage_data['count'].max() * 1.25)

    plt.suptitle('Root Cause Diagnostic: Why Prospects Drop Off at Each Funnel Stage', fontsize=14, fontweight='bold', y=0.99, color='#0f172a')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def plot_revenue_uplift(scenarios_df, output_path):
    """Plots the simulated revenue uplift from targeted optimization initiatives."""
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    fig.patch.set_facecolor(PALETTE['bg'])
    ax.set_facecolor('#ffffff')

    y_pos = np.arange(len(scenarios_df))
    bars = ax.barh(y_pos, scenarios_df['additional_arr_usd'] / 1e6, height=0.5,
                   color=['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b'],
                   edgecolor='#0f172a', linewidth=1.0)

    for bar, (_, row) in zip(bars, scenarios_df.iterrows()):
        w = bar.get_width()
        ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2,
                f"+${w:.2f}M ARR  (+{row['net_new_customers']} Won Customers)",
                ha='left', va='center', fontsize=9.5, fontweight='bold', color='#0f172a')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(scenarios_df['initiative'], fontsize=9.5, fontweight='bold', color='#1e293b')
    ax.set_xlabel('Projected Additional ARR ($ Millions USD)', fontsize=10.5, fontweight='bold', color='#334155')
    ax.set_title('What-If Sensitivity Model: Revenue Uplift from Targeted Stage Optimizations',
                 fontsize=13, fontweight='bold', pad=15, color='#0f172a')
    ax.set_xlim(0, max(scenarios_df['additional_arr_usd'] / 1e6) * 1.35)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

def generate_all_figures(cleaned_data_path, cleaned_spend_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.funnel_analyzer import FunnelAnalyzer
    
    analyzer = FunnelAnalyzer(cleaned_data_path, cleaned_spend_path)
    
    funnel_df = analyzer.compute_overall_funnel()
    plot_funnel_waterfall(funnel_df, os.path.join(output_dir, 'funnel_waterfall_dropoff.png'))
    
    channel_df = analyzer.compute_channel_performance()
    plot_channel_performance(channel_df, os.path.join(output_dir, 'channel_conversion_matrix.png'))
    plot_cac_vs_ltv_bubble(channel_df, os.path.join(output_dir, 'cac_vs_ltv_bubble_chart.png'))
    
    reasons_df = analyzer.compute_drop_off_reasons()
    plot_drop_off_reasons(reasons_df, os.path.join(output_dir, 'drop_off_reasons_breakdown.png'))
    
    scenarios_df = analyzer.simulate_conversion_uplift()
    plot_revenue_uplift(scenarios_df, os.path.join(output_dir, 'revenue_uplift_simulation.png'))
    print("All analytical figures generated successfully!")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(__file__))
    clean_data = os.path.join(base_dir, 'data', 'processed', 'cleaned_funnel_journeys.csv')
    clean_spend = os.path.join(base_dir, 'data', 'processed', 'cleaned_ad_spend_by_channel.csv')
    figures_dir = os.path.join(base_dir, 'reports', 'figures')
    
    generate_all_figures(clean_data, clean_spend, figures_dir)
