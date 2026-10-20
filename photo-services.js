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
