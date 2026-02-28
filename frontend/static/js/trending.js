// Trending Now page

let trendingData = { google: [], twitter: [], reddit: [] };
let expandedTerms = new Set();

function heatClass(score) {
    if (score >= 70) return 'heat-hot';
    if (score >= 50) return 'heat-warm';
    if (score >= 30) return 'heat-mild';
    if (score >= 15) return 'heat-cool';
    return 'heat-cold';
}

// ─── Load trending sources ────────────────────────────────────────────────────

async function loadTrending() {
    document.getElementById('loading-state').classList.remove('hidden');
    document.getElementById('trending-grid').classList.remove('grid');
    document.getElementById('trending-grid').classList.add('hidden');

    try {
        const data = await fetch('/api/trends/trending-now').then(r => r.json());
        trendingData = data;
        renderTrending(data);
    } catch (e) {
        document.getElementById('loading-state').innerHTML =
            `<p class="col-span-3 text-center py-8 text-red-500">Failed to load trending data: ${e.message}</p>`;
    }

    loadRecentKeywords();
}

function renderTrending(data) {
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('trending-grid').classList.remove('hidden');
    document.getElementById('trending-grid').classList.add('grid');

    renderSource('google', data.google || []);
    renderSource('twitter', data.twitter || []);
    renderSource('reddit', data.reddit || []);
}

function renderSource(source, items) {
    const list = document.getElementById(`${source}-list`);
    const countEl = document.getElementById(`${source}-count`);
    countEl.textContent = `${items.length} topics`;

    if (items.length === 0) {
        list.innerHTML = `<div class="px-5 py-8 text-center text-gray-400 text-sm">
            No data available right now.<br><span class="text-xs">Try refreshing in a moment.</span>
        </div>`;
        return;
    }

    list.innerHTML = items.slice(0, 20).map((item, i) => {
        const isExpanded = expandedTerms.has(item.term.toLowerCase());
        const termEncoded = encodeURIComponent(item.term);
        return `
        <div class="trending-item px-4 py-3 hover:bg-gray-50 transition-colors" data-term="${escapeHtml(item.term)}">
            <div class="flex items-start gap-3">
                <span class="text-xs text-gray-300 font-mono w-5 pt-0.5 shrink-0">${i + 1}</span>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-800 truncate" title="${escapeHtml(item.term)}">${escapeHtml(item.term)}</p>
                    ${item.detail ? `<p class="text-xs text-gray-400 mt-0.5 truncate">${escapeHtml(item.detail)}</p>` : ''}
                </div>
                <button
                    onclick="expandTerm('${escapeHtml(item.term).replace(/'/g, "\\'")}')"
                    class="expand-btn shrink-0 px-2.5 py-1 text-xs rounded-lg transition-colors ${isExpanded ? 'bg-green-100 text-green-700' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'}"
                    data-term="${escapeHtml(item.term)}">
                    ${isExpanded ? '✓ Done' : 'Expand'}
                </button>
            </div>
        </div>`;
    }).join('');
}

// ─── Expand a single term ─────────────────────────────────────────────────────

async function expandTerm(term) {
    const btn = document.querySelector(`button[data-term="${CSS.escape(term)}"]`);
    if (btn) {
        btn.textContent = '...';
        btn.disabled = true;
        btn.classList.add('opacity-50');
    }

    showStatus(`Expanding "${term}"...`);

    try {
        const resp = await fetch('/api/trends/expand-trending', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify([term]),
        });
        const data = await resp.json();

        if (data.jobs && data.jobs.length > 0) {
            const jobId = data.jobs[0].job_id;
            await pollUntilDone([jobId], `"${term}"`);
        }

        expandedTerms.add(term.toLowerCase());
        if (btn) {
            btn.textContent = '✓ Done';
            btn.disabled = false;
            btn.classList.remove('opacity-50');
            btn.className = 'expand-btn shrink-0 px-2.5 py-1 text-xs rounded-lg bg-green-100 text-green-700';
        }

        loadRecentKeywords();
    } catch (e) {
        showStatus(`Error: ${e.message}`, true);
        if (btn) {
            btn.textContent = 'Retry';
            btn.disabled = false;
            btn.classList.remove('opacity-50');
        }
    }
}

// ─── Expand top 10 across all sources ────────────────────────────────────────

