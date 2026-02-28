// Keyword Browse/List page

let currentPage = 1;
const pageSize = 50;

function heatClass(score) {
    if (score >= 70) return 'heat-hot';
    if (score >= 50) return 'heat-warm';
    if (score >= 30) return 'heat-mild';
    if (score >= 15) return 'heat-cool';
    return 'heat-cold';
}

async function loadKeywords() {
    const search = document.getElementById('filter-search').value;
    const category = document.getElementById('filter-category').value;
    const sortBy = document.getElementById('filter-sort').value;
    const risingOnly = document.getElementById('filter-rising').checked;

    const params = new URLSearchParams({
        page: currentPage,
        page_size: pageSize,
        sort_by: sortBy,
        sort_dir: 'desc',
    });
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    if (risingOnly) params.append('rising_only', 'true');

    const data = await fetch(`/api/keywords?${params}`).then(r => r.json());
    const tbody = document.getElementById('keywords-body');

    if (data.items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-8 text-gray-400">No keywords found. Start by discovering keywords.</td></tr>';
        document.getElementById('pagination-info').textContent = '';
        document.getElementById('pagination-controls').innerHTML = '';
        return;
    }

    tbody.innerHTML = data.items.map(kw => `
        <tr>
            <td>
                <a href="/keywords/${kw.id}" class="text-indigo-600 hover:underline font-medium">${kw.keyword}</a>
                ${kw.parent_keyword ? `<br><span class="text-xs text-gray-400">from: ${kw.parent_keyword}</span>` : ''}
            </td>
            <td><span class="heat-badge ${heatClass(kw.heat_score)}">${kw.heat_score}</span></td>
            <td>${kw.trends_score > 0 ? kw.trends_score.toFixed(1) : '-'}</td>
            <td class="text-xs text-gray-500">${kw.source}</td>
            <td>${(kw.categories || []).map(c => `<span class="category-pill bg-indigo-50 text-indigo-700">${c.category_name}</span>`).join('') || '<span class="text-xs text-gray-300">-</span>'}</td>
            <td>${kw.is_rising ? '<span class="rising-tag">&#9650; Rising</span>' : ''}</td>
            <td class="text-xs text-gray-500">${new Date(kw.first_seen).toLocaleDateString()}</td>
        </tr>
    `).join('');

    // Pagination
    const totalPages = Math.ceil(data.total / pageSize);
    document.getElementById('pagination-info').textContent = `Showing ${(currentPage - 1) * pageSize + 1}-${Math.min(currentPage * pageSize, data.total)} of ${data.total}`;

    let paginationHtml = '';
    if (currentPage > 1) {
        paginationHtml += `<button onclick="goToPage(${currentPage - 1})" class="px-3 py-1 text-sm border rounded hover:bg-gray-50">&laquo; Prev</button>`;
    }
    paginationHtml += `<span class="px-3 py-1 text-sm text-gray-500">Page ${currentPage} of ${totalPages}</span>`;
    if (currentPage < totalPages) {
        paginationHtml += `<button onclick="goToPage(${currentPage + 1})" class="px-3 py-1 text-sm border rounded hover:bg-gray-50">Next &raquo;</button>`;
    }
    document.getElementById('pagination-controls').innerHTML = paginationHtml;
}

function goToPage(page) {
    currentPage = page;
    loadKeywords();
}

// Load categories for filter dropdown
async function loadCategoryFilter() {
    const stats = await fetch('/api/dashboard/stats').then(r => r.json());
    const select = document.getElementById('filter-category');
    if (stats.category_distribution) {
        stats.category_distribution.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat.name;
            opt.textContent = `${cat.display_name} (${cat.count})`;
            select.appendChild(opt);
        });
    }

    // Check URL params for initial category
    const params = new URLSearchParams(window.location.search);
    if (params.get('category')) {
        select.value = params.get('category');
    }
}

// Filter event listeners
let debounceTimer;
document.getElementById('filter-search').addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => { currentPage = 1; loadKeywords(); }, 300);
});
document.getElementById('filter-category').addEventListener('change', () => { currentPage = 1; loadKeywords(); });
document.getElementById('filter-sort').addEventListener('change', () => { currentPage = 1; loadKeywords(); });
document.getElementById('filter-rising').addEventListener('change', () => { currentPage = 1; loadKeywords(); });

loadCategoryFilter().then(loadKeywords);
