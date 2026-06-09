// Frontend chat logic (minimal)
(function(){
  const BACKEND = 'http://localhost:8000'; // edit if needed

  function $(id){return document.getElementById(id)}

  async function loadSessions(){
    const user = AppFirebase.currentUser();
    if(!user) { window.location.href='index.html'; return }
    const res = await fetch(`${BACKEND}/sessions/${user.uid}`);
    const sessions = await res.json();
    const container = $('sessions');
    container.innerHTML='';
    sessions.forEach(s => {
      const el = document.createElement('div');
      el.className='session-item';
      el.textContent = s.title || s.id;
      el.dataset.id = s.id;
      el.addEventListener('click', ()=> loadMessages(s.id));
      container.appendChild(el);
    });
  }

  async function loadMessages(sessionId){
    const res = await fetch(`${BACKEND}/sessions/${sessionId}/messages`);
    const msgs = await res.json();
    const box = $('messages');
    box.innerHTML = '';
    msgs.forEach(m => {
      const div = document.createElement('div');
      div.className = m.role === 'user' ? 'msg user' : 'msg ai';
      div.textContent = m.content;
      box.appendChild(div);
    })
  }

  async function sendMessage(e){
    e.preventDefault();
    const text = $('input').value.trim();
    if(!text) return;
    const user = AppFirebase.currentUser();
    // get or create session — naive: use first session
    const res = await fetch(`${BACKEND}/sessions/${user.uid}`);
    const sessions = await res.json();
    let sessionId = sessions.length ? sessions[0].id : null;
    if(!sessionId){
      const r = await fetch(`${BACKEND}/sessions/new`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:user.uid, title:'New Chat'})});
      const data = await r.json(); sessionId = data.session_id;
      await loadSessions();
    }

    // optimistic UI
    const box = $('messages');
    const udiv = document.createElement('div'); udiv.className='msg user'; udiv.textContent = text; box.appendChild(udiv);
    $('input').value='';

    const payload = { session_id: sessionId, user_id: user.uid, message: text, history: [] };
    const r2 = await fetch(`${BACKEND}/chat/message`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const j = await r2.json();
    const adiv = document.createElement('div'); adiv.className='msg ai'; adiv.textContent = j.response; box.appendChild(adiv);
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    AppFirebase.onAuthStateChanged(user=>{
      if(!user) window.location.href='index.html';
      else loadSessions();
    });
    $('composer').addEventListener('submit', sendMessage);
    $('newSession').addEventListener('click', async ()=>{
      const user = AppFirebase.currentUser();
      if(!user) return;
      await fetch(`${BACKEND}/sessions/new`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:user.uid, title:'New Chat'})});
      loadSessions();
    })
  })
})();
