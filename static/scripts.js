const API = location.origin;

async function loadTrending(){
  const el = document.getElementById('trending-results');
  el.innerHTML = '<p class="loading">Loading...</p>';
  try{
    const r = await fetch(`${API}/trending`);
    const d = await r.json();
    renderList(d.results||[], el);
  }catch(e){ el.innerHTML='<p class="loading">Failed to load</p>' }
}

async function doSearch(q){
  const el = document.getElementById('results');
  el.innerHTML = '<p class="loading">Searching...</p>';
  try{
    const r = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
    const d = await r.json();
    renderList(d.results||[], el);
  }catch(e){ el.innerHTML='<p class="loading">Search failed</p>' }
}

function renderList(items, container){
  if(!items.length){ container.innerHTML='<p class="loading">No results.</p>'; return }
  container.innerHTML = items.map(i=>`
    <div class="result">
      <img class="thumbnail" src="${i.thumbnail}" alt="thumb">
      <h3>${escape(i.title)}</h3>
      <p>${escape(i.author)} • ${formatDuration(i.duration)}</p>
      <div class="buttons">
        <a class="download-btn" href="${API}/download?id=${i.id}&format=mp3">MP3</a>
        <a class="download-btn" href="${API}/download?id=${i.id}&format=mp4">MP4</a>
        <a class="download-btn" target="_blank" href="https://www.youtube.com/watch?v=${i.id}">Preview</a>
      </div>
    </div>
  `).join('')
}

function formatDuration(sec){ if(!sec) return 'LIVE'; const m=Math.floor(sec/60); const s=sec%60; return `${m}:${s.toString().padStart(2,'0')}` }
function escape(s){ return (s||'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'})[c]) }

document.getElementById('searchBtn').addEventListener('click',()=>{const q=document.getElementById('searchInput').value.trim(); if(q) doSearch(q)})
document.getElementById('searchInput').addEventListener('keypress',e=>{ if(e.key==='Enter') document.getElementById('searchBtn').click() })

loadTrending();
