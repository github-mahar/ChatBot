// Dashboard logic: fetch analytics and render charts using Chart.js
(function(){
  const BACKEND = 'http://localhost:8000'; // edit if needed

  function $(id){return document.getElementById(id)}

  function renderStats(data){
    const el = $('stats');
    el.innerHTML = `<div class="card">Total Sessions: ${data.total_sessions}</div><div class="card">Total Messages: ${data.total_messages}</div><div class="card">Positive: ${data.positive_feedback}</div><div class="card">Negative: ${data.negative_feedback}</div>`;
  }

  function renderCharts(data){
    const labels = data.messages_per_day.map(d=>d.date);
    const counts = data.messages_per_day.map(d=>d.count);
    const ctx = $('messagesChart').getContext('2d');
    new Chart(ctx, {type:'line', data:{labels, datasets:[{label:'Messages per day', data:counts, borderColor:'#6366f1', backgroundColor:'rgba(99,102,241,0.2)'}]}});

    const fbCtx = $('feedbackChart').getContext('2d');
    new Chart(fbCtx, {type:'bar', data:{labels:['Positive','Negative'], datasets:[{label:'Feedback', data:[data.positive_feedback, data.negative_feedback], backgroundColor:['#10B981','#EF4444']}]}});
  }

  async function load(){
    const user = AppFirebase.currentUser();
    if(!user) { window.location.href='index.html'; return }
    const res = await fetch(`${BACKEND}/analytics/${user.uid}`);
    const data = await res.json();
    renderStats(data);
    renderCharts(data);
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    AppFirebase.onAuthStateChanged(user=>{ if(user) load(); else window.location.href='index.html' });
  })
})();
