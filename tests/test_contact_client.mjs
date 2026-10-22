import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const source=readFileSync(new URL('../website.js',import.meta.url),'utf8');
const start=source.indexOf("const form=document.querySelector('#request-form');");
const end=source.indexOf('// Same-page enquiries',start);
assert.ok(start>=0&&end>start,'Contact implementation must be present');
const contactSource=source.slice(start,end);
const flush=async()=>{for(let index=0;index<40;index++)await Promise.resolve();};

class Element{
 constructor(value=''){this.value=value;this.disabled=false;this.dataset={};this.listeners={};this.children=[];this.attributes={};this.textContent='';}
 addEventListener(name,callback){(this.listeners[name]??=[]).push(callback);}
 removeEventListener(name,callback){this.listeners[name]=(this.listeners[name]||[]).filter(listener=>listener!==callback);}
 dispatch(name){for(const listener of [...this.listeners[name]||[]])listener();}
 setAttribute(name,value){this.attributes[name]=value;}
 removeAttribute(name){delete this.attributes[name];}
 setCustomValidity(){}
 replaceChildren(...children){this.children=children;}
 append(...children){this.children.push(...children);}
 remove(){this.removed=true;}
 focus(){}
}

function fixture(fetchReply,{translate=message=>message,scriptOutcome='load',width=340,language='et',hostname='localhost'}={}){
 let now=100000,timerId=0;
 const timers=new Map(),calls=[],controllers=[];
 const elements=Object.fromEntries(['service','name','contact_method','phone','email','location','timing','description','_honey'].map(name=>[name,new Element()]));
 Object.assign(elements.service,{value:'Двери',options:[{value:'Двери'}]});
 elements.name.value='Test customer';elements.contact_method.value='По телефону';elements.phone.value='+372 555 1234';
 elements.email.value='customer@example.test';elements.location.value='Tallinn';elements.timing.value='Пока не определился';elements.description.value='A synthetic enquiry.';
 const form=new Element(),button=new Element(),status=new Element(),picker=new Element(),fileList=new Element(),fileStatus=new Element();
 const captchaBox=new Element(),captchaHost=new Element(),captchaStatus=new Element(),captchaRetry=new Element();
 captchaBox.hidden=true;captchaRetry.hidden=true;captchaHost.clientWidth=width;
 const contactRadios=[new Element(),new Element()];
 form.elements=elements;form.querySelector=()=>button;
 form.querySelectorAll=()=>contactRadios;form.reportValidity=()=>true;
 form.reset=()=>{form.resetCalled=true;elements.description.value='';};
 const nodes={'#request-form':form,'#form-status':status,'#phone-reply-field':new Element(),'#email-reply-field':new Element(),'#attachments':picker,'#attachment-list':fileList,'#attachment-status':fileStatus,
  '#contact-captcha':captchaBox,'#contact-captcha-widget':captchaHost,'#captcha-status':captchaStatus,'#captcha-retry':captchaRetry};
 const browser=new Element(),scripts=[],widgets=[],resets=[],removedWidgets=[];
 const provider={
  ready:callback=>callback(),
  render:(host,options)=>{const id='widget-'+widgets.length;widgets.push({id,host,options});return id;},
  reset:id=>resets.push(id),remove:id=>removedWidgets.push(id),
 };
 class Data{
  constructor(){this.values=Object.entries(elements).filter(([,element])=>!element.disabled).map(([name,element])=>[name,element.value]);}
  append(name,value){this.values.push([name,value]);}
  set(name,value){this.values=this.values.filter(([key])=>key!==name);this.append(name,value);}
  get(name){return this.values.find(([key])=>key===name)?.[1];}
  getAll(name){return this.values.filter(([key])=>key===name).map(([,value])=>value);}
 }
 class Controller extends AbortController{constructor(){super();controllers.push(this);}}
 const context={
  document:{querySelector:selector=>nodes[selector],createElement:()=>new Element(),head:{append:script=>{
   scripts.push(script);
   const outcome=scriptOutcome;
   if(outcome!=='hang')Promise.resolve().then(()=>{if(outcome==='load'){browser.turnstile=provider;script.dispatch('load');}else script.dispatch('error');});
  }}},location:{search:'',hostname},window:browser,pageLanguage:language,
  t:translate,showFormFeedback:(node,message,state='info')=>{node.textContent=translate(message);node.dataset.state=state;},
  FormData:Data,AbortController:Controller,Date:{now:()=>now},URLSearchParams,
  setTimeout:(callback,delay)=>{const id=++timerId;timers.set(id,{callback,at:now+delay});return id;},
  clearTimeout:id=>timers.delete(id),
  fetch:(url,options={})=>{const call={url,options,at:now};calls.push(call);return fetchReply(call,calls);},
 };
 vm.runInNewContext(contactSource,context,{filename:'website.js contact form'});
 return {
  calls,controllers,elements,form,button,status,picker,fileList,fileStatus,captchaBox,captchaHost,captchaStatus,captchaRetry,scripts,widgets,resets,removedWidgets,
  scriptOutcome:value=>{scriptOutcome=value;},
  solve:(value='challenge-token',index=widgets.length-1)=>widgets[index].options.callback(value),
  expire:()=>widgets.at(-1).options['expired-callback'](),
  failCaptcha:()=>widgets.at(-1).options['error-callback'](),
  retryCaptcha:()=>captchaRetry.listeners.click[0](),
  resizeCaptcha:value=>{captchaHost.clientWidth=value;browser.dispatch('resize');},
  selectContact:value=>{elements.contact_method.value=value;contactRadios[0].listeners.change[0]();},
  submit:()=>form.listeners.submit[0]({preventDefault(){}}),
  attach:files=>{picker.files=files;picker.listeners.change[0]();},
  async tick(ms){
   await flush();const target=now+ms;
   while(true){
    const pending=[...timers.entries()].filter(([,timer])=>timer.at<=target).sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];
    if(!pending)break;
    now=pending[1].at;timers.delete(pending[0]);pending[1].callback();await flush();
   }
   now=target;await flush();
  },
 };
}

