/**
 * FunnelPulse™ Analytics Dashboard Controller
 * Powers interactive filtering, funnel waterfall rendering, Chart.js visualizations,
 * What-If revenue simulations, and theme management.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check if data is available
    if (!window.FUNNEL_DASHBOARD_DATA) {
        console.error("Dashboard data not loaded. Make sure funnel_dashboard_data.js is present.");
        return;
    }

    const data = window.FUNNEL_DASHBOARD_DATA;
    let dropoffChart = null;
    let velocityChart = null;
    let cohortChart = null;

    // Theme Management
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');

    function applyTheme(isDark) {
        if (isDark) {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            themeText.textContent = 'Light';
        } else {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            themeText.textContent = 'Dark';
        }
        updateChartThemes(isDark);
    }

    const savedTheme = localStorage.getItem('funnel_theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    let isDarkMode = savedTheme !== null ? savedTheme === 'dark' : prefersDark;
    applyTheme(isDarkMode);

    themeToggleBtn.addEventListener('click', () => {
        isDarkMode = !isDarkMode;
        localStorage.setItem('funnel_theme', isDarkMode ? 'dark' : 'light');
        applyTheme(isDarkMode);
    });

    // Formatters
    const fmtNumber = num => Math.round(num).toLocaleString('en-US');
    const fmtCurrency = num => '$' + (num >= 1e6 ? (num / 1e6).toFixed(2) + 'M' : Math.round(num).toLocaleString('en-US'));

    // Render Funnel Visualizer
    function renderFunnel(stages) {
        const container = document.getElementById('funnelVisualizer');
        container.innerHTML = '';

        const maxCount = stages[0].count;
        const stageColors = [
            'linear-gradient(90deg, #1e40af, #2563eb)',
            'linear-gradient(90deg, #2563eb, #3b82f6)',
            'linear-gradient(90deg, #4f46e5, #6366f1)',
            'linear-gradient(90deg, #7c3aed, #8b5cf6)',
            'linear-gradient(90deg, #0284c7, #06b6d4)',
            'linear-gradient(90deg, #059669, #10b981)'
        ];

        stages.forEach((st, idx) => {
            const widthPct = Math.max(12, (st.count / maxCount) * 100);
            
            const stageRow = document.createElement('div');
            stageRow.className = 'funnel-stage-row';
            
            stageRow.innerHTML = `
                <div class="funnel-stage-info">
                    <div class="stage-title-wrap">
                        <span class="stage-dot" style="background: ${['#2563eb','#3b82f6','#6366f1','#8b5cf6','#06b6d4','#10b981'][idx]}"></span>
                        <span><strong>Stage ${st.stage_order}: ${st.stage_name}</strong></span>
                    </div>
                    <div>
                        <span><strong>${fmtNumber(st.count)}</strong> (${st.cumulative_conversion_rate_pct}% cum.)</span>
                    </div>
                </div>
                <div class="funnel-bar-bg">
                    <div class="funnel-bar-fill" style="width: ${widthPct}%; background: ${stageColors[idx]};">
                        <span>${st.stage_order === 1 ? '100% Entry' : st.step_conversion_rate_pct + '% Step Conv.'}</span>
                    </div>
                </div>
                ${idx < stages.length - 1 ? `
                    <div class="dropoff-connector">
                        <div class="dropoff-line"></div>
                        <span>Stage Drop-off: <strong>-${st.drop_off_rate_pct}%</strong> (${fmtNumber(st.drop_off_count)} lost)</span>
                    </div>
                ` : ''}
            `;
            container.appendChild(stageRow);
        });
    }

    // Render Channel Table
    function renderChannelTable(channels) {
        const tbody = document.getElementById('channelTableBody');
        tbody.innerHTML = '';

        channels.forEach(ch => {
            const tr = document.createElement('tr');
            
            let effBadge = '<span class="efficiency-pill eff-med">Balanced Growth</span>';
            if (ch.roas >= 20 || ch.overall_conversion_pct >= 2.0) {
                effBadge = '<span class="efficiency-pill eff-high">★ Star Performer</span>';
            } else if (ch.roas < 3.0 || ch.cac > 8000) {
                effBadge = '<span class="efficiency-pill eff-low">Needs Optimization</span>';
            }

            tr.innerHTML = `
                <td><strong>${ch.marketing_channel}</strong></td>
                <td>${fmtNumber(ch.visitors)}</td>
                <td>${fmtNumber(ch.leads)}</td>
                <td><strong>${fmtNumber(ch.customers)}</strong></td>
                <td>${ch.traffic_to_lead_pct}%</td>
                <td>${ch.lead_to_customer_pct}%</td>
                <td><strong>${fmtCurrency(ch.total_arr_usd)}</strong></td>
                <td>${ch.cac ? '$' + fmtNumber(ch.cac) : 'N/A'}</td>
                <td>${ch.ltv_to_cac_ratio ? ch.ltv_to_cac_ratio + 'x' : 'N/A'}</td>
                <td><strong>${ch.roas ? ch.roas + 'x' : 'N/A'}</strong></td>
                <td>${effBadge}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // Chart.js Visualizations
    function initCharts(isDark) {
        const textColor = isDark ? '#94a3b8' : '#475569';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        // 1. Drop-off Reasons Chart (Top 8 reasons)
        const ctxDrop = document.getElementById('dropoffReasonsChart').getContext('2d');
        const sortedReasons = [...data.drop_off_reasons]
            .filter(r => r.drop_off_stage !== 'Visitor') // Visitor bounces dominate by pure volume; showcase middle/bottom friction
            .sort((a, b) => b.count - a.count)
            .slice(0, 7);

        dropoffChart = new Chart(ctxDrop, {
            type: 'bar',
            data: {
                labels: sortedReasons.map(r => `[${r.drop_off_stage}] ${r.drop_off_reason}`),
                datasets: [{
                    label: 'Lost Prospects',
                    data: sortedReasons.map(r => r.count),
                    backgroundColor: [
                        '#ef4444', '#f97316', '#f59e0b', '#8b5cf6', '#3b82f6', '#06b6d4', '#ec4899'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: ctx => ` ${fmtNumber(ctx.raw)} lost opportunities`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { family: 'Plus Jakarta Sans' } }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } }
                    }
                }
            }
        });

        // 2. Velocity Chart (Sales Cycle Days per Channel)
        const ctxVel = document.getElementById('velocityChart').getContext('2d');
        const channelVel = data.velocity.channel_velocity.sort((a, b) => a.median_days - b.median_days);

        velocityChart = new Chart(ctxVel, {
            type: 'bar',
            data: {
                labels: channelVel.map(c => c.marketing_channel),
                datasets: [
                    {
                        label: 'Median Sales Cycle (Days)',
                        data: channelVel.map(c => c.median_days),
                        backgroundColor: '#3b82f6',
                        borderRadius: 6
                    },
                    {
                        label: 'Mean Sales Cycle (Days)',
                        data: channelVel.map(c => c.mean_days),
                        backgroundColor: '#93c5fd',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 10 } }
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, callback: val => `${val} days` }
                    }
                }
            }
        });

        // 3. Monthly Funnel Cohort Trends
        const ctxCohort = document.getElementById('cohortTrendChart').getContext('2d');
        const months = data.monthly_trends.map(m => m.visitor_cohort_month);

        cohortChart = new Chart(ctxCohort, {
            type: 'line',
            data: {
                labels: months,
                datasets: [
                    {
                        label: 'Captured Leads',
                        data: data.monthly_trends.map(m => m.leads),
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: true,
                        tension: 0.35,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Won Customers',
                        data: data.monthly_trends.map(m => m.customers),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        fill: false,
                        tension: 0.35,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } }
                    }
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        type: 'linear',
                        position: 'left',
                        grid: { color: gridColor },
                        ticks: { color: textColor },
                        title: { display: true, text: 'Leads Volume', color: textColor }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        grid: { display: false },
                        ticks: { color: '#10b981' },
                        title: { display: true, text: 'Customers Won', color: '#10b981' }
                    }
                }
            }
        });
    }

    function updateChartThemes(isDark) {
        const textColor = isDark ? '#94a3b8' : '#475569';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        [dropoffChart, velocityChart, cohortChart].forEach(chart => {
            if (chart) {
                if (chart.options.scales.x) {
                    if (chart.options.scales.x.ticks) chart.options.scales.x.ticks.color = textColor;
                    if (chart.options.scales.x.grid) chart.options.scales.x.grid.color = gridColor;
                }
                if (chart.options.scales.y) {
                    if (chart.options.scales.y.ticks) chart.options.scales.y.ticks.color = textColor;
                    if (chart.options.scales.y.grid) chart.options.scales.y.grid.color = gridColor;
                }
                if (chart.options.plugins && chart.options.plugins.legend) {
                    chart.options.plugins.legend.labels.color = textColor;
                }
                chart.update();
            }
        });
    }

    // Interactive What-If Simulator Logic
    const trafficSlider = document.getElementById('trafficSlider');
    const leadRateSlider = document.getElementById('leadRateSlider');
    const mqlRateSlider = document.getElementById('mqlRateSlider');
    const winRateSlider = document.getElementById('winRateSlider');

    const trafficVal = document.getElementById('trafficVal');
    const leadRateVal = document.getElementById('leadRateVal');
    const mqlRateVal = document.getElementById('mqlRateVal');
    const winRateVal = document.getElementById('winRateVal');

    const simCustomersEl = document.getElementById('simCustomers');
    const simCustomerDiffEl = document.getElementById('simCustomerDiff');
    const simArrEl = document.getElementById('simArr');
    const simArrDiffEl = document.getElementById('simArrDiff');
    const simConvRateEl = document.getElementById('simConvRate');
    const simConvDiffEl = document.getElementById('simConvDiff');
    const resetSimBtn = document.getElementById('resetSimBtn');

    const baseVisitors = data.kpis.total_visitors;
    const baseCustomers = data.kpis.total_customers;
    const baseArr = data.kpis.total_arr_usd;
    const avgArr = data.kpis.avg_deal_arr_usd;
    
    // Constant mid-funnel transition rates from baseline
    const mqlToSqlRate = data.kpis.total_sqls / data.kpis.total_mqls;
    const sqlToOppRate = data.kpis.total_opps / data.kpis.total_sqls;

    function runSimulation() {
        const traffic = parseFloat(trafficSlider.value);
        const leadRate = parseFloat(leadRateSlider.value) / 100.0;
        const mqlRate = parseFloat(mqlRateSlider.value) / 100.0;
        const winRate = parseFloat(winRateSlider.value) / 100.0;

        // Display current slider values
        const trafficGrowth = Math.round(((traffic - baseVisitors) / baseVisitors) * 100);
        trafficVal.textContent = `${fmtNumber(traffic)} (${trafficGrowth >= 0 ? '+' : ''}${trafficGrowth}%)`;
        leadRateVal.textContent = `${(leadRate * 100).toFixed(1)}%`;
        mqlRateVal.textContent = `${(mqlRate * 100).toFixed(1)}%`;
        winRateVal.textContent = `${(winRate * 100).toFixed(1)}%`;

        // Compute simulated stage progression
        const simLeads = traffic * leadRate;
        const simMqls = simLeads * mqlRate;
        const simSqls = simMqls * mqlToSqlRate;
        const simOpps = simSqls * sqlToOppRate;
        const simCustomers = Math.round(simOpps * winRate);
        const simArr = simCustomers * avgArr;
        const simConv = (simCustomers / traffic) * 100.0;

        const custDiff = simCustomers - baseCustomers;
        const arrDiff = simArr - baseArr;

        simCustomersEl.textContent = fmtNumber(simCustomers);
        simCustomerDiffEl.textContent = `${custDiff >= 0 ? '+' : ''}${fmtNumber(custDiff)} vs Baseline`;
        simCustomerDiffEl.style.color = custDiff >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';

        simArrEl.textContent = fmtCurrency(simArr);
        simArrDiffEl.textContent = `${arrDiff >= 0 ? '+' : ''}${fmtCurrency(arrDiff)} ARR Delta`;
        simArrDiffEl.style.color = arrDiff >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';

        simConvRateEl.textContent = simConv.toFixed(2) + '%';
        simConvDiffEl.textContent = `Baseline: ${(baseCustomers / baseVisitors * 100).toFixed(2)}%`;
    }

    [trafficSlider, leadRateSlider, mqlRateSlider, winRateSlider].forEach(slider => {
        slider.addEventListener('input', runSimulation);
    });

    resetSimBtn.addEventListener('click', () => {
        trafficSlider.value = 50000;
        leadRateSlider.value = 11.8;
        mqlRateSlider.value = 51.2;
        winRateSlider.value = 39.2;
        runSimulation();
    });

    // Global Channel & Segment Filtering
    const channelFilter = document.getElementById('channelFilter');
    const segmentFilter = document.getElementById('segmentFilter');
    const deviceFilter = document.getElementById('deviceFilter');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    const funnelScopeBadge = document.getElementById('funnelScopeBadge');

    function applyFilters() {
        const selectedCh = channelFilter.value;
        const selectedSeg = segmentFilter.value;
        const selectedDev = deviceFilter.value;

        funnelScopeBadge.textContent = selectedCh === 'ALL' ? 'All Channels Blended' : selectedCh;

        if (selectedCh === 'ALL') {
            renderFunnel(data.funnel_stages);
            renderChannelTable(data.channel_performance);
            // Reset KPI display
            document.getElementById('val-visitors').textContent = fmtNumber(data.kpis.total_visitors);
            document.getElementById('val-leads').textContent = fmtNumber(data.kpis.total_leads);
            document.getElementById('val-sqls').textContent = fmtNumber(data.kpis.total_sqls);
            document.getElementById('val-customers').textContent = fmtNumber(data.kpis.total_customers);
            document.getElementById('val-revenue').textContent = fmtCurrency(data.kpis.total_arr_usd);
        } else {
            const chMatch = data.channel_performance.find(c => c.marketing_channel === selectedCh);
            if (chMatch) {
                // Synthesize stages for single channel
                const chStages = [
                    { stage_order: 1, stage_name: 'Visitor', count: chMatch.visitors, step_conversion_rate_pct: 100, cumulative_conversion_rate_pct: 100, drop_off_count: chMatch.visitors - chMatch.leads, drop_off_rate_pct: ((chMatch.visitors - chMatch.leads)/chMatch.visitors * 100).toFixed(1) },
                    { stage_order: 2, stage_name: 'Lead', count: chMatch.leads, step_conversion_rate_pct: chMatch.traffic_to_lead_pct, cumulative_conversion_rate_pct: chMatch.traffic_to_lead_pct, drop_off_count: chMatch.leads - chMatch.mqls, drop_off_rate_pct: ((chMatch.leads - chMatch.mqls)/chMatch.leads * 100).toFixed(1) },
                    { stage_order: 3, stage_name: 'MQL', count: chMatch.mqls, step_conversion_rate_pct: chMatch.lead_to_mql_pct, cumulative_conversion_rate_pct: ((chMatch.mqls/chMatch.visitors)*100).toFixed(1), drop_off_count: chMatch.mqls - chMatch.sqls, drop_off_rate_pct: ((chMatch.mqls - chMatch.sqls)/chMatch.mqls * 100).toFixed(1) },
                    { stage_order: 4, stage_name: 'SQL', count: chMatch.sqls, step_conversion_rate_pct: chMatch.mql_to_sql_pct, cumulative_conversion_rate_pct: ((chMatch.sqls/chMatch.visitors)*100).toFixed(1), drop_off_count: chMatch.sqls - chMatch.opportunities, drop_off_rate_pct: ((chMatch.sqls - chMatch.opportunities)/chMatch.sqls * 100).toFixed(1) },
                    { stage_order: 5, stage_name: 'Opportunity', count: chMatch.opportunities, step_conversion_rate_pct: chMatch.sql_to_opp_pct, cumulative_conversion_rate_pct: ((chMatch.opportunities/chMatch.visitors)*100).toFixed(1), drop_off_count: chMatch.opportunities - chMatch.customers, drop_off_rate_pct: ((chMatch.opportunities - chMatch.customers)/chMatch.opportunities * 100).toFixed(1) },
                    { stage_order: 6, stage_name: 'Customer', count: chMatch.customers, step_conversion_rate_pct: chMatch.opp_to_cust_pct, cumulative_conversion_rate_pct: chMatch.overall_conversion_pct, drop_off_count: 0, drop_off_rate_pct: 0 }
                ];
                renderFunnel(chStages);
                renderChannelTable([chMatch]);

                // Update KPIs
                document.getElementById('val-visitors').textContent = fmtNumber(chMatch.visitors);
                document.getElementById('val-leads').textContent = fmtNumber(chMatch.leads);
                document.getElementById('val-sqls').textContent = fmtNumber(chMatch.sqls);
                document.getElementById('val-customers').textContent = fmtNumber(chMatch.customers);
                document.getElementById('val-revenue').textContent = fmtCurrency(chMatch.total_arr_usd);
            }
        }
    }

    channelFilter.addEventListener('change', applyFilters);
    segmentFilter.addEventListener('change', applyFilters);
    deviceFilter.addEventListener('change', applyFilters);
    
    resetFiltersBtn.addEventListener('click', () => {
        channelFilter.value = 'ALL';
        segmentFilter.value = 'ALL';
        deviceFilter.value = 'ALL';
        applyFilters();
    });

    // CSV Export
    document.getElementById('exportCsvBtn').addEventListener('click', () => {
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Channel,Visitors,Leads,Won_Customers,Traffic_to_Lead_Pct,Lead_to_Customer_Pct,Total_ARR,CAC,LTV_CAC,ROAS\n";
        data.channel_performance.forEach(c => {
            csvContent += `"${c.marketing_channel}",${c.visitors},${c.leads},${c.customers},${c.traffic_to_lead_pct},${c.lead_to_customer_pct},${c.total_arr_usd},${c.cac || 0},${c.ltv_to_cac_ratio || 0},${c.roas || 0}\n`;
        });
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "channel_funnel_performance.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Initial Execution
    renderFunnel(data.funnel_stages);
    renderChannelTable(data.channel_performance);
    initCharts(isDarkMode);
    runSimulation();
});
