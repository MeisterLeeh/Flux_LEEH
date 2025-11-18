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
      <img src="${v.thumbnail || 'https://via.placeholder.com/480x360'}" class="thumbnail" loading="lazy">
      <h3>${v.title}</h3>
      <p>${v.author} • ${formatDuration(v.duration)}</p>

      ${v.duration > 600 ? `
        <video controls preload="none" poster="${v.thumbnail}">
          <source src="${API}/preview?id=${v.id}&type=video" type="video/mp4">
          Your browser does not support video.
        </video>` : `
        <audio controls preload="none">
          <source src="${API}/preview?id=${v.id}&type=audio" type="audio/mpeg">
          Your browser does not support audio.
        </audio>`}

      <div class="buttons">
        <button class="download-btn mp3" data-id="${v.id}">MP3</button>
        <button class="download-btn mp4" data-id="${v.id}">MP4</button>
      </div>
      <progress class="progress" value="0" max="100"></progress>
    </div>
  `).join('');

  // NEW: Simple direct download with progress (works perfectly with redirect)
  document.querySelectorAll('.download-btn').forEach(btn => {
    btn.onclick = function(e) {
      e.preventDefault();
      const videoId = this.dataset.id;
      const format = this.classList.contains('mp3') ? 'mp3' : 'mp4';
      const prog = this.parentElement.nextElementSibling;
      prog.style.display = 'block';
      prog.value = 0;

      // Create invisible iframe to trigger real download with correct filename
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = `${API}/download?id=${videoId}&format=${format}`;
      document.body.appendChild(iframe);

      // Fake progress (since we can't track real download progress on redirect)
      let fakeProgress = 0;
      const interval = setInterval(() => {
        fakeProgress += 8;
        prog.value = fakeProgress;
        if (fakeProgress >= 95) {
          clearInterval(interval);
          setTimeout(() => {
            prog.style.display = 'none';
            prog.value = 0;
          }, 2000);
        }
      }, 200);

      // Clean up iframe after 10s
      setTimeout(() => iframe.remove(), 10000);
    };
  });
}

function formatDuration(seconds) {
  if (!seconds) return 'LIVE';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// Dark mode & search
document.getElementById('toggle-mode').onclick = () => {
  document.body.classList.toggle('light-mode');
};

document.getElementById('searchInput').addEventListener('keypress', e => {
  if (e.key === 'Enter') search();
});

document.addEventListener('DOMContentLoaded', loadTrending);