async function expandAll() {
    const allTerms = [];
    const seen = new Set();
    for (const source of ['google', 'twitter', 'reddit']) {
        for (const item of (trendingData[source] || []).slice(0, 5)) {
            const key = item.term.toLowerCase();
            if (!seen.has(key) && !expandedTerms.has(key)) {
                seen.add(key);
                allTerms.push(item.term);
            }
        }
    }

    const terms = allTerms.slice(0, 10);
    if (terms.length === 0) {
        showStatus('All top terms already expanded!');
        return;
    }

    const btn = document.getElementById('btn-expand-all');
    btn.disabled = true;
    btn.textContent = 'Starting...';
    showStatus(`Launching ${terms.length} expansion jobs...`);

    try {
        const resp = await fetch('/api/trends/expand-trending', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(terms),
        });
        const data = await resp.json();

        if (data.jobs) {
            const jobIds = data.jobs.map(j => j.job_id);
            // Mark all as in-progress
            for (const t of terms) {
                const btn2 = document.querySelector(`button[data-term="${CSS.escape(t)}"]`);
                if (btn2) { btn2.textContent = '...'; btn2.disabled = true; }
            }
            await pollUntilDone(jobIds, `${terms.length} trending topics`);

            for (const t of terms) {
                expandedTerms.add(t.toLowerCase());
                const btn2 = document.querySelector(`button[data-term="${CSS.escape(t)}"]`);
                if (btn2) {
                    btn2.textContent = '✓ Done';
                    btn2.disabled = false;
                    btn2.className = 'expand-btn shrink-0 px-2.5 py-1 text-xs rounded-lg bg-green-100 text-green-700';
                }
            }
            loadRecentKeywords();
        }
    } catch (e) {
        showStatus(`Error: ${e.message}`, true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Auto-Expand Top 10`;
    }
}

// ─── Poll jobs until all done ─────────────────────────────────────────────────

async function pollUntilDone(jobIds, label) {
    const maxWait = 180; // 3 min
    let attempts = 0;

    return new Promise((resolve) => {
        const interval = setInterval(async () => {
            attempts++;
            try {
                const results = await Promise.all(
                    jobIds.map(id => fetch(`/api/jobs/${id}`).then(r => r.json()))
                );
                const done = results.filter(j => j.status === 'completed' || j.status === 'failed');
                const totalFound = results.reduce((s, j) => s + (j.keywords_found || 0), 0);

                if (done.length === results.length) {
                    clearInterval(interval);
                    showStatus(`Done! Discovered ${totalFound} new keywords from ${label}`, false, true);
                    setTimeout(hideStatus, 6000);
                    resolve();
                } else {
                    const avgProgress = results.reduce((s, j) => s + (j.progress || 0), 0) / results.length;
                    showStatus(`Expanding ${label}... ${Math.round(avgProgress)}% (${done.length}/${results.length} done)`);
                }
            } catch (e) { /* keep polling */ }

            if (attempts >= maxWait / 2) {
                clearInterval(interval);
                showStatus(`Jobs still running. Check <a href="/jobs" class="underline">Jobs page</a>.`);
                resolve();
            }
        }, 2000);
    });
}

// ─── Recently discovered keywords ────────────────────────────────────────────

async function loadRecentKeywords() {
    try {
        const data = await fetch('/api/keywords?sort_by=first_seen&sort_dir=desc&page_size=20').then(r => r.json());
        if (!data.items || data.items.length === 0) return;

        document.getElementById('recent-section').classList.remove('hidden');
        const tbody = document.getElementById('recent-body');
        tbody.innerHTML = data.items.map((kw, i) => `
            <tr>
                <td class="text-xs text-gray-300">${i + 1}</td>
                <td>
                    <a href="/keywords/${kw.id}" class="text-indigo-600 hover:underline font-medium">${escapeHtml(kw.keyword)}</a>
                    ${kw.parent_keyword ? `<br><span class="text-xs text-gray-400">from: ${escapeHtml(kw.parent_keyword)}</span>` : ''}
                </td>
                <td><span class="heat-badge ${heatClass(kw.heat_score)}">${kw.heat_score}</span></td>
                <td class="text-xs text-gray-500">${kw.source}</td>
                <td>${(kw.categories || []).map(c => `<span class="category-pill bg-indigo-50 text-indigo-700">${c.category_name}</span>`).join('') || '<span class="text-xs text-gray-300">-</span>'}</td>
                <td>${kw.is_rising ? '<span class="rising-tag">&#9650; Rising</span>' : ''}</td>
            </tr>
        `).join('');
    } catch (e) { /* silently ignore */ }
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

function showStatus(msg, isError = false, isSuccess = false) {
    const bar = document.getElementById('expand-status-bar');
    const text = document.getElementById('expand-status-text');
    bar.classList.remove('hidden');
    bar.className = `mb-6 border rounded-xl p-4 flex items-center gap-3 ${
        isError ? 'bg-red-50 border-red-200' : isSuccess ? 'bg-green-50 border-green-200' : 'bg-indigo-50 border-indigo-200'
    }`;
    text.innerHTML = msg;
    text.className = `text-sm font-medium ${isError ? 'text-red-700' : isSuccess ? 'text-green-700' : 'text-indigo-700'}`;
}

function hideStatus() {
    document.getElementById('expand-status-bar').classList.add('hidden');
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ─── Init ─────────────────────────────────────────────────────────────────────
loadTrending();
