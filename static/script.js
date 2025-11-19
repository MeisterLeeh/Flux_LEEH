const API = location.origin;

async function search() {
    const q = document.getElementById('searchInput').value.trim();
    if (!q) return;
    const container = document.getElementById('results');
    container.innerHTML = '<p class="loading">Searching...</p>';
    const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    renderResults(data.results || []);
}

function renderResults(videos) {
    const container = document.getElementById('results');
    container.innerHTML = videos.map(v => `
        <div class="result">
            <img src="${v.thumbnail}" class="thumbnail">
            <h3>${v.title}</h3>
            <p>${v.author} • ${formatDuration(v.duration)}</p>
            <video controls preload="metadata" poster="${v.thumbnail}">
                <source src="${API}/preview?id=${v.id}" type="video/mp4">
            </video>
            <div class="buttons">
                <a href="${API}/download?id=${v.id}&format=mp3" download class="download-btn mp3">MP3</a>
                <a href="${API}/download?id=${v.id}&format=mp4" download class="download-btn mp4">MP4</a>
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

document.getElementById('searchInput').addEventListener('keypress', e => {
    if (e.key === 'Enter') search();
});

fetch(`${API}/trending`).then(r => r.json()).then(d => renderResults(d.results || []));