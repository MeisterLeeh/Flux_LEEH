const API = location.origin;

async function search() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;
    const container = document.getElementById('results');
    container.innerHTML = '<p class="loading">Searching...</p>';
    try {
        const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        renderResults(data.results || []);
    } catch (err) {
        container.innerHTML = '<p class="loading">Search failed. Try again.</p>';
    }
}

function renderResults(videos) {
    const container = document.getElementById('results');
    if (!videos.length) {
        container.innerHTML = '<p class="loading">No results found.</p>';
        return;
    }
    container.innerHTML = videos.map(v => `
        <div class="result">
            <img src="${v.thumbnail}" class="thumbnail" alt="thumb">
            <h3>${escapeHtml(v.title)}</h3>
            <p>${escapeHtml(v.author)} • ${formatDuration(v.duration)}</p>
            <div class="buttons">
                <a href="${API}/download?id=${v.id}&format=mp3" class="download-btn mp3">MP3</a>
                <a href="${API}/download?id=${v.id}&format=mp4" class="download-btn mp4">MP4</a>
                <a href="https://www.youtube.com/watch?v=${v.id}" target="_blank" class="download-btn">Preview</a>
            </div>
        </div>
    `).join('');
}

function renderTrending(videos) {
    const container = document.getElementById('trending-results');
    if (!videos.length) {
        container.innerHTML = '<p class="loading">No trending items.</p>';
        return;
    }
    container.innerHTML = videos.map(v => `
        <div class="result">
            <img src="${v.thumbnail}" class="thumbnail" alt="thumb">
            <h3>${escapeHtml(v.title)}</h3>
            <p>${escapeHtml(v.author)} • ${formatDuration(v.duration)}</p>
            <div class="buttons">
                <a href="${API}/download?id=${v.id}&format=mp3" class="download-btn mp3">MP3</a>
                <a href="${API}/download?id=${v.id}&format=mp4" class="download-btn mp4">MP4</a>
                <a href="https://www.youtube.com/watch?v=${v.id}" target="_blank" class="download-btn">Preview</a>
            </div>
        </div>
    `).join('');
}

function formatDuration(sec) {
    if (!sec) return "LIVE";
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2,'0')}`;
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>"']/g, function (c) {
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c];
    });
}

// Enter key
const input = document.getElementById('searchInput');
if (input) {
    input.addEventListener('keypress', e => {
        if (e.key === 'Enter') search();
    });
}

// Trending load
fetch(`${API}/trending`).then(r => r.json()).then(d => renderTrending(d.results || [])).catch(()=>{});

// Theme toggle (keeps your existing UI behaviour)
const toggle = document.getElementById('toggle-mode');
if (toggle) {
    toggle.addEventListener('click', () => {
        document.body.classList.toggle('light-mode');
        toggle.textContent = document.body.classList.contains('light-mode') ? '☀️' : '🌙';
    });
}
