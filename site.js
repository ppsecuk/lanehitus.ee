const chooser = document.querySelector('#choose-form');
const details = document.querySelector('#details-form');
const description = document.querySelector('#description');
const status = document.querySelector('#status');
let selected = '';
let lastTile = null;
document.querySelectorAll('[data-service]').forEach(tile => {
  tile.addEventListener('click', () => {
    selected = tile.dataset.service;
    lastTile = tile;
    document.querySelector('#selected-service').textContent = selected;
    chooser.hidden = true;
    details.hidden = false;
    tile.setAttribute('aria-expanded', 'true');
    status.textContent = '';
    description.placeholder = selected === 'Терраса' ? 'Например: заменить настил террасы около 15 м² в Таллинне.' : 'Расскажите, что нужно сделать и какой результат вы хотите получить.';
    document.querySelector('#details-title').focus();
  });
});
document.querySelector('#change-service').addEventListener('click', () => {
  details.hidden = true;
  chooser.hidden = false;
  if (lastTile) { lastTile.setAttribute('aria-expanded', 'false'); lastTile.focus(); }
});
function getMessage() {
  const text = description.value.trim();
  const location = document.querySelector('#location').value.trim();
  return selected + '\n\n' + text + (location ? '\n\nМестоположение: ' + location : '');
}
details.addEventListener('submit', event => {
  event.preventDefault();
  if (!description.value.trim()) { status.textContent = 'Кратко опишите задачу.'; description.focus(); return; }
  window.location.href = 'mailto:lebjodkin.toll68@gmail.com?subject=' + encodeURIComponent(selected) + '&body=' + encodeURIComponent(getMessage());
  status.textContent = 'Письмо подготовлено. Отправьте его из своей почтовой программы.';
});
document.querySelector('#copy-message').addEventListener('click', async () => {
  if (!description.value.trim()) { status.textContent = 'Сначала добавьте описание задачи.'; description.focus(); return; }
  try {
    await navigator.clipboard.writeText(getMessage());
    status.textContent = 'Описание скопировано. Вставьте его в письмо на lebjodkin.toll68@gmail.com.';
  } catch {
    status.textContent = 'Не удалось скопировать автоматически. Выделите описание и скопируйте его вручную.';
    description.focus(); description.select();
  }
});

const consultDialog = document.querySelector('#consult-dialog');
const consultOpen = document.querySelector('#consult-open');
consultOpen.addEventListener('click', () => consultDialog.showModal());
document.querySelector('#consult-close').addEventListener('click', () => consultDialog.close());
consultDialog.addEventListener('click', event => {
  if (event.target !== consultDialog) return;
  const rect = consultDialog.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) consultDialog.close();
});
consultDialog.addEventListener('close', () => consultOpen.focus());

const serviceGallery = document.querySelector('#services-gallery');
const previousService = document.querySelector('#services-prev');
const nextService = document.querySelector('#services-next');
function updateGalleryControls() {
  previousService.disabled = serviceGallery.scrollLeft <= 2;
  nextService.disabled = serviceGallery.scrollLeft + serviceGallery.clientWidth >= serviceGallery.scrollWidth - 2;
}
function moveGallery(direction) {
  const slide = serviceGallery.querySelector('.photo-tile');
  const gap = parseFloat(getComputedStyle(serviceGallery).columnGap) || 0;
  serviceGallery.scrollBy({ left: direction * (slide.getBoundingClientRect().width + gap), behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
}
previousService.addEventListener('click', () => moveGallery(-1));
nextService.addEventListener('click', () => moveGallery(1));
serviceGallery.addEventListener('scroll', updateGalleryControls, { passive: true });
serviceGallery.addEventListener('keydown', event => {
  if (event.target !== serviceGallery) return;
  if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
    event.preventDefault(); moveGallery(event.key === 'ArrowRight' ? 1 : -1);
  }
});
new ResizeObserver(updateGalleryControls).observe(serviceGallery);
updateGalleryControls();
