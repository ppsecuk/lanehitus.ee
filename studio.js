const services = {
  terrace: { title: 'Терраса', category: 'БОЛЬШЕ МЕСТА ДЛЯ ОТДЫХА', description: 'Новый настил, ступени или обновление существующей террасы. Обсудим размеры, материалы и ваши пожелания.', button: 'Обсудить террасу', image: 'terrace.svg', alt: 'Иллюстрация деревянной террасы', note: 'Иллюстрация · не выполненный проект LAN OÜ', index: '01 / 04' },
  wood: { title: 'Работы по дереву', category: 'НАТУРАЛЬНЫЕ МАТЕРИАЛЫ', description: 'Обшивка, деревянные детали и восстановление элементов. Расскажите, что нужно сделать или отремонтировать.', button: 'Обсудить работу', image: 'preview-room.jpg', alt: 'Демонстрационный интерьер в натуральных оттенках', index: '02 / 04' },
  renovation: { title: 'Ремонт квартиры', category: 'ОБНОВИТЬ ПРОСТРАНСТВО', description: 'Освежить стены, заменить пол или обновить комнату. Расскажите, что хотите изменить.', button: 'Обсудить ремонт', image: 'preview-interior.jpg', alt: 'Демонстрационный интерьер светлой гостиной', index: '03 / 04' },
  other: { title: 'Ваша задача', category: 'НЕ НАШЛИ НУЖНУЮ УСЛУГУ?', description: 'Опишите, с чем нужна помощь. Обсудим детали и уточним, сможем ли взяться за работу.', button: 'Рассказать о задаче', image: 'preview-home.jpg', alt: 'Демонстрационный жилой интерьер', index: '04 / 04' },
  consultation: { title: 'Давайте поговорим', category: 'КОНСУЛЬТАЦИЯ', description: 'Ещё нет готового плана? Позвоните по номеру +372 523 2477 или напишите, что хотите обсудить.', button: 'Задать вопрос', image: 'preview-interior.jpg', alt: 'Демонстрационный интерьер светлой гостиной', index: '↗' }
};
let selected = 'renovation';
const form = document.querySelector('#brief-form');
const description = document.querySelector('#description');
const openButton = document.querySelector('#open-brief');
const status = document.querySelector('#form-status');
function selectService(key) {
  selected = key;
  const item = services[key];
  document.querySelector('#detail-category').textContent = item.category;
  document.querySelector('#detail-title').textContent = item.title;
  document.querySelector('#detail-description').textContent = item.description;
  openButton.textContent = item.button + ' ↗';
  const photo = document.querySelector('#service-photo');
  photo.src = item.image;
  photo.alt = item.alt;
  document.querySelector('#photo-note').textContent = item.note || 'Фото для настроения · не выполненный проект LAN OÜ';
  document.querySelector('#photo-index').textContent = item.index;
  status.textContent = '';
  document.querySelectorAll('input[name="service"]').forEach(input => { input.checked = input.value === key; });
}
function openForm() {
  form.hidden = false;
  openButton.setAttribute('aria-expanded', 'true');
  description.focus({ preventScroll: true });
  form.scrollIntoView({ behavior: 'auto', block: 'nearest' });
}
document.querySelectorAll('input[name="service"]').forEach(input => {
  input.addEventListener('change', () => {
    selectService(input.value);
    if (window.matchMedia('(max-width:720px)').matches) document.querySelector('.visual-panel').scrollIntoView({ behavior: 'auto', block: 'start' });
  });
});
openButton.addEventListener('click', openForm);
document.querySelector('#consult-button').addEventListener('click', () => { selectService('consultation'); openForm(); });
document.querySelector('#close-brief').addEventListener('click', () => {
  form.hidden = true;
  openButton.setAttribute('aria-expanded', 'false');
  openButton.focus();
});
form.addEventListener('submit', event => {
  event.preventDefault();
  const text = description.value.trim();
  if (!text) { status.textContent = 'Добавьте описание или ваш вопрос.'; description.focus(); return; }
  const subject = selected === 'consultation' ? 'Консультация' : services[selected].title;
  window.location.href = 'mailto:lebjodkin.toll68@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(text);
  status.textContent = 'Письмо подготовлено для почтовой программы. Оно ещё не отправлено.';
});