const reply=(data,status=200)=>Promise.resolve({ok:status>=200&&status<300,status,json:async()=>data});
const token=(value='valid-token',extra={})=>reply({token:value,ready:true,...extra});
const protectedToken=(extra={})=>token('signed-token',{captcha:{provider:'turnstile',siteKey:'synthetic-site-key',action:'contact'},...extra});
const hanging=signal=>new Promise((resolve,reject)=>{
 const abort=()=>{const error=new Error('aborted');error.name='AbortError';reject(error);};
 if(signal.aborted)abort();else signal.addEventListener('abort',abort,{once:true});
});

test('waits for the token minimum age, sends stable values and clears only on success',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token():reply({ok:true}));
 const file={name:'photo.heic',size:123,lastModified:1};page.attach([file]);
 await page.tick(0);const attempt=page.submit();await page.tick(1999);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 await page.tick(1);await attempt;
 const post=page.calls.find(call=>call.url==='/api/enquiry');
 assert.equal(post.options.body.get('service'),'Двери');assert.equal(post.options.body.get('contact_method'),'По телефону');
 assert.equal(post.options.body.get('phone'),'+372 555 1234');assert.equal(post.options.body.get('email'),undefined);
 assert.equal(post.options.body.get('_token'),'valid-token');assert.equal(post.options.body.get('attachment1'),file);
 assert.equal(page.form.resetCalled,true);assert.equal(page.fileList.children.length,0);assert.equal(page.status.dataset.state,'success');
});

test('refreshes an expired prefetched token before a single POST',async()=>{
 let count=0;
 const page=fixture(call=>call.url==='/api/token'?token('token-'+(++count)):reply({ok:true}));
 await page.tick(3601000);const attempt=page.submit();await page.tick(2000);await attempt;
 const posts=page.calls.filter(call=>call.url==='/api/enquiry');
 assert.equal(posts.length,1);assert.equal(posts[0].options.body.get('_token'),'token-2');
});

