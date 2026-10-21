'use strict';
const pageLanguage=document.documentElement.lang==='ru'?'ru':'et';
const localeMessages=window.LAN_MESSAGES?.[pageLanguage]||{};
function t(message){return localeMessages[message]??message;}
// Full-width galleries must exclude the space occupied by desktop scrollbars.
const pageRoot=document.documentElement;
let pageWidth=0;
function syncPageWidth(){
 const width=pageRoot.clientWidth;
 if(width<=0||width===pageWidth)return;
 pageWidth=width;
 pageRoot.style.setProperty('--page-width',width+'px');
}
syncPageWidth();
window.addEventListener('resize',syncPageWidth,{passive:true});
if('ResizeObserver' in window)new ResizeObserver(syncPageWidth).observe(pageRoot);
// Keep the copyright year current, including on pages left open over New Year.
const copyrightYear=document.querySelector('[data-current-year]');
if(copyrightYear){
 const updateYear=()=>{copyrightYear.textContent=String(new Date().getFullYear());};
 updateYear();
 setInterval(updateYear,60000);
 document.addEventListener('visibilitychange',updateYear);
}
const toggle=document.querySelector('.menu-button');
const nav=document.querySelector('#navigation');
function setMenuOpen(open){
 if(open)document.querySelector('.language-picker')?.removeAttribute('open');
 nav.classList.toggle('open',open);
 toggle.setAttribute('aria-expanded',String(open));
 toggle.setAttribute('aria-label',open?t('Закрыть меню'):t('Открыть меню'));
}
function closeMenu(){setMenuOpen(false);}
toggle.addEventListener('click',()=>setMenuOpen(toggle.getAttribute('aria-expanded')!=='true'));
document.addEventListener('pointerdown',event=>{
 if(nav.classList.contains('open')&&!nav.contains(event.target)&&!toggle.contains(event.target))closeMenu();
});
nav.addEventListener('focusout',event=>{
 if(!nav.contains(event.relatedTarget)&&!toggle.contains(event.relatedTarget))closeMenu();
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&toggle.getAttribute('aria-expanded')==='true'){closeMenu();toggle.focus();}});
nav.addEventListener('click',e=>{if(e.target.closest('a'))closeMenu();});
matchMedia('(min-width:701px)').addEventListener('change',closeMenu);
const search=document.querySelector('#faq-search');
if(search){search.addEventListener('input',()=>{const query=search.value.trim().toLocaleLowerCase(pageLanguage);let count=0;document.querySelectorAll('#faq-list details').forEach(item=>{item.hidden=!item.textContent.toLocaleLowerCase(pageLanguage).includes(query);if(!item.hidden)count++;});document.querySelector('#faq-empty').hidden=count>0;});}
const contactData={'email': 'bGViam9ka2luLnRvbGw2OEBnbWFpbC5jb20=', 'phone': 'KzM3MjUyMzI0Nzc='};
const getContact=kind=>atob(contactData[kind]);
const email=getContact('email');
document.querySelectorAll('[data-contact]').forEach(link=>link.addEventListener('click',()=>{link.href=(link.dataset.contact==='phone'?'tel:':'mailto:')+getContact(link.dataset.contact);}));
const revealContact=document.querySelector('#show-contacts');
revealContact?.addEventListener('click',()=>{
 const values=document.querySelector('#contact-values');
 const expanded=revealContact.getAttribute('aria-expanded')!=='true';
 if(expanded)values.querySelectorAll('[data-contact-value]').forEach(node=>{const kind=node.dataset.contactValue;const a=document.createElement('a');a.href=(kind==='phone'?'tel:':'mailto:')+getContact(kind);a.textContent=kind==='phone'?getContact(kind).replace(/(\+\d{3})(\d{3})(\d+)/,'$1 $2 $3'):getContact(kind);node.replaceChildren(a);});
 values.hidden=!expanded;revealContact.setAttribute('aria-expanded',String(expanded));revealContact.textContent=expanded?t('Скрыть номер и email'):t('Показать номер и email');
});
const copyEmail=document.querySelector('#copy-email');
if(copyEmail)copyEmail.addEventListener('click',async()=>{const status=document.querySelector('#email-status');try{await navigator.clipboard.writeText(email);status.textContent=t('Email скопирован.');}catch{status.textContent=t('Не удалось скопировать автоматически. Выделите адрес выше и скопируйте его.');}});
function showFormFeedback(node,message,state='info'){
 node.dataset.state=state;
 node.setAttribute('role',state==='error'?'alert':'status');
 node.textContent=t(message);
}
const form=document.querySelector('#request-form');
if(form){
 const service=form.elements.service;
 const requested=new URLSearchParams(location.search).get('service');
 if([...service.options].some(option=>option.value===requested))service.value=requested;
 const status=document.querySelector('#form-status');
 function syncContactMethod(){
  const byPhone=form.elements.contact_method.value==='По телефону';
  document.querySelector('#phone-reply-field').hidden=!byPhone;
  document.querySelector('#email-reply-field').hidden=byPhone;
  form.elements.phone.disabled=!byPhone;form.elements.phone.required=byPhone;
  form.elements.email.disabled=byPhone;form.elements.email.required=!byPhone;
  form.elements.phone.setCustomValidity('');form.elements.email.setCustomValidity('');
 }
 form.querySelectorAll('[name="contact_method"]').forEach(input=>input.addEventListener('change',syncContactMethod));
 syncContactMethod();

 let attachedFiles=[];
 const picker=document.querySelector('#attachments'),fileList=document.querySelector('#attachment-list'),fileStatus=document.querySelector('#attachment-status');
 function renderFiles(){
  fileList.replaceChildren();
  attachedFiles.forEach((file,index)=>{
   const row=document.createElement('li'),label=document.createElement('span'),remove=document.createElement('button');
   label.textContent=file.name+' · '+(file.size/1024/1024).toFixed(1)+t(' МБ');
   remove.type='button';remove.textContent=t('Удалить');remove.setAttribute('aria-label',t('Удалить ')+file.name);
   remove.addEventListener('click',()=>{attachedFiles.splice(index,1);renderFiles();showFormFeedback(fileStatus,t('Файл удалён. ')+attachedFiles.length+t(' из 5 файлов.'));picker.focus();});
   row.append(label,remove);fileList.append(row);
  });
 }
 picker.addEventListener('change',()=>{
  const candidates=[...attachedFiles];
  for(const file of picker.files){if(!candidates.some(f=>f.name===file.name&&f.size===file.size&&f.lastModified===file.lastModified))candidates.push(file);}
  let error='';
  if(candidates.length>5)error=t('Можно добавить не более 5 файлов. Удалите лишние и попробуйте снова.');
  else if(candidates.some(f=>!/\.(jpe?g|png|webp|heic|heif|pdf)$/i.test(f.name)))error=t('Выберите изображения JPG, PNG, WebP, HEIC или документы PDF.');
  else if(candidates.reduce((total,f)=>total+f.size,0)>10000000)error=t('Общий размер файлов не должен превышать 10 МБ.');
  picker.value='';
  if(error){showFormFeedback(fileStatus,error,'error');return;}
  attachedFiles=candidates;renderFiles();showFormFeedback(fileStatus,t('Выбрано ')+attachedFiles.length+t(' из 5 файлов.'));
 });
 function validate(){for(const name of [form.elements.contact_method.value==='По телефону'?'phone':'email','location','description']){const field=form.elements[name];field.setCustomValidity(field.value.trim()?'':t('Заполните это поле.'));}return form.reportValidity();}
 form.addEventListener('input',e=>{if(e.target.setCustomValidity)e.target.setCustomValidity('');showFormFeedback(status,'');});

 // Same-origin SMTP delivery. Values remain in the form on failure.
 form.action='/api/enquiry';
 const sendButton=form.querySelector('[type="submit"]');sendButton.disabled=false;
 let submissionPending=false,tokenPromise=null;
 async function prepareToken(){
  const response=await fetch('/api/token',{cache:'no-store'});
  if(!response.ok)throw new Error(t('Отправка временно недоступна. Пожалуйста, позвоните нам.'));
  const data=await response.json();return data;
 }
 function loadToken(){tokenPromise=prepareToken().catch(()=>null);}
 loadToken();
 form.addEventListener('submit',async event=>{
  event.preventDefault();
  if(submissionPending||!validate()||form.elements._honey.value)return;
  submissionPending=true;sendButton.disabled=true;sendButton.textContent=t('Отправляем…');form.setAttribute('aria-busy','true');
  showFormFeedback(status,t('Отправляем заявку…'),'pending');
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),30000);
  try{
   const session=await tokenPromise;
   if(!session||!session.ready)throw new Error(t('Отправка временно недоступна. Пожалуйста, позвоните нам.'));
   const data=new FormData(form);data.append('_token',session.token);
   attachedFiles.forEach((file,index)=>data.append('attachment'+(index+1),file,file.name));
   const response=await fetch('/api/enquiry',{method:'POST',body:data,signal:controller.signal});
   const result=await response.json();
   if(!response.ok||!result.ok)throw new Error(result.error||t('Не удалось подтвердить отправку.'));
   showFormFeedback(status,t('Спасибо! Заявка отправлена. Мы свяжемся с вами выбранным способом.'),'success');
   form.reset();attachedFiles=[];renderFiles();fileStatus.textContent='';syncContactMethod();
  }catch(error){
   showFormFeedback(status,error.name==='AbortError'?t('Не удалось подтвердить отправку вовремя. Данные сохранены в форме. Пожалуйста, позвоните нам.'):error.message,'error');
  }finally{
   clearTimeout(timeout);submissionPending=false;sendButton.disabled=false;sendButton.textContent=t('Отправить заявку');form.removeAttribute('aria-busy');loadToken();
  }
 });



}

