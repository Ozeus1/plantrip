function recoveryBadge(){const n=state.password_requests?.length||0;$('#usersNav span').textContent='Usuários'+(n?' ('+n+')':'')}
function recoveryRequestsHtml(){
  const requests=state.password_requests||[];if(!requests.length)return '';
  return `<section class="panel recovery-requests"><span class="eyebrow">AVISOS PARA O ADMINISTRADOR</span><h2>Solicitações de nova senha <span class="tag">${requests.length} pendentes</span></h2><p>O usuário pediu ajuda pelo login. Gere uma senha e entregue diretamente a ele.</p>${requests.map(r=>`<div class="recovery-request"><div><strong>${esc(r.name)}</strong><p>${esc(r.email)} · ${date(r.created)} ${time(r.created)}</p></div><div>${r.user_id!==state.user.id?`<button class="primary" data-recovery-user="${r.user_id}">Gerar senha provisória</button>`:''}<button class="text-btn" data-resolve-request="${r.id}">Marcar como atendida</button></div></div>`).join('')}</section>`;
}
function bindRecoveryRequests(){
  document.querySelectorAll('[data-recovery-user]').forEach(b=>b.onclick=()=>openResetPassword(state.users.find(u=>u.id===Number(b.dataset.recoveryUser))));
  document.querySelectorAll('[data-resolve-request]').forEach(b=>b.onclick=async()=>{b.disabled=true;try{await api('/api/password-requests/resolve',{request_id:Number(b.dataset.resolveRequest)});await load()}catch(ex){toast(ex.message);b.disabled=false}});
}
function initRecoveryControls(){
  $('#toggleLoginPassword').onclick=()=>{const input=$('#authForm input[name=password]'),show=input.type==='password';input.type=show?'text':'password';$('#toggleLoginPassword').textContent=show?'Ocultar senha':'Mostrar senha';$('#toggleLoginPassword').setAttribute('aria-pressed',String(show))};
  $('#forgotPassword').onclick=()=>{const f=$('#recoveryForm');f.reset();f.elements.email.value=$('#authForm input[name=email]').value;$('#recoveryError').textContent='';$('#recoveryFeedback').textContent='';$('#recoverySend').disabled=false;$('#recoveryDialog').showModal()};
  $('#recoveryForm').onsubmit=async ev=>{ev.preventDefault();const b=$('#recoverySend');b.disabled=true;$('#recoveryError').textContent='';try{const result=await api('/api/password-requests',{email:ev.target.elements.email.value});$('#recoveryFeedback').textContent=result.message;ev.target.reset()}catch(ex){$('#recoveryError').textContent=ex.message;b.disabled=false}};
}
