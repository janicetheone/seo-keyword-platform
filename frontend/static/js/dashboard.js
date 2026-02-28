// Dashboard - load stats, charts, and top keywords

let categoryChartInstance = null;
let opportunityChartInstance = null;
let competitorChartInstance = null;

function heatClass(score) {
    if (score >= 70) return 'heat-hot';
    if (score >= 50) return 'heat-warm';
    if (score >= 30) return 'heat-mild';
    if (score >= 15) return 'heat-cool';
    return 'heat-cold';
}

async function loadDashboard() {
    // Load stats
    const stats = await fetch('/api/dashboard/stats').then(r => r.json());
    document.getElementById('stat-total').textContent = stats.total_keywords.toLocaleString();
    document.getElementById('stat-new').textContent = `+${stats.new_this_week}`;
    document.getElementById('stat-rising').textContent = stats.rising_count;
    document.getElementById('stat-heat').textContent = stats.avg_heat_score;

    if (stats.last_collection) {
        document.getElementById('last-collection').textContent =
            `${stats.last_collection.type} (${stats.last_collection.status}) - ${new Date(stats.last_collection.time).toLocaleString()}`;
    }

    // Category pie chart
    if (stats.category_distribution && stats.category_distribution.length > 0) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        if (categoryChartInstance) categoryChartInstance.destroy();
        categoryChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: stats.category_distribution.map(c => c.display_name),
                datasets: [{
                    data: stats.category_distribution.map(c => c.count),
                    backgroundColor: stats.category_distribution.map(c => c.color),
                    borderWidth: 2,
                    borderColor: '#fff',
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } },
                }
            }
        });
    }

    // Top keywords
    const topKws = await fetch('/api/dashboard/top-keywords?limit=20').then(r => r.json());
    const tbody = document.getElementById('top-keywords-body');
    tbody.innerHTML = topKws.map((kw, i) => `
        <tr>
            <td class="text-xs text-gray-400">${i + 1}</td>
            <td>
                <a href="/keywords/${kw.id}" class="text-indigo-600 hover:underline font-medium">${kw.keyword}</a>
            </td>
            <td><span class="heat-badge ${heatClass(kw.heat_score)}">${kw.heat_score}</span></td>
            <td>${kw.is_rising ? '<span class="rising-tag">&#9650; Rising</span>' : ''}</td>
        </tr>
    `).join('');

    // Opportunity matrix
    const matrix = await fetch('/api/dashboard/opportunity-matrix').then(r => r.json());
    if (matrix.length > 0) {
        const ctx2 = document.getElementById('opportunityChart').getContext('2d');
        if (opportunityChartInstance) opportunityChartInstance.destroy();
        opportunityChartInstance = new Chart(ctx2, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Keywords',
                    data: matrix.map(m => ({ x: m.competition, y: m.heat_score, label: m.keyword })),
                    backgroundColor: matrix.map(m => m.is_rising ? '#059669' : '#6366f1'),
                    pointRadius: 5,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: 'Competition' }, min: 0, max: 1 },
                    y: { title: { display: true, text: 'Heat Score' }, min: 0, max: 100 },
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const point = matrix[ctx.dataIndex];
                                return `${point.keyword}: Heat ${point.heat_score}, Comp ${point.competition}`;
                            }
                        }
                    },
                    legend: { display: false },
                }
            }
        });
    }

    // Competitor coverage
    const coverage = await fetch('/api/dashboard/competitor-coverage').then(r => r.json());
    if (coverage.length > 0) {
        const ctx3 = document.getElementById('competitorChart').getContext('2d');
        if (competitorChartInstance) competitorChartInstance.destroy();
        competitorChartInstance = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: coverage.map(c => c.name),
                datasets: [{
                    label: 'Keywords',
                    data: coverage.map(c => c.keyword_count),
                    backgroundColor: '#6366f1',
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true },
                }
            }
        });
    }
}

loadDashboard();
