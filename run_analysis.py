"""
Marketing Funnel & Conversion Performance Analysis
Master Pipeline Runner Script
Executes data generation, cleaning, statistical analysis, figure rendering,
dashboard payload export, and Jupyter notebook compilation in one command.
"""

import os
import sys
import time

def run_master_pipeline():
    start_time = time.time()
    print("=" * 75)
    print("   MARKETING FUNNEL & CONVERSION PERFORMANCE ANALYSIS PIPELINE")
    print("   Task 3 (2026) • Future Interns Analytics Suite")
    print("=" * 75)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, 'data', 'raw')
    proc_dir = os.path.join(base_dir, 'data', 'processed')
    reports_dir = os.path.join(base_dir, 'reports', 'figures')
    dash_data_dir = os.path.join(base_dir, 'dashboard', 'data')
    nb_dir = os.path.join(base_dir, 'notebooks')

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(proc_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(dash_data_dir, exist_ok=True)
    os.makedirs(nb_dir, exist_ok=True)

    raw_funnel = os.path.join(raw_dir, 'raw_marketing_funnel.csv')
    raw_spend = os.path.join(raw_dir, 'raw_ad_spend_by_channel.csv')

    # Step 1: Data Generation (if missing or refreshed)
    if not os.path.exists(raw_funnel) or not os.path.exists(raw_spend):
        print("\n[STEP 1/6] Generating raw marketing funnel and ad spend datasets...")
        from src.data_generator import generate_funnel_data, generate_ad_spend_data
        df_raw = generate_funnel_data(num_visitors=50000, random_seed=42)
        df_raw.to_csv(raw_funnel, index=False)
        df_sp = generate_ad_spend_data()
        df_sp.to_csv(raw_spend, index=False)
        print(f" -> Raw data generated successfully ({len(df_raw)} records).")
    else:
        print("\n[STEP 1/6] Raw dataset already exists. Skipping re-generation.")

    # Step 2: Data Cleaning & Chronological Validation
    print("\n[STEP 2/6] Executing data cleaning and chronological validation pipeline...")
    from src.data_cleaner import clean_marketing_funnel
    df_clean, audit = clean_marketing_funnel(raw_funnel, raw_spend, proc_dir)
    print(f" -> Cleaned dataset saved ({len(df_clean)} records). Duplicates removed: {audit['duplicates_removed']}.")

    # Step 3: Analytical Metrics Engine
    print("\n[STEP 3/6] Running funnel analytics engine...")
    from src.funnel_analyzer import FunnelAnalyzer
    clean_data_path = os.path.join(proc_dir, 'cleaned_funnel_journeys.csv')
    clean_spend_path = os.path.join(proc_dir, 'cleaned_ad_spend_by_channel.csv')
    analyzer = FunnelAnalyzer(clean_data_path, clean_spend_path)
    
    funnel_summary = analyzer.compute_overall_funnel()
    channel_summary = analyzer.compute_channel_performance()
    scenarios = analyzer.simulate_conversion_uplift()

    # Save summary tables
    funnel_summary.to_csv(os.path.join(proc_dir, 'funnel_stage_metrics.csv'), index=False)
    channel_summary.to_csv(os.path.join(proc_dir, 'channel_conversion_performance.csv'), index=False)
    scenarios.to_csv(os.path.join(proc_dir, 'simulated_revenue_uplift.csv'), index=False)
    print(" -> Funnel summary metrics saved to data/processed/")

    # Step 4: High-Resolution Visualizations
    print("\n[STEP 4/6] Generating publication-quality analytical figures...")
    from src.visualizer import generate_all_figures
    generate_all_figures(clean_data_path, clean_spend_path, reports_dir)

    # Step 5: Export Dashboard Data
    print("\n[STEP 5/6] Exporting web dashboard payload...")
    from src.export_dashboard_data import export_dashboard_payload
    export_dashboard_payload(clean_data_path, clean_spend_path, dash_data_dir)

    # Step 6: Compile Jupyter Notebook
    print("\n[STEP 6/6] Compiling Jupyter Notebook...")
    from src.generate_notebook import create_marketing_funnel_notebook
    nb_path = os.path.join(nb_dir, 'marketing_funnel_analysis.ipynb')
    create_marketing_funnel_notebook(nb_path)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 75)
    print(f" PIPELINE COMPLETED SUCCESSFULLY IN {elapsed} SECONDS!")
    print("=" * 75)
    print("\nDeliverables Created:")
    print(" 1. Processed Data:       data/processed/cleaned_funnel_journeys.csv")
    print(" 2. Executive Charts:     reports/figures/ (*.png)")
    print(" 3. Interactive Dashboard:dashboard/index.html (open in any web browser)")
    print(" 4. Jupyter Notebook:     notebooks/marketing_funnel_analysis.ipynb")
    print(" 5. Executive Report:     reports/EXECUTIVE_REPORT.md")
    print(" 6. Power BI Guide:       reports/powerbi_tableau_guide.md")
    print("=" * 75)

if __name__ == '__main__':
    run_master_pipeline()
