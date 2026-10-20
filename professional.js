const service = document.querySelector('#service');
const description = document.querySelector('#description');
const status = document.querySelector('#status');
document.querySelectorAll('[data-service]').forEach(link => {
  link.addEventListener('click', () => {
    service.value = link.dataset.service;
    status.textContent = '';
    description.focus({ preventScroll: true });
  });
});
document.querySelector('#request-form').addEventListener('submit', event => {
  event.preventDefault();
  const text = description.value.trim();
  if (!text) { status.textContent = 'Опишите задачу или задайте вопрос.'; description.focus(); return; }
  window.location.href = 'mailto:lebjodkin.toll68@gmail.com?subject=' + encodeURIComponent(service.value) + '&body=' + encodeURIComponent(text);
  status.textContent = 'Письмо подготовлено для почтовой программы. Оно ещё не отправлено.';
});