// Same-page enquiries preserve the chosen service without a page reload.
document.querySelectorAll('a[data-service]').forEach(link=>link.addEventListener('click',()=>{
 const select=document.querySelector('#service');
 if([...select.options].some(option=>option.value===link.dataset.service))select.value=link.dataset.service;
 document.querySelector('#form-status').textContent='';
}));
function revealAnchor(){
 const id=location.hash.slice(1);
 const target=document.getElementById(id);
 if(!target)return;
 if(target.tagName==='DETAILS')target.open=true;
 if(!target.matches('input,textarea,select,button,a[href]'))target.setAttribute('tabindex','-1');
 target.focus({preventScroll:true});
}
window.addEventListener('hashchange',revealAnchor);
document.querySelectorAll('a[href="#privacy"]').forEach(link=>link.addEventListener('click',()=>{document.querySelector('#privacy').open=true;}));
revealAnchor();
const sections=[...new Set([...nav.querySelectorAll('a[href^="#"]')].map(link=>document.getElementById(link.hash.slice(1))).filter(Boolean))];
let scrollPending=false;
function updateSection(){
 const limit=document.querySelector('header').getBoundingClientRect().height+60;
 let current=null;
 for(const section of sections){if(section.getBoundingClientRect().top<=limit)current=section.id;}
 document.querySelectorAll('nav a[href^="#"]').forEach(link=>{if(link.hash==='#'+current)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
 scrollPending=false;
}
window.addEventListener('scroll',()=>{if(!scrollPending){scrollPending=true;requestAnimationFrame(updateSection);}},{passive:true});
window.addEventListener('resize',updateSection);
updateSection();


// Shared full-screen viewer; images retain their original aspect ratio.
const gallery=document.createElement('dialog');
gallery.className='photo-gallery';gallery.setAttribute('aria-labelledby','gallery-title');
gallery.innerHTML='<div class="gallery-bar"><h2 id="gallery-title">Фотографии</h2><button class="gallery-close" type="button" aria-label="Закрыть галерею">×</button></div><div class="gallery-stage"><img class="gallery-image" alt="" draggable="false"></div><button class="gallery-prev" type="button" aria-label="Предыдущее фото">‹</button><button class="gallery-next" type="button" aria-label="Следующее фото">›</button><p class="gallery-caption" aria-live="polite"><span class="gallery-caption-text"></span></p>';
gallery.querySelector('#gallery-title').textContent=t('Фотографии');
for(const [selector,label] of [
 ['.gallery-close','Закрыть галерею'],
 ['.gallery-prev','Предыдущее фото'],
 ['.gallery-next','Следующее фото']
])gallery.querySelector(selector).setAttribute('aria-label',t(label));
document.body.append(gallery);
let galleryOwner=null,galleryOpener=null;
function updateGallery(){if(!galleryOwner)return;const {slides,index}=galleryOwner.snapshot();const image=gallery.querySelector('.gallery-image');image.src=slides[index].dataset.fullsrc||slides[index].currentSrc||slides[index].src;image.alt=slides[index].alt;gallery.querySelector('.gallery-caption-text').textContent=(index+1)+' / '+slides.length+' · '+slides[index].alt;gallery.classList.toggle('is-single',slides.length===1);}
function openGallery(owner,opener,title){galleryOwner=owner;galleryOpener=opener;gallery.querySelector('#gallery-title').textContent=title;updateGallery();gallery.showModal();document.body.classList.add('gallery-open');document.dispatchEvent(new Event('gallerychange'));}
gallery.querySelector('.gallery-close').addEventListener('click',()=>gallery.close());
// The image uses object-fit:contain; its element also covers the letterbox space.
// Close only outside the actual rendered photo, not inside that element's box.
gallery.addEventListener('click',event=>{
 if(event.target.closest('button,.gallery-caption-text'))return;
 if(event.target.closest('.gallery-bar,.gallery-caption')){gallery.close();return;}
 const image=gallery.querySelector('.gallery-image');
 if(!image.naturalWidth||!image.naturalHeight){if(event.target===gallery)gallery.close();return;}
 const box=image.getBoundingClientRect();
 const scale=Math.min(box.width/image.naturalWidth,box.height/image.naturalHeight);
 const width=image.naturalWidth*scale,height=image.naturalHeight*scale;
 const left=box.left+(box.width-width)/2,top=box.top+(box.height-height)/2;
 if(event.clientX<left||event.clientX>left+width||event.clientY<top||event.clientY>top+height)gallery.close();
});

gallery.addEventListener('close',()=>{document.body.classList.remove('gallery-open');galleryOwner=null;galleryOpener?.focus({preventScroll:true});document.dispatchEvent(new Event('gallerychange'));});
function galleryStep(direction){galleryOwner?.step(direction);updateGallery();}
gallery.querySelector('.gallery-prev').addEventListener('click',()=>galleryStep(-1));
gallery.querySelector('.gallery-next').addEventListener('click',()=>galleryStep(1));
gallery.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();galleryStep(e.key==='ArrowRight'?1:-1);}});
function enableSwipe(element,onSwipe,onStart=()=>{},onEnd=()=>{}){
 let pointer=null,suppressClick=false;
 element.addEventListener('pointerdown',e=>{if(!e.isPrimary||e.button!==0)return;suppressClick=false;pointer={id:e.pointerId,x:e.clientX,y:e.clientY};e.target.setPointerCapture?.(e.pointerId);onStart();});
 element.addEventListener('pointerup',e=>{if(!pointer||e.pointerId!==pointer.id)return;const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;pointer=null;suppressClick=Math.abs(dx)>10||Math.abs(dy)>10;if(Math.abs(dx)>30&&Math.abs(dx)>Math.abs(dy))onSwipe(dx<0?1:-1);onEnd();});
 const cancel=()=>{pointer=null;onEnd();};element.addEventListener('pointercancel',cancel);element.addEventListener('lostpointercapture',cancel);
 element.addEventListener('click',e=>{if(suppressClick){e.preventDefault();e.stopImmediatePropagation();suppressClick=false;}},true);
}
enableSwipe(gallery.querySelector('.gallery-stage'),galleryStep);
// Deferred previews acquire sources only when needed. Cache in-flight loads and
// successful decodes, but allow a later interaction to retry a failed image.
const carouselImageLoads=new WeakMap();
function loadCarouselImage(image){
 const existing=carouselImageLoads.get(image);
 if(existing)return existing;
 const pending=new Promise(resolve=>{
  let settled=false,decoding=false;
  function finish(ready){
   if(settled)return;
   settled=true;clearTimeout(timeout);
   image.removeEventListener('load',loaded);image.removeEventListener('error',failed);
   resolve(ready);
  }
  function loaded(){
   if(settled||decoding)return;
   if(!image.naturalWidth){finish(false);return;}
   decoding=true;
   try{Promise.resolve(image.decode?.()).then(()=>finish(image.naturalWidth>0),()=>finish(false));}
   catch{finish(false);}
  }
  function failed(){finish(false);}
  const timeout=setTimeout(failed,20000);
  image.addEventListener('load',loaded);image.addEventListener('error',failed);
  const source=image.dataset.src||image.getAttribute('src');
  const sources=image.dataset.srcset||image.getAttribute('srcset');
  if(!source&&!sources){finish(false);return;}
  // Reassign an already failed URL so another attempt emits fresh load events.
  if(image.complete&&!image.naturalWidth){image.removeAttribute('srcset');image.removeAttribute('src');}
  image.loading='eager';
  if(sources&&image.getAttribute('srcset')!==sources)image.setAttribute('srcset',sources);
  if(source&&image.getAttribute('src')!==source)image.setAttribute('src',source);
  // Cached images can finish before a load listener observes an event.
  if(image.complete&&image.naturalWidth)loaded();
 });
 carouselImageLoads.set(image,pending);
 pending.then(ready=>{if(!ready&&carouselImageLoads.get(image)===pending)carouselImageLoads.delete(image);});
 return pending;
}
// Independent 5-second carousels with staggered starts.
document.querySelectorAll('.service-carousel').forEach(carousel=>{
 const slides=[...carousel.querySelectorAll('.carousel-slide')];
 if(!slides.length)return;
 const motion=matchMedia('(prefers-reduced-motion: reduce)');
 let index=0,displayedIndex=0,requestVersion=0,transitioning=false;
 let paused=motion.matches,hovered=false,focused=false,visible=false,dragging=false,timer=null;
 function paint(){slides.forEach((slide,i)=>{slide.classList.toggle('is-active',i===displayedIndex);slide.setAttribute('aria-hidden',String(i!==displayedIndex));});}
 const autoplayOffset=Math.floor(Math.random()*3000);
 function advance(){timer=null;void go(index+1,true);}
 function sync(delay=5000+autoplayOffset){clearTimeout(timer);timer=null;if(slides.length>1&&!transitioning&&!paused&&!hovered&&!focused&&visible&&!document.hidden&&!dragging&&!gallery.open)timer=setTimeout(advance,delay);}
 function preloadNext(){if(slides.length>1&&visible&&!document.hidden&&!gallery.open)void loadCarouselImage(slides[(index+1)%slides.length]);}
 async function go(next,autoplay=false){
  const version=++requestVersion;
  index=((next%slides.length)+slides.length)%slides.length;
  transitioning=true;sync();
  const ready=await loadCarouselImage(slides[index]);
  // Rapid navigation may finish out of order; only its latest target can paint.
  if(version!==requestVersion)return;
  if(ready){displayedIndex=index;paint();}
  transitioning=false;preloadNext();sync(autoplay?5000:5000+autoplayOffset);
 }
 function setVisible(next){
  if(visible===next)return;
  visible=next;
  if(visible&&!document.hidden)void go(index);
  else sync();
 }
 const owner={snapshot:()=>({slides,index}),step:direction=>go(index+direction)};
 carousel.querySelector('.carousel-prev').addEventListener('click',()=>go(index-1));
 carousel.querySelector('.carousel-next').addEventListener('click',()=>go(index+1));
 const opener=carousel.querySelector('.carousel-open');
 opener.addEventListener('click',()=>openGallery(owner,opener,carousel.closest('.service-row').querySelector('h3').textContent));
 const strip=document.querySelector('[data-service-gallery="'+carousel.closest('.service-row').querySelector('.service-price').getAttribute('href').slice(1)+'"]');
 strip?.querySelectorAll('.service-photo').forEach(button=>button.addEventListener('click',()=>{go(Number(button.dataset.photoIndex));opener.click();}));
 carousel.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse'){hovered=true;sync();}});
 carousel.addEventListener('pointerleave',()=>{hovered=false;sync();});
 carousel.addEventListener('focusin',()=>{focused=true;sync();});
 carousel.addEventListener('focusout',e=>{focused=carousel.contains(e.relatedTarget);sync();});
 carousel.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();go(index+(e.key==='ArrowRight'?1:-1));}});
 enableSwipe(carousel,direction=>go(index+direction),()=>{dragging=true;sync();},()=>{dragging=false;sync();});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden&&visible)void go(index);else sync();});
 document.addEventListener('gallerychange',()=>{if(!gallery.open&&visible&&!document.hidden)void go(index);else sync();});
 motion.addEventListener('change',()=>{paused=motion.matches;sync();});
 if('IntersectionObserver' in window){const observer=new IntersectionObserver(entries=>{setVisible(entries[0].isIntersecting);});observer.observe(carousel);}
 else{
  let visibilityFrame=null;
  function updateVisibility(){
   visibilityFrame=null;
   const bounds=carousel.getBoundingClientRect();
   setVisible(bounds.bottom>0&&bounds.top<innerHeight&&bounds.right>0&&bounds.left<innerWidth);
  }
  function queueVisibility(){if(visibilityFrame===null)visibilityFrame=requestAnimationFrame(updateVisibility);}
  window.addEventListener('scroll',queueVisibility,{passive:true});window.addEventListener('resize',queueVisibility,{passive:true});
  updateVisibility();
 }
 paint();sync();
});

