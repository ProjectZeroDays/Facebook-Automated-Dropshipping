const b64u = {
  toBuf: s => { s = s.replace(/-/g,'+').replace(/_/g,'/'); s += '='.repeat((4-s.length%4)%4);
    const b = atob(s); const u = new Uint8Array(b.length);
    for (let i=0;i<b.length;i++) u[i]=b.charCodeAt(i); return u.buffer; },
  fromBuf: b => btoa(String.fromCharCode(...new Uint8Array(b)))
    .replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'')
};

async function waRegister(label){
  try{
    const opts = await fetch('/auth/passkey/register/begin',{method:'POST'}).then(r=>r.json());
    opts.challenge = b64u.toBuf(opts.challenge);
    opts.user.id   = b64u.toBuf(opts.user.id);
    (opts.excludeCredentials||[]).forEach(c => c.id = b64u.toBuf(c.id));
    const cred = await navigator.credentials.create({publicKey: opts});
    const payload = {
      id: cred.id, rawId: b64u.fromBuf(cred.rawId), type: cred.type,
      response: {
        clientDataJSON: b64u.fromBuf(cred.response.clientDataJSON),
        attestationObject: b64u.fromBuf(cred.response.attestationObject)
      },
      label: label || (navigator.platform || 'device')
    };
    return await fetch('/auth/passkey/register/finish',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}).then(r=>r.json());
  }catch(e){ return {ok:false, error:String(e)}; }
}

async function waLogin(email){
  const begin = await fetch('/auth/passkey/login/begin',{method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify({email})}).then(r=>r.json());
  if (begin.error) return {ok:false, error:begin.error};
  const opts = begin.options;
  opts.challenge = b64u.toBuf(opts.challenge);
  (opts.allowCredentials||[]).forEach(c => c.id = b64u.toBuf(c.id));
  const cred = await navigator.credentials.get({publicKey: opts});
  const payload = {
    id: cred.id, rawId: b64u.fromBuf(cred.rawId), type: cred.type,
    response: {
      clientDataJSON: b64u.fromBuf(cred.response.clientDataJSON),
      authenticatorData: b64u.fromBuf(cred.response.authenticatorData),
      signature: b64u.fromBuf(cred.response.signature),
      userHandle: cred.response.userHandle ? b64u.fromBuf(cred.response.userHandle) : null
    }
  };
  return await fetch('/auth/passkey/login/finish',{method:'POST',
    headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}).then(r=>r.json());
}
