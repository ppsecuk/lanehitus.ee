const choose = document.querySelector('#choose-step');
const details = document.querySelector('#details-step');
const title = document.querySelector('#details-title');
const description = document.querySelector('#description');
const status = document.querySelector('#status');
let selected = '';
let lastChoice = null;
const help = {
  'Терраса': 'Расскажите о размерах, состоянии террасы и желаемом результате.',
  'Работы по дереву': 'Какие элементы нужно сделать, обновить или восстановить?',
  'Ремонт квартиры': 'Что хотите изменить: стены, пол, отдельную комнату или всю квартиру?',
  'Другая задача': 'Опишите вашу идею. Уточним детали и возможность выполнения.',
  'Консультация': 'Готовый план не нужен. Задайте вопрос или позвоните нам напрямую.'
};
document.querySelectorAll('[data-service]').forEach(button => {
  button.addEventListener('click', () => {
    selected = button.dataset.service;
    lastChoice = button;
    title.textContent = selected;
    document.querySelector('#details-help').textContent = help[selected];
    status.textContent = '';
    choose.hidden = true;
    details.hidden = false;
    document.querySelector('#step-one').removeAttribute('aria-current');
    document.querySelector('#step-two').setAttribute('aria-current', 'step');
    title.focus();
  });
});
document.querySelector('#go-back').addEventListener('click', () => {
  details.hidden = true;
  choose.hidden = false;
  document.querySelector('#step-two').removeAttribute('aria-current');
  document.querySelector('#step-one').setAttribute('aria-current', 'step');
  lastChoice?.focus();
});
document.querySelector('#request-form').addEventListener('submit', event => {
  event.preventDefault();
  const text = description.value.trim();
  if (!text) { status.textContent = 'Опишите задачу или задайте вопрос.'; description.focus(); return; }
  const place = document.querySelector('#place').value.trim();
  const body = text + (place ? '\n\nМестоположение: ' + place : '');
  window.location.href = 'mailto:lebjodkin.toll68@gmail.com?subject=' + encodeURIComponent(selected) + '&body=' + encodeURIComponent(body);
  status.textContent = 'Письмо подготовлено для почтовой программы. Оно ещё не отправлено.';
});