test('email contact sends only the selected reply channel and localizes known server errors',async()=>{
 const message='Слишком много попыток. Попробуйте через 10 минут.';
 const translated='Liiga palju katseid. Proovige uuesti 10 minuti pärast.';
 const page=fixture(call=>call.url==='/api/token'?token():reply({error:message},429),{translate:value=>value===message?translated:value});
 page.selectContact('По email');
 await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
 const post=page.calls.find(call=>call.url==='/api/enquiry');
 assert.equal(post.options.body.get('contact_method'),'По email');assert.equal(post.options.body.get('email'),'customer@example.test');
 assert.equal(post.options.body.get('phone'),undefined);assert.equal(page.status.textContent,translated);assert.equal(page.form.resetCalled,undefined);
});

test('recovers from a failed initial token request without retrying POST',async()=>{
 let count=0;
 const page=fixture(call=>call.url==='/api/token'?(++count===1?reply(null,404):token()):reply({ok:true}));
 await page.tick(0);const attempt=page.submit();await page.tick(2000);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);assert.equal(page.status.dataset.state,'success');
});

test('bounds hanging token requests to ten seconds and retains form input',async()=>{
 const page=fixture(call=>hanging(call.options.signal));
 await page.tick(10000);assert.equal(page.controllers[0].signal.aborted,true);
 const attempt=page.submit();await page.tick(10000);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 assert.equal(page.status.textContent,'Отправка временно недоступна. Пожалуйста, позвоните нам.');
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.form.resetCalled,undefined);
});

test('aborting during token minimum-age wait prevents POST',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token():reply({ok:true}));
 await page.tick(0);const attempt=page.submit();await page.tick(100);page.controllers[1].abort();await flush();await attempt;
 await page.tick(2000);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);assert.equal(page.status.dataset.state,'error');
 assert.equal(page.elements.description.value,'A synthetic enquiry.');
});

test('allows mobile uploads beyond thirty seconds and aborts the whole attempt at ninety seconds',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token():hanging(call.options.signal));
 await page.tick(2000);const attempt=page.submit();await page.tick(30000);
 const post=page.calls.find(call=>call.url==='/api/enquiry');assert.ok(post);assert.equal(post.options.signal.aborted,false);
 await page.tick(60000);await attempt;
 assert.equal(post.options.signal.aborted,true);assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.button.disabled,false);assert.equal(page.status.dataset.state,'error');
});

test('HTML server failures show a localized safe message and retain attachments',async()=>{
 const translate=message=>message==='Не удалось подтвердить отправку.'?'Saatmist ei õnnestunud kinnitada.':message;
 const page=fixture(call=>call.url==='/api/token'?token():Promise.resolve({ok:false,status:500,json:async()=>{throw new SyntaxError('Unexpected token <: private server details');}}),{translate});
 page.attach([{name:'plan.pdf',size:100,lastModified:1}]);
 await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
 assert.equal(page.status.textContent,'Saatmist ei õnnestunud kinnitada.');assert.equal(page.fileList.children.length,1);
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.form.resetCalled,undefined);
});

test('does not expose unknown JSON server details and handles upload-limit HTML failures',async()=>{
 for(const status of [500,413]){
  const page=fixture(call=>call.url==='/api/token'?token():reply({error:'Private server details'},status));
  await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
  assert.equal(page.status.textContent,status===413?'Максимум 5 файлов и 10 МБ суммарно.':'Не удалось подтвердить отправку.');
 }
});

test('offline POST errors show a localized message without browser diagnostics',async()=>{
 const translate=message=>message==='Не удалось подтвердить отправку.'?'Saatmist ei õnnestunud kinnitada.':message;
 const page=fixture(call=>call.url==='/api/token'?token():Promise.reject(new TypeError('Failed to fetch: private network diagnostic')),{translate});
 await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
 assert.equal(page.status.textContent,'Saatmist ei õnnestunud kinnitada.');assert.equal(page.status.dataset.state,'error');
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.form.resetCalled,undefined);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);
});

