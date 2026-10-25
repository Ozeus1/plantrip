let resetPasswordUser=null;
function renderPasswordPage(){
  if($('#tripNotice'))$('#tripNotice').hidden=true;
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.view==='password'));
  $('#breadcrumb').textContent='Minha conta / Minha senha';$('#pageTitle').textContent='Sua conta, sua senha.';
  $('#pageSubtitle').textContent='Altere a senha usada para entrar nas suas viagens.';$('#add').hidden=true;
  const min=state.user.role==='admin'?8:5;
  $('#content').innerHTML=`<section class="panel password-panel"><h2>Alterar minha senha</h2><p>Após a alteração, você precisará entrar novamente em todos os dispositivos.</p><form id="passwordForm"><label>Senha atual<input name="current_password" type="password" autocomplete="current-password" required maxlength="128"></label><label>Nova senha<input name="new_password" type="password" autocomplete="new-password" required minlength="${min}" maxlength="128"><small>Pelo menos ${min} caracteres.</small></label><label>Confirmar nova senha<input name="confirmation" type="password" autocomplete="new-password" required minlength="${min}" maxlength="128"></label><p class="error" id="passwordError" role="alert"></p><button class="primary" id="passwordSave">Salvar nova senha</button></form></section>`;
  $('#passwordForm').onsubmit=async ev=>{
    ev.preventDefault();const f=ev.target,b=$('#passwordSave');$('#passwordError').textContent='';
    if(f.elements.new_password.value!==f.elements.confirmation.value){$('#passwordError').textContent='A confirmação da nova senha não confere.';return}
    b.disabled=true;
    try{await api('/api/account/password',Object.fromEntries(new FormData(f)));f.reset();publicLoginRequested=true;selectedTrip='';localStorage.removeItem('plantrip-trip');leaveAttraction();if(location.pathname==='/diary')history.replaceState({},'','/');await load();$('#authForm input[name=password]').value='';toast('Senha alterada. Entre novamente com a nova senha.')}
    catch(ex){$('#passwordError').textContent=ex.message;b.disabled=false}
  };
}
function openResetPassword(user){
  resetPasswordUser=user;$('#resetPasswordTarget').textContent=user.name+' · '+user.email;
  $('#generatedPassword').textContent='';$('#resetPasswordResult').hidden=true;$('#resetPasswordError').textContent='';$('#resetPasswordGenerate').hidden=false;$('#resetPasswordGenerate').disabled=false;$('#resetPasswordDialog').showModal();
}
function bindPasswordResetButtons(){document.querySelectorAll('[data-reset-password]').forEach(b=>b.onclick=()=>openResetPassword(state.users.find(u=>u.id===Number(b.dataset.resetPassword))));document.querySelectorAll('[data-own-password]').forEach(b=>b.onclick=()=>go('password'))}
function initPasswordControls(){
  $('#resetPasswordForm').onsubmit=async ev=>{
    ev.preventDefault();if(!resetPasswordUser)return;
    const b=$('#resetPasswordGenerate');b.disabled=true;$('#resetPasswordError').textContent='';
    try{const result=await api('/api/users/reset-password',{user_id:resetPasswordUser.id});$('#generatedPassword').textContent=result.password;$('#resetPasswordResult').hidden=false;b.hidden=true;const updated=await api('/api/state'+(selectedTrip?'?trip_id='+selectedTrip:''));state.password_requests=updated.password_requests;recoveryBadge();if(view==='users')renderManagement();toast('Nova senha gerada. As sessões anteriores foram encerradas.')}
    catch(ex){$('#resetPasswordError').textContent=ex.message;b.disabled=false}
  };
  $('#copyGeneratedPassword').onclick=async()=>{try{await navigator.clipboard.writeText($('#generatedPassword').textContent);toast('Senha copiada. Compartilhe diretamente com o usuário.')}catch{toast('Selecione a senha exibida e copie manualmente.')}};
  $('#resetPasswordDialog').addEventListener('close',()=>{$('#generatedPassword').textContent='';resetPasswordUser=null});
}
