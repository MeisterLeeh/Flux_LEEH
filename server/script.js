const API = location.origin; // This fixes "Backend not running!"

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
        </video>` : `
        <audio controls preload="none">
          <source src="${API}/preview?id=${v.id}&type=audio" type="audio/mpeg">
        </audio>`}

      <div class="buttons">
        <a href="${API}/download?id=${v.id}&format=mp3" class="download-btn">MP3</a>
        <a href="${API}/download?id=${v.id}&format=mp4" class="download-btn">MP4</a>
      </div>
      <progress class="progress" value="0" max="100"></progress>
    </div>
  `).join('');

  // Progress bar for downloads
  document.querySelectorAll('.download-btn').forEach(btn => {
    btn.onclick = e => {
      e.preventDefault();
      const prog = btn.parentElement.nextElementSibling;
      prog.style.display = 'block';
      prog.value = 0;

      const xhr = new XMLHttpRequest();
      xhr.open('GET', btn.href, true);
      xhr.responseType = 'blob';

      xhr.onprogress = ev => {
        if (ev.lengthComputable) prog.value = (ev.loaded / ev.total) * 100;
      };

      xhr.onload = () => {
        const url = URL.createObjectURL(xhr.response);
        const a = document.createElement('a');
        a.href = url;
        a.download = btn.textContent === 'MP3' ? `${btn.closest('.result').querySelector('h3').textContent}.mp3` 
                                               : `${btn.closest('.result').querySelector('h3').textContent}.mp4`;
        a.click();
        prog.style.display = 'none';
      };

      xhr.send();
    };
  });
}

function formatDuration(seconds) {
  if (!seconds) return 'LIVE';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// Dark mode toggle
document.getElementById('toggle-mode').onclick = () => {
  document.body.classList.toggle('light-mode');
};

// Enter key search
document.getElementById('searchInput').addEventListener('keypress', e => {
  if (e.key === 'Enter') search();
});

document.addEventListener('DOMContentLoaded', loadTrending);