// Animate a photo track instead of a native scroll offset, including during touch.
if(typeof Element.prototype.animate==='function'){
 const motion=matchMedia('(prefers-reduced-motion: reduce)');
 const states=[...document.querySelectorAll('.service-photo-strip')].map(strip=>{
  const track=document.createElement('div');track.className='service-photo-track';
  track.append(...strip.childNodes);strip.append(track);
  return {strip,track,animation:null,limit:0,duration:0,visible:!('IntersectionObserver' in window),pointer:null,suppressUntil:0};
 });
 function phase(state){
  const time=Number(state.animation?.currentTime)||0;
  return state.duration?((time/state.duration)%2+2)%2:0;
 }
 function position(state){const progress=phase(state);return state.limit*(progress<=1?progress:2-progress);}
 function seek(state,next){
  if(!state.animation||state.limit<=0)return;
  const reverse=phase(state)>=1,progress=Math.max(0,Math.min(state.limit,next))/state.limit;
  state.animation.currentTime=(reverse?2-progress:progress)*state.duration;
 }
 function sync(){
  for(const state of states){
   if(!state.animation)continue;
   const allowed=!motion.matches&&!document.hidden&&!gallery.open&&state.visible;
   if(allowed&&state.animation.playState!=='running')state.animation.play();
   else if(!allowed&&state.animation.playState!=='paused')state.animation.pause();
  }
 }
 function geometry(){
  for(const state of states){
   const limit=Math.max(0,state.track.scrollWidth-state.strip.clientWidth);
   if(motion.matches||limit<=1){
    const previous=state.animation?position(state):state.strip.scrollLeft;
    state.animation?.cancel();state.animation=null;state.pointer=null;
    state.strip.classList.remove('has-track-motion');
    state.limit=limit;state.duration=0;state.strip.scrollLeft=Math.min(limit,previous);
    continue;
   }
   if(state.animation&&state.limit===limit)continue;
   const reverse=state.animation&&phase(state)>=1;
   const previous=state.animation?position(state):state.strip.scrollLeft;
   const progress=Math.max(0,Math.min(1,previous/limit));
   const previousPhase=reverse?2-progress:progress;
   state.animation?.cancel();state.limit=limit;state.duration=limit/22*1000;
   state.strip.classList.add('has-track-motion');state.strip.scrollLeft=0;
   state.animation=state.track.animate([
    {transform:'translate3d(0,0,0)'},{transform:`translate3d(${-limit}px,0,0)`}
   ],{duration:state.duration,easing:'linear',direction:'alternate',iterations:Infinity,fill:'both'});
   state.animation.currentTime=previousPhase*state.duration;
  }
  sync();
 }
 for(const state of states){
  const {strip}=state;
  strip.addEventListener('pointerdown',event=>{
   if(!state.animation||!event.isPrimary||event.button!==0)return;
   state.suppressUntil=0;
   state.pointer={id:event.pointerId,x:event.clientX,y:event.clientY,lastX:event.clientX,dragged:false};
  });
  strip.addEventListener('pointermove',event=>{
   const pointer=state.pointer;if(!pointer||pointer.id!==event.pointerId)return;
   const dx=event.clientX-pointer.x,dy=event.clientY-pointer.y;
   if(!pointer.dragged){
    if(Math.max(Math.abs(dx),Math.abs(dy))<8)return;
    if(Math.abs(dy)>=Math.abs(dx)){state.pointer=null;return;}
    pointer.dragged=true;
    try{strip.setPointerCapture(event.pointerId);}catch{}
   }
   if(event.cancelable)event.preventDefault();
   seek(state,position(state)+pointer.lastX-event.clientX);pointer.lastX=event.clientX;
  },{passive:false});
  function endPointer(event){
   const pointer=state.pointer;if(!pointer||pointer.id!==event.pointerId)return;
   if(pointer.dragged)state.suppressUntil=performance.now()+500;
   state.pointer=null;
   try{if(strip.hasPointerCapture(event.pointerId))strip.releasePointerCapture(event.pointerId);}catch{}
  }
  strip.addEventListener('pointerup',endPointer);strip.addEventListener('pointercancel',endPointer);
  strip.addEventListener('lostpointercapture',endPointer);
  strip.addEventListener('click',event=>{
   if(performance.now()<state.suppressUntil){
    state.suppressUntil=0;event.preventDefault();event.stopImmediatePropagation();
   }
  },true);
  strip.addEventListener('wheel',event=>{
   if(!state.animation||event.ctrlKey||(!event.shiftKey&&Math.abs(event.deltaX)<=Math.abs(event.deltaY)))return;
   const amount=event.deltaX||(event.shiftKey?event.deltaY:0);if(!amount)return;
   const unit=event.deltaMode===1?16:event.deltaMode===2?strip.clientWidth:1;
   event.preventDefault();seek(state,position(state)+amount*unit);
  },{passive:false});
  strip.addEventListener('focusin',event=>{
   const photo=event.target.closest('.service-photo');
   if(!state.animation||!photo?.matches(':focus-visible'))return;
   const bounds=photo.getBoundingClientRect(),trackBounds=state.track.getBoundingClientRect();
   const left=bounds.left-trackBounds.left,right=left+bounds.width,current=position(state);
   if(left<current)seek(state,left);
   else if(right>current+strip.clientWidth)seek(state,right-strip.clientWidth);
  });
  for(const type of ['contextmenu','dragstart'])strip.addEventListener(type,event=>{if(state.animation)event.preventDefault();});
 }
 document.addEventListener('visibilitychange',sync);document.addEventListener('gallerychange',sync);
 motion.addEventListener('change',geometry);window.addEventListener('resize',geometry);
 if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{
   for(const entry of entries){
    const state=states.find(item=>item.strip===entry.target);
    if(state)state.visible=entry.isIntersecting&&entry.intersectionRatio>=.15;
   }
   sync();
  },{threshold:[0,.15]});
  for(const state of states)observer.observe(state.strip);
 }
 if('ResizeObserver' in window){
  const observer=new ResizeObserver(geometry);
  for(const state of states)observer.observe(state.strip);
 }
 geometry();
}

