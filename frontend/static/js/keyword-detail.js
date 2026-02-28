// Keyword Detail page

function heatClass(score) {
    if (score >= 70) return 'heat-hot';
    if (score >= 50) return 'heat-warm';
    if (score >= 30) return 'heat-mild';
    if (score >= 15) return 'heat-cool';
    return 'heat-cold';
}

async function loadKeywordDetail() {
    const kw = await fetch(`/api/keywords/${KEYWORD_ID}`).then(r => r.json());

    if (kw.error) {
        document.getElementById('kw-text').textContent = 'Keyword not found';
        return;
    }

    document.getElementById('kw-text').textContent = kw.keyword;
    const heatEl = document.getElementById('kw-heat');
    heatEl.textContent = kw.heat_score;
    heatEl.className = 'text-3xl font-bold';
    heatEl.style.color = { 'heat-hot': '#dc2626', 'heat-warm': '#ea580c', 'heat-mild': '#ca8a04', 'heat-cool': '#16a34a', 'heat-cold': '#64748b' }[heatClass(kw.heat_score)];
    document.getElementById('kw-trends').textContent = kw.trends_score > 0 ? kw.trends_score.toFixed(1) : '-';
    document.getElementById('kw-rank').textContent = kw.autocomplete_rank || '-';
    document.getElementById('kw-sources').textContent = kw.source_count;

    // Meta badges
    const meta = document.getElementById('kw-meta');
    let metaHtml = '';
    metaHtml += `<span class="heat-badge ${heatClass(kw.heat_score)}">Heat: ${kw.heat_score}</span>`;
    if (kw.is_rising) metaHtml += '<span class="rising-tag">&#9650; Rising</span>';
    metaHtml += `<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">Source: ${kw.source}</span>`;
    if (kw.parent_keyword) metaHtml += `<span class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">Parent: ${kw.parent_keyword}</span>`;
    meta.innerHTML = metaHtml;

    // Categories
    const catDiv = document.getElementById('kw-categories');
    if (kw.categories && kw.categories.length > 0) {
        catDiv.innerHTML = kw.categories.map(c => `
            <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <span class="category-pill bg-indigo-100 text-indigo-700 text-sm">${c.category_name}</span>
                <span class="text-xs text-gray-500">confidence: ${(c.confidence * 100).toFixed(0)}%</span>
            </div>
        `).join('');
    }

    // Trend history chart
    loadTrendChart();
}

async function loadTrendChart() {
    const snapshots = await fetch(`/api/trends/snapshots/${KEYWORD_ID}`).then(r => r.json());
    const noDataEl = document.getElementById('no-trend-data');

    if (snapshots.length === 0) {
        noDataEl.classList.remove('hidden');
        return;
    }
    noDataEl.classList.add('hidden');

    const ctx = document.getElementById('trendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: snapshots.map(s => new Date(s.date).toLocaleDateString()),
            datasets: [{
                label: 'Trends Score',
                data: snapshots.map(s => s.score),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, max: 100 },
            },
            plugins: { legend: { display: false } },
        }
    });
}

loadKeywordDetail();
