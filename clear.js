const chooser = document.querySelector('#choose-form');
const details = document.querySelector('#details-form');
const description = document.querySelector('#description');
const status = document.querySelector('#status');
const continueButton = document.querySelector('#continue');
let selected = '';
chooser.addEventListener('submit', event => {
  event.preventDefault();
  const choice = chooser.querySelector('input[name="service"]:checked');
  if (!choice) return;
  selected = choice.value;
  document.querySelector('#selected-service').textContent = selected;
  chooser.hidden = true;
  details.hidden = false;
  continueButton.setAttribute('aria-expanded', 'true');
  status.textContent = '';
  document.querySelector('#details-title').focus();
});
document.querySelector('#change-service').addEventListener('click', () => {
  details.hidden = true;
  chooser.hidden = false;
  continueButton.setAttribute('aria-expanded', 'false');
  chooser.querySelector('input[name="service"]:checked')?.focus();
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