// Open the language menu on pointer hover; retain native tap and keyboard control.
const languagePicker=document.querySelector('.language-picker');
if(languagePicker){
 languagePicker.addEventListener('toggle',()=>{if(languagePicker.open&&matchMedia('(max-width:700px)').matches)closeMenu();});
 languagePicker.addEventListener('pointerenter',event=>{if(event.pointerType==='mouse')languagePicker.open=true;});
 languagePicker.addEventListener('pointerleave',event=>{if(event.pointerType==='mouse'&&!languagePicker.contains(document.activeElement))languagePicker.open=false;});
 languagePicker.addEventListener('focusout',event=>{if(!languagePicker.contains(event.relatedTarget)&&!languagePicker.matches(':hover'))languagePicker.open=false;});
 languagePicker.addEventListener('keydown',event=>{if(event.key==='Escape'){languagePicker.open=false;languagePicker.querySelector('summary').focus();}});
}

// Language navigation keeps the exact viewport coordinates, without category anchors.
const languagePositionParameter='_lan_scroll';
function restoreLanguagePosition(){
 const url=new URL(location.href);
 const raw=url.searchParams.get(languagePositionParameter);
 if(raw===null)return;
 // The coordinates travel with this navigation only, even if storage is blocked.
 url.searchParams.delete(languagePositionParameter);
 history.replaceState(history.state,'',url.pathname+url.search+url.hash);
 let saved;
 try{saved=JSON.parse(raw);}catch{return;}
 if(!Number.isFinite(saved?.top)||!Number.isFinite(saved?.left))return;
 const method=[...document.querySelectorAll('[name="contact_method"]')].find(input=>input.value===saved.contactMethod);
 if(method){
  method.checked=true;
  method.dispatchEvent(new Event('change',{bubbles:true}));
 }
 let active=true;
 function apply(){
  if(!active)return;
  const maximum=Math.max(0,document.documentElement.scrollHeight-innerHeight);
  const top=Math.max(0,Math.min(maximum,saved.top));
  const left=Math.max(0,saved.left);
  if(Math.abs(scrollY-top)>.5||Math.abs(scrollX-left)>.5){
   window.scrollTo({top,left,behavior:'instant'});
  }
 }
 function queueCorrection(){requestAnimationFrame(apply);}
 const events=['wheel','touchstart','pointerdown','keydown'];
 function stop(){
  active=false;
  clearTimeout(timeout);
  events.forEach(name=>document.removeEventListener(name,stop,true));
  window.removeEventListener('load',queueCorrection);
  window.removeEventListener('pageshow',queueCorrection);
  window.removeEventListener('pagehide',stop);
 }
 const timeout=setTimeout(stop,15000);
 events.forEach(name=>document.addEventListener(name,stop,{capture:true,passive:true}));
 window.addEventListener('pagehide',stop,{once:true});
 window.addEventListener('pageshow',queueCorrection,{once:true});
 apply();
 queueCorrection();
 if(document.readyState==='complete')queueCorrection();
 else window.addEventListener('load',queueCorrection,{once:true});
 document.fonts?.ready.then(queueCorrection).catch(()=>{});
}

