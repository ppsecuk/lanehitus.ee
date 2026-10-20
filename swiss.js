const menuToggle = document.querySelector('#menu-toggle');
const menu = document.querySelector('#site-menu');
const dialog = document.querySelector('#enquiry');
const service = document.querySelector('#service');
const description = document.querySelector('#description');
const status = document.querySelector('#form-status');
let opener = null;
function closeMenu() {
  menu.hidden = true;
  menuToggle.setAttribute('aria-expanded', 'false');
  menuToggle.setAttribute('aria-label', 'Открыть меню');
}
menuToggle.addEventListener('click', () => {
  const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
  menu.hidden = isOpen;
  menuToggle.setAttribute('aria-expanded', String(!isOpen));
  menuToggle.setAttribute('aria-label', isOpen ? 'Открыть меню' : 'Закрыть меню');
});
menu.querySelector('a').addEventListener('click', closeMenu);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && !menu.hidden) { closeMenu(); menuToggle.focus(); }
});
document.querySelectorAll('[data-service]').forEach(button => {
  button.addEventListener('click', () => {
    opener = menu.contains(button) ? menuToggle : button;
    closeMenu();
    service.value = button.dataset.service;
    status.textContent = '';
    dialog.showModal();
  });
});
document.querySelector('#dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('close', () => opener?.focus());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const r = dialog.getBoundingClientRect();
  if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
});
function brief() { return service.value + '\n\n' + description.value.trim(); }
document.querySelector('#enquiry-form').addEventListener('submit', event => {
  event.preventDefault();
  if (!description.value.trim()) { status.textContent = 'Напишите короткое описание или ваш вопрос.'; description.focus(); return; }
  window.location.href = 'mailto:lebjodkin.toll68@gmail.com?subject=' + encodeURIComponent(service.value) + '&body=' + encodeURIComponent(brief());
  status.textContent = 'Письмо подготовлено. Отправьте его из почтовой программы.';
});
document.querySelector('#copy-brief').addEventListener('click', async () => {
  if (!description.value.trim()) { status.textContent = 'Сначала добавьте описание задачи.'; description.focus(); return; }
  try { await navigator.clipboard.writeText(brief()); status.textContent = 'Описание скопировано. Вставьте его в письмо на lebjodkin.toll68@gmail.com.'; }
  catch { status.textContent = 'Выделите и скопируйте описание вручную.'; description.focus(); description.select(); }
});
