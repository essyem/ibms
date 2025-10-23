/* Dashboard charts: fetch analytics_api and render Chart.js charts */
document.addEventListener('DOMContentLoaded', function() {
    // Load Chart.js dynamically if not present
    function loadChartJs(callback) {
        if (window.Chart) return callback();
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
        script.onload = callback;
        document.head.appendChild(script);
    }

    loadChartJs(() => {
        // Fetch analytics data and dashboard summary in parallel
    const analyticsPromise = fetch('/api/analytics/', { credentials: 'same-origin' }).then(r => r.json()).catch(() => ({ revenue_trend: [], top_customers: [] }));
    const summaryPromise = fetch('/dashboard_summary_api/', { credentials: 'same-origin' }).then(r => r.json()).catch(() => null);

        Promise.all([analyticsPromise, summaryPromise]).then(([data, summary]) => {
            if (summary && summary.html) {
                const placeholder = document.getElementById('dashboard-summary-placeholder');
                if (placeholder) placeholder.innerHTML = summary.html;
            }

            // Use analytics data to render charts
            // (fall through to existing rendering logic)
            
            // Ensure data is defined
            data = data || { revenue_trend: [], top_customers: [] };

            // Render charts below
        
            // Revenue trend (line)
            
            
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
            
                // Revenue trend (line)
                const revenueCtx = document.getElementById('chartRevenue');
                if (revenueCtx && revenueCtx.getContext) {
                    const rCtx = revenueCtx.getContext('2d');
                    const revenueLabels = data.revenue_trend.map(d => d.date).reverse();
                    const revenueData = data.revenue_trend.map(d => d.revenue).reverse();

                    new Chart(rCtx, {
                    type: 'line',
                    data: {
                        labels: revenueLabels,
                        datasets: [{
                            label: 'Daily Revenue',
                            data: revenueData,
                            fill: true,
                            backgroundColor: 'rgba(54,162,235,0.12)',
                            borderColor: 'rgba(54,162,235,1)',
                            tension: 0.3,
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { x: { display: false }, y: { ticks: { callback: function(v){ return 'QAR ' + v; } } } }
                    }
                });
                }

                // Top customers (bar)
                const customers = data.top_customers || [];
                const custLabels = customers.map(c => c.name);
                const custData = customers.map(c => c.revenue);
                const topCustEl = document.getElementById('chartTopCustomers');
                if (topCustEl && topCustEl.getContext) {
                    const custCtx = topCustEl.getContext('2d');
                    new Chart(custCtx, {
                    type: 'bar',
                    data: { labels: custLabels, datasets: [{ label: 'Revenue', data: custData, backgroundColor: 'rgba(99,102,241,0.9)' }] },
                    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { ticks: { callback: v => 'QAR ' + v } } } }
                });
                }

                // Sparklines for quick stats (if present)
                document.querySelectorAll('.sparkline').forEach((el, idx) => {
                    if (!el.getContext) return;
                    const ctx = el.getContext('2d');
                    const values = (data.revenue_trend && data.revenue_trend.length) ? data.revenue_trend.map(d => d.revenue).slice(-10) : [0,0,0,0,0,0,0,0,0,0];
                    new Chart(ctx, { type: 'line', data: { labels: values.map((_,i)=>i+1), datasets:[{ data: values, borderColor: 'rgba(34,34,34,0.95)', backgroundColor:'rgba(91,70,246,0.12)', tension:0.3 }] }, options:{ responsive:true, plugins:{ legend:{ display:false } }, scales:{ x:{ display:false }, y:{ display:false } } } });
                });
            })
            .catch(err => console.error('Analytics API error', err));
    });
});