document.querySelectorAll('a[data-language]').forEach(link=>{
 link.addEventListener('click',event=>{
  if(event.defaultPrevented||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  if(link.dataset.language===pageLanguage){
   if(languagePicker)languagePicker.open=false;
   return;
  }
  const destination=new URL(link.getAttribute('href'),location.origin);
  destination.search=location.search;
  destination.hash='';
  const selectedService=document.querySelector('#service')?.value;
  if(selectedService)destination.searchParams.set('service',selectedService);
  destination.searchParams.set(languagePositionParameter,JSON.stringify({
   top:scrollY,left:scrollX,
   contactMethod:document.querySelector('#request-form')?.elements.contact_method.value
  }));
  link.href=destination.pathname+destination.search;
  location.assign(link.href);
 });
});

// Keep mobile language selection before the hamburger with a separate touch target.
const mobileLanguage=matchMedia('(max-width:700px)');
function arrangeLanguage(){
 if(!languagePicker)return;
 if(mobileLanguage.matches)toggle.before(languagePicker);
 else nav.append(languagePicker);
 languagePicker.open=false;
}
mobileLanguage.addEventListener('change',arrangeLanguage);
arrangeLanguage();

// Return to the top without leaving a #top fragment in the address bar.
document.querySelectorAll('[data-scroll-top]').forEach(link=>{
 link.addEventListener('click',event=>{
  event.preventDefault();
  if(location.hash)history.replaceState(null,'',location.pathname+location.search);
  window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
 });
});


// Cookie Consent: reuse the informational notice from pavelpsec.uk.
// CookieConsent 3.1.1 | Copyright (c) 2016 Silktide Ltd | MIT | See THIRD_PARTY_NOTICES.md.
!function(e){if(!e.hasInitialised){var t={escapeRegExp:function(e){return e.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g,"\\$&")},hasClass:function(e,t){var i=" ";return 1===e.nodeType&&(i+e.className+i).replace(/[\n\t]/g,i).indexOf(i+t+i)>=0},addClass:function(e,t){e.className+=" "+t},removeClass:function(e,t){var i=new RegExp("\\b"+this.escapeRegExp(t)+"\\b");e.className=e.className.replace(i,"")},interpolateString:function(e,t){return e.replace(/{{([a-z][a-z0-9\-_]*)}}/gi,function(e){return t(arguments[1])||""})},getCookie:function(e){var t=("; "+document.cookie).split("; "+e+"=");return t.length<2?void 0:t.pop().split(";").shift()},setCookie:function(e,t,i,n,o,s){var r=new Date;r.setHours(r.getHours()+24*(i||365));var a=[e+"="+t,"expires="+r.toUTCString(),"path="+(o||"/")];n&&a.push("domain="+n),s&&a.push("secure"),document.cookie=a.join(";")},deepExtend:function(e,t){for(var i in t)t.hasOwnProperty(i)&&(i in e&&this.isPlainObject(e[i])&&this.isPlainObject(t[i])?this.deepExtend(e[i],t[i]):e[i]=t[i]);return e},throttle:function(e,t){var i=!1;return function(){i||(e.apply(this,arguments),i=!0,setTimeout(function(){i=!1},t))}},hash:function(e){var t,i,n=0;if(0===e.length)return n;for(t=0,i=e.length;t<i;++t)n=(n<<5)-n+e.charCodeAt(t),n|=0;return n},normaliseHex:function(e){return"#"==e[0]&&(e=e.substr(1)),3==e.length&&(e=e[0]+e[0]+e[1]+e[1]+e[2]+e[2]),e},getContrast:function(e){return e=this.normaliseHex(e),(299*parseInt(e.substr(0,2),16)+587*parseInt(e.substr(2,2),16)+114*parseInt(e.substr(4,2),16))/1e3>=128?"#000":"#fff"},getLuminance:function(e){var t=parseInt(this.normaliseHex(e),16),i=38+(t>>16),n=38+(t>>8&255),o=38+(255&t);return"#"+(16777216+65536*(i<255?i<1?0:i:255)+256*(n<255?n<1?0:n:255)+(o<255?o<1?0:o:255)).toString(16).slice(1)},isMobile:function(){return/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)},isPlainObject:function(e){return"object"==typeof e&&null!==e&&e.constructor==Object},traverseDOMPath:function(e,i){return e&&e.parentNode?t.hasClass(e,i)?e:this.traverseDOMPath(e.parentNode,i):null}};e.status={deny:"deny",allow:"allow",dismiss:"dismiss"},e.transitionEnd=function(){var e=document.createElement("div"),t={t:"transitionend",OT:"oTransitionEnd",msT:"MSTransitionEnd",MozT:"transitionend",WebkitT:"webkitTransitionEnd"};for(var i in t)if(t.hasOwnProperty(i)&&void 0!==e.style[i+"ransition"])return t[i];return""}(),e.hasTransition=!!e.transitionEnd;var i=Object.keys(e.status).map(t.escapeRegExp);e.customStyles={},e.Popup=function(){var n={enabled:!0,container:null,cookie:{name:"cookieconsent_status",path:"/",domain:"",expiryDays:365,secure:!1},onPopupOpen:function(){},onPopupClose:function(){},onInitialise:function(e){},onStatusChange:function(e,t){},onRevokeChoice:function(){},onNoCookieLaw:function(e,t){},content:{header:"Cookies used on the website!",message:"This website uses cookies to ensure you get the best experience on our website.",dismiss:"Got it!",allow:"Allow cookies",deny:"Decline",link:"Learn more",href:"https://www.cookiesandyou.com",close:"&#x274c;",target:"_blank",policy:"Cookie Policy"},elements:{header:'<span class="cc-header">{{header}}</span>&nbsp;',message:'<span id="cookieconsent:desc" class="cc-message">{{message}}</span>',messagelink:'<span id="cookieconsent:desc" class="cc-message">{{message}} <a aria-label="learn more about cookies" role=button tabindex="0" class="cc-link" href="{{href}}" rel="noopener noreferrer nofollow" target="{{target}}">{{link}}</a></span>',dismiss:'<a aria-label="dismiss cookie message" role=button tabindex="0" class="cc-btn cc-dismiss">{{dismiss}}</a>',allow:'<a aria-label="allow cookies" role=button tabindex="0"  class="cc-btn cc-allow">{{allow}}</a>',deny:'<a aria-label="deny cookies" role=button tabindex="0" class="cc-btn cc-deny">{{deny}}</a>',link:'<a aria-label="learn more about cookies" role=button tabindex="0" class="cc-link" href="{{href}}" rel="noopener noreferrer nofollow" target="{{target}}">{{link}}</a>',close:'<span aria-label="dismiss cookie message" role=button tabindex="0" class="cc-close">{{close}}</span>'},window:'<div role="dialog" aria-live="polite" aria-label="cookieconsent" aria-describedby="cookieconsent:desc" class="cc-window {{classes}}">\x3c!--googleoff: all--\x3e{{children}}\x3c!--googleon: all--\x3e</div>',revokeBtn:'<div class="cc-revoke {{classes}}">{{policy}}</div>',compliance:{info:'<div class="cc-compliance">{{dismiss}}</div>',"opt-in":'<div class="cc-compliance cc-highlight">{{deny}}{{allow}}</div>',"opt-out":'<div class="cc-compliance cc-highlight">{{deny}}{{allow}}</div>'},type:"info",layouts:{basic:"{{messagelink}}{{compliance}}","basic-close":"{{messagelink}}{{compliance}}{{close}}","basic-header":"{{header}}{{message}}{{link}}{{compliance}}"},layout:"basic",position:"bottom",theme:"block",static:!1,palette:null,revokable:!1,animateRevokable:!0,showLink:!0,dismissOnScroll:!1,dismissOnTimeout:!1,dismissOnWindowClick:!1,ignoreClicksFrom:["cc-revoke","cc-btn"],autoOpen:!0,autoAttach:!0,whitelistPage:[],blacklistPage:[],overrideHTML:null};function o(){this.initialise.apply(this,arguments)}function s(e){this.openingTimeout=null,t.removeClass(e,"cc-invisible")}function r(t){t.style.display="none",t.removeEventListener(e.transitionEnd,this.afterTransition),this.afterTransition=null}function a(){var e=this.options.position.split("-"),t=[];return e.forEach(function(e){t.push("cc-"+e)}),t}function c(n){var o=this.options,s=document.createElement("div"),r=o.container&&1===o.container.nodeType?o.container:document.body;s.innerHTML=n;var a=s.children[0];return a.style.display="none",t.hasClass(a,"cc-window")&&e.hasTransition&&t.addClass(a,"cc-invisible"),this.onButtonClick=function(n){var o=t.traverseDOMPath(n.target,"cc-btn")||n.target;if(t.hasClass(o,"cc-btn")){var s=o.className.match(new RegExp("\\bcc-("+i.join("|")+")\\b")),r=s&&s[1]||!1;r&&(this.setStatus(r),this.close(!0))}t.hasClass(o,"cc-close")&&(this.setStatus(e.status.dismiss),this.close(!0));t.hasClass(o,"cc-revoke")&&this.revokeChoice()}.bind(this),a.addEventListener("click",this.onButtonClick),o.autoAttach&&(r.firstChild?r.insertBefore(a,r.firstChild):r.appendChild(a)),a}function l(e){return"000000"==(e=t.normaliseHex(e))?"#222":t.getLuminance(e)}function u(e,t){for(var i=0,n=e.length;i<n;++i){var o=e[i];if(o instanceof RegExp&&o.test(t)||"string"==typeof o&&o.length&&o===t)return!0}return!1}return o.prototype.initialise=function(i){this.options&&this.destroy(),t.deepExtend(this.options={},n),t.isPlainObject(i)&&t.deepExtend(this.options,i),function(){var t=this.options.onInitialise.bind(this);if(!window.navigator.cookieEnabled)return t(e.status.deny),!0;if(window.CookiesOK||window.navigator.CookiesOK)return t(e.status.allow),!0;var i=Object.keys(e.status),n=this.getStatus(),o=i.indexOf(n)>=0;o&&t(n);return o}.call(this)&&(this.options.enabled=!1),u(this.options.blacklistPage,location.pathname)&&(this.options.enabled=!1),u(this.options.whitelistPage,location.pathname)&&(this.options.enabled=!0);var o=this.options.window.replace("{{classes}}",function(){var i=this.options,n="top"==i.position||"bottom"==i.position?"banner":"floating";t.isMobile()&&(n="floating");var o=["cc-"+n,"cc-type-"+i.type,"cc-theme-"+i.theme];i.static&&o.push("cc-static");o.push.apply(o,a.call(this));(function(i){var n=t.hash(JSON.stringify(i)),o="cc-color-override-"+n,s=t.isPlainObject(i);this.customStyleSelector=s?o:null,s&&function(i,n,o){if(e.customStyles[i])return void++e.customStyles[i].references;var s={},r=n.popup,a=n.button,c=n.highlight;r&&(r.text=r.text?r.text:t.getContrast(r.background),r.link=r.link?r.link:r.text,s[o+".cc-window"]=["color: "+r.text,"background-color: "+r.background],s[o+".cc-revoke"]=["color: "+r.text,"background-color: "+r.background],s[o+" .cc-link,"+o+" .cc-link:active,"+o+" .cc-link:visited"]=["color: "+r.link],a&&(a.text=a.text?a.text:t.getContrast(a.background),a.border=a.border?a.border:"transparent",s[o+" .cc-btn"]=["color: "+a.text,"border-color: "+a.border,"background-color: "+a.background],a.padding&&s[o+" .cc-btn"].push("padding: "+a.padding),"transparent"!=a.background&&(s[o+" .cc-btn:hover, "+o+" .cc-btn:focus"]=["background-color: "+(a.hover||l(a.background))]),c?(c.text=c.text?c.text:t.getContrast(c.background),c.border=c.border?c.border:"transparent",s[o+" .cc-highlight .cc-btn:first-child"]=["color: "+c.text,"border-color: "+c.border,"background-color: "+c.background]):s[o+" .cc-highlight .cc-btn:first-child"]=["color: "+r.text]));var u=document.createElement("style");document.head.appendChild(u),e.customStyles[i]={references:1,element:u.sheet};var h=-1;for(var p in s)s.hasOwnProperty(p)&&u.sheet.insertRule(p+"{"+s[p].join(";")+"}",++h)}(n,i,"."+o);return s}).call(this,this.options.palette);this.customStyleSelector&&o.push(this.customStyleSelector);return o}.call(this).join(" ")).replace("{{children}}",function(){var e={},i=this.options;i.showLink||(i.elements.link="",i.elements.messagelink=i.elements.message);Object.keys(i.elements).forEach(function(n){e[n]=t.interpolateString(i.elements[n],function(e){var t=i.content[e];return e&&"string"==typeof t&&t.length?t:""})});var n=i.compliance[i.type];n||(n=i.compliance.info);e.compliance=t.interpolateString(n,function(t){return e[t]});var o=i.layouts[i.layout];o||(o=i.layouts.basic);return t.interpolateString(o,function(t){return e[t]})}.call(this)),s=this.options.overrideHTML;if("string"==typeof s&&s.length&&(o=s),this.options.static){var r=c.call(this,'<div class="cc-grower">'+o+"</div>");r.style.display="",this.element=r.firstChild,this.element.style.display="none",t.addClass(this.element,"cc-invisible")}else this.element=c.call(this,o);(function(){var i=this.setStatus.bind(this),n=this.close.bind(this),o=this.options.dismissOnTimeout;"number"==typeof o&&o>=0&&(this.dismissTimeout=window.setTimeout(function(){i(e.status.dismiss),n(!0)},Math.floor(o)));var s=this.options.dismissOnScroll;if("number"==typeof s&&s>=0){var r=function(t){window.pageYOffset>Math.floor(s)&&(i(e.status.dismiss),n(!0),window.removeEventListener("scroll",r),this.onWindowScroll=null)};this.options.enabled&&(this.onWindowScroll=r,window.addEventListener("scroll",r))}var a=this.options.dismissOnWindowClick,c=this.options.ignoreClicksFrom;if(a){var l=function(o){for(var s=!1,r=o.path.length,a=c.length,u=0;u<r;u++)if(!s)for(var h=0;h<a;h++)s||(s=t.hasClass(o.path[u],c[h]));s||(i(e.status.dismiss),n(!0),window.removeEventListener("click",l),window.removeEventListener("touchend",l),this.onWindowClick=null)}.bind(this);this.options.enabled&&(this.onWindowClick=l,window.addEventListener("click",l),window.addEventListener("touchend",l))}}).call(this),function(){"info"!=this.options.type&&(this.options.revokable=!0);t.isMobile()&&(this.options.animateRevokable=!1);if(this.options.revokable){var e=a.call(this);this.options.animateRevokable&&e.push("cc-animate"),this.customStyleSelector&&e.push(this.customStyleSelector);var i=this.options.revokeBtn.replace("{{classes}}",e.join(" ")).replace("{{policy}}",this.options.content.policy);this.revokeBtn=c.call(this,i);var n=this.revokeBtn;if(this.options.animateRevokable){var o=t.throttle(function(e){var i=!1,o=window.innerHeight-20;t.hasClass(n,"cc-top")&&e.clientY<20&&(i=!0),t.hasClass(n,"cc-bottom")&&e.clientY>o&&(i=!0),i?t.hasClass(n,"cc-active")||t.addClass(n,"cc-active"):t.hasClass(n,"cc-active")&&t.removeClass(n,"cc-active")},200);this.onMouseMove=o,window.addEventListener("mousemove",o)}}}.call(this),this.options.autoOpen&&this.autoOpen()},o.prototype.destroy=function(){this.onButtonClick&&this.element&&(this.element.removeEventListener("click",this.onButtonClick),this.onButtonClick=null),this.dismissTimeout&&(clearTimeout(this.dismissTimeout),this.dismissTimeout=null),this.onWindowScroll&&(window.removeEventListener("scroll",this.onWindowScroll),this.onWindowScroll=null),this.onWindowClick&&(window.removeEventListener("click",this.onWindowClick),this.onWindowClick=null),this.onMouseMove&&(window.removeEventListener("mousemove",this.onMouseMove),this.onMouseMove=null),this.element&&this.element.parentNode&&this.element.parentNode.removeChild(this.element),this.element=null,this.revokeBtn&&this.revokeBtn.parentNode&&this.revokeBtn.parentNode.removeChild(this.revokeBtn),this.revokeBtn=null,function(i){if(t.isPlainObject(i)){var n=t.hash(JSON.stringify(i)),o=e.customStyles[n];if(o&&!--o.references){var s=o.element.ownerNode;s&&s.parentNode&&s.parentNode.removeChild(s),e.customStyles[n]=null}}}(this.options.palette),this.options=null},o.prototype.open=function(t){if(this.element)return this.isOpen()||(e.hasTransition?this.fadeIn():this.element.style.display="",this.options.revokable&&this.toggleRevokeButton(),this.options.onPopupOpen.call(this)),this},o.prototype.close=function(t){if(this.element)return this.isOpen()&&(e.hasTransition?this.fadeOut():this.element.style.display="none",t&&this.options.revokable&&this.toggleRevokeButton(!0),this.options.onPopupClose.call(this)),this},o.prototype.fadeIn=function(){var i=this.element;if(e.hasTransition&&i&&(this.afterTransition&&r.call(this,i),t.hasClass(i,"cc-invisible"))){if(i.style.display="",this.options.static){var n=this.element.clientHeight;this.element.parentNode.style.maxHeight=n+"px"}this.openingTimeout=setTimeout(s.bind(this,i),20)}},o.prototype.fadeOut=function(){var i=this.element;e.hasTransition&&i&&(this.openingTimeout&&(clearTimeout(this.openingTimeout),s.bind(this,i)),t.hasClass(i,"cc-invisible")||(this.options.static&&(this.element.parentNode.style.maxHeight=""),this.afterTransition=r.bind(this,i),i.addEventListener(e.transitionEnd,this.afterTransition),t.addClass(i,"cc-invisible")))},o.prototype.isOpen=function(){return this.element&&""==this.element.style.display&&(!e.hasTransition||!t.hasClass(this.element,"cc-invisible"))},o.prototype.toggleRevokeButton=function(e){this.revokeBtn&&(this.revokeBtn.style.display=e?"":"none")},o.prototype.revokeChoice=function(e){this.options.enabled=!0,this.clearStatus(),this.options.onRevokeChoice.call(this),e||this.autoOpen()},o.prototype.hasAnswered=function(t){return Object.keys(e.status).indexOf(this.getStatus())>=0},o.prototype.hasConsented=function(t){var i=this.getStatus();return i==e.status.allow||i==e.status.dismiss},o.prototype.autoOpen=function(e){!this.hasAnswered()&&this.options.enabled?this.open():this.hasAnswered()&&this.options.revokable&&this.toggleRevokeButton(!0)},o.prototype.setStatus=function(i){var n=this.options.cookie,o=t.getCookie(n.name),s=Object.keys(e.status).indexOf(o)>=0;Object.keys(e.status).indexOf(i)>=0?(t.setCookie(n.name,i,n.expiryDays,n.domain,n.path,n.secure),this.options.onStatusChange.call(this,i,s)):this.clearStatus()},o.prototype.getStatus=function(){return t.getCookie(this.options.cookie.name)},o.prototype.clearStatus=function(){var e=this.options.cookie;t.setCookie(e.name,"",-1,e.domain,e.path)},o}(),e.Location=function(){var e={timeout:5e3,services:["ipinfo"],serviceDefinitions:{ipinfo:function(){return{url:"//ipinfo.io",headers:["Accept: application/json"],callback:function(e,t){try{var i=JSON.parse(t);return i.error?s(i):{code:i.country}}catch(e){return s({error:"Invalid response ("+e+")"})}}}},ipinfodb:function(e){return{url:"//api.ipinfodb.com/v3/ip-country/?key={api_key}&format=json&callback={callback}",isScript:!0,callback:function(e,t){try{var i=JSON.parse(t);return"ERROR"==i.statusCode?s({error:i.statusMessage}):{code:i.countryCode}}catch(e){return s({error:"Invalid response ("+e+")"})}}}},maxmind:function(){return{url:"//js.maxmind.com/js/apis/geoip2/v2.1/geoip2.js",isScript:!0,callback:function(e){window.geoip2?geoip2.country(function(t){try{e({code:t.country.iso_code})}catch(t){e(s(t))}},function(t){e(s(t))}):e(new Error("Unexpected response format. The downloaded script should have exported `geoip2` to the global scope"))}}}}};function i(i){t.deepExtend(this.options={},e),t.isPlainObject(i)&&t.deepExtend(this.options,i),this.currentServiceIndex=-1}function n(e,t,i){var n,o=document.createElement("script");o.type="text/"+(e.type||"javascript"),o.src=e.src||e,o.async=!1,o.onreadystatechange=o.onload=function(){var e=o.readyState;clearTimeout(n),t.done||e&&!/loaded|complete/.test(e)||(t.done=!0,t(),o.onreadystatechange=o.onload=null)},document.body.appendChild(o),n=setTimeout(function(){t.done=!0,t(),o.onreadystatechange=o.onload=null},i)}function o(e,t,i,n,o){var s=new(window.XMLHttpRequest||window.ActiveXObject)("MSXML2.XMLHTTP.3.0");if(s.open(n?"POST":"GET",e,1),s.setRequestHeader("Content-type","application/x-www-form-urlencoded"),Array.isArray(o))for(var r=0,a=o.length;r<a;++r){var c=o[r].split(":",2);s.setRequestHeader(c[0].replace(/^\s+|\s+$/g,""),c[1].replace(/^\s+|\s+$/g,""))}"function"==typeof t&&(s.onreadystatechange=function(){s.readyState>3&&t(s)}),s.send(n)}function s(e){return new Error("Error ["+(e.code||"UNKNOWN")+"]: "+e.error)}return i.prototype.getNextService=function(){var e;do{e=this.getServiceByIdx(++this.currentServiceIndex)}while(this.currentServiceIndex<this.options.services.length&&!e);return e},i.prototype.getServiceByIdx=function(e){var i=this.options.services[e];if("function"==typeof i){var n=i();return n.name&&t.deepExtend(n,this.options.serviceDefinitions[n.name](n)),n}return"string"==typeof i?this.options.serviceDefinitions[i]():t.isPlainObject(i)?this.options.serviceDefinitions[i.name](i):null},i.prototype.locate=function(e,t){var i=this.getNextService();i?(this.callbackComplete=e,this.callbackError=t,this.runService(i,this.runNextServiceOnError.bind(this))):t(new Error("No services to run"))},i.prototype.setupUrl=function(e){var t=this.getCurrentServiceOpts();return e.url.replace(/\{(.*?)\}/g,function(i,n){if("callback"===n){var o="callback"+Date.now();return window[o]=function(t){e.__JSONP_DATA=JSON.stringify(t)},o}if(n in t.interpolateUrl)return t.interpolateUrl[n]})},i.prototype.runService=function(e,t){var i=this;e&&e.url&&e.callback&&(e.isScript?n:o)(this.setupUrl(e),function(n){var o=n?n.responseText:"";e.__JSONP_DATA&&(o=e.__JSONP_DATA,delete e.__JSONP_DATA),i.runServiceCallback.call(i,t,e,o)},this.options.timeout,e.data,e.headers)},i.prototype.runServiceCallback=function(e,t,i){var n=this,o=t.callback(function(t){o||n.onServiceResult.call(n,e,t)},i);o&&this.onServiceResult.call(this,e,o)},i.prototype.onServiceResult=function(e,t){t instanceof Error||t&&t.error?e.call(this,t,null):e.call(this,null,t)},i.prototype.runNextServiceOnError=function(e,t){if(e){this.logError(e);var i=this.getNextService();i?this.runService(i,this.runNextServiceOnError.bind(this)):this.completeService.call(this,this.callbackError,new Error("All services failed"))}else this.completeService.call(this,this.callbackComplete,t)},i.prototype.getCurrentServiceOpts=function(){var e=this.options.services[this.currentServiceIndex];return"string"==typeof e?{name:e}:"function"==typeof e?e():t.isPlainObject(e)?e:{}},i.prototype.completeService=function(e,t){this.currentServiceIndex=-1,e&&e(t)},i.prototype.logError=function(e){var t=this.currentServiceIndex,i=this.getServiceByIdx(t);console.warn("The service["+t+"] ("+i.url+") responded with the following error",e)},i}(),e.Law=function(){var e={regionalLaw:!0,hasLaw:["AT","BE","BG","HR","CZ","CY","DK","EE","FI","FR","DE","EL","HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","SK","ES","SE","GB","UK","GR","EU"],revokable:["HR","CY","DK","EE","FR","DE","LV","LT","NL","PT","ES"],explicitAction:["HR","IT","ES"]};function i(e){this.initialise.apply(this,arguments)}return i.prototype.initialise=function(i){t.deepExtend(this.options={},e),t.isPlainObject(i)&&t.deepExtend(this.options,i)},i.prototype.get=function(e){var t=this.options;return{hasLaw:t.hasLaw.indexOf(e)>=0,revokable:t.revokable.indexOf(e)>=0,explicitAction:t.explicitAction.indexOf(e)>=0}},i.prototype.applyLaw=function(e,t){var i=this.get(t);return i.hasLaw||(e.enabled=!1,"function"==typeof e.onNoCookieLaw&&e.onNoCookieLaw(t,i)),this.options.regionalLaw&&(i.revokable&&(e.revokable=!0),i.explicitAction&&(e.dismissOnScroll=!1,e.dismissOnTimeout=!1)),e},i}(),e.initialise=function(i,n,o){var s=new e.Law(i.law);n||(n=function(){}),o||(o=function(){});var r=Object.keys(e.status),a=t.getCookie("cookieconsent_status");r.indexOf(a)>=0?n(new e.Popup(i)):e.getCountryCode(i,function(t){delete i.law,delete i.location,t.code&&(i=s.applyLaw(i,t.code)),n(new e.Popup(i))},function(t){delete i.law,delete i.location,o(t,new e.Popup(i))})},e.getCountryCode=function(t,i,n){t.law&&t.law.countryCode?i({code:t.law.countryCode}):t.location?new e.Location(t.location).locate(function(e){i(e||{})},n):i({})},e.utils=t,e.hasInitialised=!0,window.cookieconsent=e}}(window.cookieconsent||{});
window.cookieconsent.initialise({
 onPopupOpen:function(){this.element?.setAttribute('aria-label',t('Файлы cookie'));},
 cookie: {expiryDays:365,secure:location.protocol==='https:'},
 elements: {
  dismiss:'<button type="button" aria-label="{{dismiss}}" class="cc-btn cc-dismiss">{{dismiss}}</button>',
  messagelink:'<span id="cookieconsent:desc" class="cc-message"><svg class="cookie-icon" width="26" height="26" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M20.9 12.8A9 9 0 1 1 11.2 3.1 4 4 0 0 0 16 7.8a4 4 0 0 0 4.9 5Z"/><circle cx="7.5" cy="10" r=".8"/><circle cx="8" cy="15.5" r=".8"/><circle cx="13.5" cy="15" r=".8"/><circle cx="12" cy="10.5" r=".6"/></svg><span class="cookie-copy">{{message}} <a class="cc-link" href="{{href}}" target="_blank" rel="noopener noreferrer">{{link}}</a></span></span>'
 },
 palette: {
  popup: {background:'rgba(6, 75, 53, 0.75)',text:'#ffffff'},
  button: {background:'#ffffff',text:'#064b35'},
  highlight: {background:'#e2f4e9',text:'#064b35'}
 },
 content: {
  message:t('Этот сайт использует файлы cookie для сохранения ваших настроек.'),
  dismiss:t('Понятно'),
  link:t('Подробнее'),
  href:'https://www.cookiesandyou.com/about-cookies/'
 }
});

restoreLanguagePosition();
