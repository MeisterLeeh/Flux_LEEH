const API = location.origin;

async function search() {
  const q = document.getElementById('searchInput').value.trim();
  if (!q) return;
  const container = document.getElementById('results');
  container.innerHTML = '<p class="loading">Searching...</p>';
  try {
    const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.results || data.results.length === 0) {
      container.innerHTML = '<p>No results found.</p>';
      return;
    }
    renderResults(data.results);
  } catch (e) {
    container.innerHTML = '<p style="color:red">Search failed. Try again.</p>';
  }
}

async function loadTrending() {
  const container = document.getElementById('trending-results');
  container.innerHTML = '<p class="loading">Loading SA bangers...</p>';
  try {
    const res = await fetch(`${API}/trending`);
    const data = await res.json();
    if (data.results && data.results.length > 0) {
      renderResults(data.results, container);
    } else {
      container.innerHTML = '<p>Trending unavailable right now.</p>';
    }
  } catch (e) {
    container.innerHTML = '<p>Trending failed to load.</p>';
  }
}

function renderResults(videos, container = document.getElementById('results')) {
  container.innerHTML = videos.map(v => `
    <div class="result">
      <img src="${v.thumbnail}" class="thumbnail" loading="lazy">
      <h3>${v.title}</h3>
      <p>${v.author} • ${formatDuration(v.duration)}</p>
      ${v.duration > 600 ? `
        <video controls preload="metadata" poster="${v.thumbnail}">
          <source src="${API}/preview?id=${v.id}&type=video" type="video/mp4">
        </video>` : `
        <audio controls preload="metadata">
          <source src="${API}/preview?id=${v.id}&type=audio" type="audio/mpeg">
        </audio>`}
      <div class="buttons">
        <a href="${API}/download?id=${v.id}&format=mp3" download class="download-btn mp3">MP3</a>
        <a href="${API}/download?id=${v.id}&format=mp4" download class="download-btn mp4">MP4</a>
      </div>
    </div>
  `).join('');

  // NO MORE IFRAME TRICK — JUST DIRECT <a download> LINKS
  // This is the only way that works reliably in 2025
}

function formatDuration(seconds) {
  if (!seconds) return 'LIVE';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

document.getElementById('toggle-mode').onclick = () => {
  document.body.classList.toggle('light-mode');
};

document.getElementById('searchInput').addEventListener('keypress', e => {
  if (e.key === 'Enter') search();
});

document.addEventListener('DOMContentLoaded', loadTrending);