test('honors token timing metadata and refuses a duplicate pending submission',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token('metadata-token',{expiresIn:3600,minDelayMs:3000}):hanging(call.options.signal));
 await page.tick(0);const attempt=page.submit();await page.tick(2999);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 await page.tick(1);await page.submit();assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);
 page.controllers[1].abort();await flush();await attempt;
});

test('renders Turnstile from the official script and submits one verified response',async()=>{
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}),{hostname:'lanehitus.ee'});
 await page.tick(2000);
 assert.equal(page.captchaBox.hidden,false);assert.equal(page.scripts.length,1);
 assert.equal(page.scripts[0].src,'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit');
 const widget=page.widgets[0];assert.equal(widget.host,page.captchaHost);assert.equal(widget.options.size,'flexible');
 assert.equal(widget.options.theme,'light');assert.equal(widget.options.language,'auto');assert.equal(widget.options.action,'contact');assert.equal(widget.options['response-field'],false);
 page.elements['cf-turnstile-response']=new Element('stale-provider-field');
 page.solve('verified-response');const attempt=page.submit();await page.tick(0);await attempt;
 const post=page.calls.find(call=>call.url==='/api/enquiry');
 assert.deepEqual(post.options.body.getAll('cf-turnstile-response'),['verified-response']);
 assert.equal(page.resets.length,1);assert.equal(page.widgets.length,1,'Refreshing the signed token must preserve the widget');
 assert.equal(page.status.dataset.state,'success');
});

test('waits for verification without sending or automatically retrying a POST',async()=>{
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({error:'Не удалось подтвердить отправку. Пожалуйста, позвоните нам.'},502));
 page.attach([{name:'plan.pdf',size:100,lastModified:1}]);
 await page.tick(2000);const attempt=page.submit();await page.tick(5000);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 assert.equal(page.captchaStatus.textContent,'Подтвердите, что вы не робот.');
 page.solve();await page.tick(0);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);assert.equal(page.resets.length,1);
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.fileList.children.length,1);
 await page.tick(2000);assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);
});

test('expired challenges retain the form and recover through a new challenge',async()=>{
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}));
 await page.tick(2000);page.solve('expired-response');page.expire();
 assert.equal(page.captchaRetry.hidden,false);assert.equal(page.captchaStatus.textContent,'Подтвердите, что вы не робот.');
 const rejected=page.submit();await page.tick(0);await rejected;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);assert.equal(page.elements.description.value,'A synthetic enquiry.');
 await page.retryCaptcha();page.solve('fresh-response');await page.tick(2000);
 const attempt=page.submit();await page.tick(0);await attempt;
 const posts=page.calls.filter(call=>call.url==='/api/enquiry');assert.equal(posts.length,1);
 assert.equal(posts[0].options.body.get('cf-turnstile-response'),'fresh-response');
});

test('expiry callbacks never abort a valid response already being uploaded',async()=>{
 let finishPost;
 const page=fixture(call=>call.url==='/api/token'?protectedToken():new Promise(resolve=>{finishPost=resolve;}));
 await page.tick(2000);page.solve();const attempt=page.submit();await page.tick(0);
 const post=page.calls.find(call=>call.url==='/api/enquiry');assert.ok(post);page.expire();await page.tick(0);
 assert.equal(post.options.signal.aborted,false);assert.equal(page.resets.length,0);assert.equal(page.captchaRetry.disabled,true);
 finishPost({ok:true,status:200,json:async()=>({ok:true})});await flush();await attempt;
 assert.equal(page.status.dataset.state,'success');assert.equal(page.resets.length,1);
});

