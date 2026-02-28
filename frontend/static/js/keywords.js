// Keyword Discovery page

function heatClass(score) {
    if (score >= 70) return 'heat-hot';
    if (score >= 50) return 'heat-warm';
    if (score >= 30) return 'heat-mild';
    if (score >= 15) return 'heat-cool';
    return 'heat-cold';
}

// Preset seed buttons
document.querySelectorAll('.seed-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.getElementById('seed-input').value = btn.dataset.seed;
    });
});

// Expansion form
document.getElementById('expand-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const seed = document.getElementById('seed-input').value.trim();
    if (!seed) return;

    const depth = parseInt(document.getElementById('depth-select').value);
    const useAutocomplete = document.getElementById('use-autocomplete').checked;
    const useTrends = document.getElementById('use-trends').checked;
    const useSerp = document.getElementById('use-serp').checked;

    const btn = document.getElementById('expand-btn');
    const status = document.getElementById('expand-status');
    const statusText = document.getElementById('expand-status-text');

    btn.disabled = true;
    btn.textContent = 'Expanding...';
    status.classList.remove('hidden');
    statusText.textContent = 'Starting expansion job...';

    try {
        const resp = await fetch('/api/keywords/expand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                seed_keyword: seed,
                depth: depth,
                use_autocomplete: useAutocomplete,
                use_trends: useTrends,
                use_serp: useSerp,
            }),
        });
        const data = await resp.json();

        if (data.job_id) {
            statusText.textContent = `Job #${data.job_id} started. Polling for results...`;
            pollAndShowResults(data.job_id, seed);
        }
    } catch (err) {
        statusText.textContent = 'Error: ' + err.message;
        btn.disabled = false;
        btn.textContent = 'Expand Keywords';
    }
});

async function pollAndShowResults(jobId, seed) {
    const statusText = document.getElementById('expand-status-text');
    const btn = document.getElementById('expand-btn');
    const status = document.getElementById('expand-status');

    let attempts = 0;
    const maxAttempts = 120; // 2 minutes max

    const poll = setInterval(async () => {
        attempts++;
        try {
            const job = await fetch(`/api/jobs/${jobId}`).then(r => r.json());

            if (job.status === 'completed') {
                clearInterval(poll);
                statusText.textContent = `Done! Found ${job.keywords_found} new keywords.`;
                btn.disabled = false;
                btn.textContent = 'Expand Keywords';
                loadResults(seed);
                setTimeout(() => status.classList.add('hidden'), 5000);
            } else if (job.status === 'failed') {
                clearInterval(poll);
                statusText.textContent = `Failed: ${job.error_message || 'Unknown error'}`;
                btn.disabled = false;
                btn.textContent = 'Expand Keywords';
            } else {
                statusText.textContent = `Running... ${Math.round(job.progress)}%`;
            }
        } catch (e) {
            // Job might not be tracked yet, keep polling
        }

        if (attempts >= maxAttempts) {
            clearInterval(poll);
            statusText.textContent = 'Job is taking longer than expected. Check the Jobs page.';
            btn.disabled = false;
            btn.textContent = 'Expand Keywords';
            // Still try to show any results
            loadResults(seed);
        }
    }, 2000);
}

async function loadResults(seed) {
    const section = document.getElementById('results-section');
    const tbody = document.getElementById('results-body');
    const countEl = document.getElementById('result-count');

    const resp = await fetch(`/api/keywords?parent_keyword=${encodeURIComponent(seed)}&page_size=100&sort_by=heat_score&sort_dir=desc`);
    const data = await resp.json();

    section.classList.remove('hidden');
    countEl.textContent = `${data.total} keywords found`;

    if (data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-400">No keywords found yet. The job may still be running.</td></tr>';
        return;
    }

    tbody.innerHTML = data.items.map(kw => `
        <tr>
            <td><a href="/keywords/${kw.id}" class="text-indigo-600 hover:underline font-medium">${kw.keyword}</a></td>
            <td><span class="heat-badge ${heatClass(kw.heat_score)}">${kw.heat_score}</span></td>
            <td class="text-xs text-gray-500">${kw.source}</td>
            <td>${(kw.categories || []).map(c => `<span class="category-pill bg-indigo-50 text-indigo-700">${c.category_name}</span>`).join('')}</td>
            <td>${kw.is_rising ? '<span class="rising-tag">&#9650; Rising</span>' : ''}</td>
        </tr>
    `).join('');
}