test('blocked provider scripts expose retry and recover without losing the enquiry',async()=>{
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}),{scriptOutcome:'error'});
 await page.tick(2000);assert.equal(page.widgets.length,0);assert.equal(page.captchaRetry.hidden,false);
 const rejected=page.submit();await page.tick(0);await rejected;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 assert.equal(page.status.textContent,'Проверка временно недоступна. Повторите попытку или позвоните нам.');
 assert.equal(page.elements.description.value,'A synthetic enquiry.');
 page.scriptOutcome('load');await page.retryCaptcha();await page.tick(2000);page.solve();
 const attempt=page.submit();await page.tick(0);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,1);assert.equal(page.status.dataset.state,'success');
});

test('provider loading and challenge waits are bounded and never bypass verification',async()=>{
 const blocked=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}),{scriptOutcome:'hang'});
 await blocked.tick(10000);assert.equal(blocked.scripts[0].removed,true);assert.equal(blocked.captchaRetry.hidden,false);
 assert.equal(blocked.calls.filter(call=>call.url==='/api/enquiry').length,0);
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}));
 await page.tick(2000);const attempt=page.submit();await page.tick(90000);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);assert.equal(page.status.dataset.state,'error');
 assert.equal(page.elements.description.value,'A synthetic enquiry.');assert.equal(page.button.disabled,false);
});

test('narrow forms use a compact challenge and ignore callbacks from replaced widgets',async()=>{
 const page=fixture(call=>call.url==='/api/token'?protectedToken():reply({ok:true}),{width:244,language:'ru'});
 await page.tick(2000);assert.equal(page.widgets[0].options.size,'compact');assert.equal(page.widgets[0].options.language,'ru');
 page.resizeCaptcha(400);await page.tick(0);assert.equal(page.widgets[1].options.size,'flexible');assert.equal(page.removedWidgets.length,1);
 page.solve('stale-response',0);const attempt=page.submit();await page.tick(0);
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
 page.solve('new-response');await page.tick(0);await attempt;
 assert.equal(page.calls.find(call=>call.url==='/api/enquiry').options.body.get('cf-turnstile-response'),'new-response');
});

test('a signed-token refresh preserves an unused challenge response',async()=>{
 let issued=0;
 const page=fixture(call=>call.url==='/api/token'?protectedToken({token:'signed-'+(++issued),expiresIn:3,minDelayMs:0}):reply({ok:true}));
 await page.tick(0);page.solve('unused-response');await page.tick(4000);
 const attempt=page.submit();await page.tick(0);await attempt;
 const post=page.calls.find(call=>call.url==='/api/enquiry');assert.equal(post.options.body.get('_token'),'signed-2');
 assert.equal(post.options.body.get('cf-turnstile-response'),'unused-response');assert.equal(page.widgets.length,1);
 assert.equal(page.resets.length,1,'Only the actual POST consumes and resets the challenge');
});

test('present but invalid captcha configuration fails closed',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token('valid-token',{captcha:null}):reply({ok:true}));
 await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
 assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);assert.equal(page.captchaBox.hidden,false);
 assert.equal(page.captchaRetry.hidden,false);assert.equal(page.elements.description.value,'A synthetic enquiry.');
});

test('legacy local preview without captcha configuration never loads the provider',async()=>{
 const page=fixture(call=>call.url==='/api/token'?token():reply({ok:true}));
 await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
 assert.equal(page.scripts.length,0);assert.equal(page.captchaBox.hidden,true);
 assert.equal(page.calls.find(call=>call.url==='/api/enquiry').options.body.get('cf-turnstile-response'),undefined);
});

test('missing captcha metadata fails closed outside the loopback preview',async()=>{
 for(const hostname of ['lanehitus.ee','www.lanehitus.ee']){
  const page=fixture(call=>call.url==='/api/token'?token():reply({ok:true}),{hostname});
  await page.tick(2000);const attempt=page.submit();await page.tick(0);await attempt;
  assert.equal(page.calls.filter(call=>call.url==='/api/enquiry').length,0);
  assert.equal(page.captchaBox.hidden,false);assert.equal(page.captchaRetry.hidden,false);
  assert.equal(page.elements.description.value,'A synthetic enquiry.');
 }
});
