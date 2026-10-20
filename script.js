// Add verified contact details here before publishing. No information is sent by default.
const siteConfig = { email: 'lebjodkin.toll68@gmail.com', phone: '+3725232477', serviceArea: '' };
const form = document.querySelector('#brief-form');
const service = document.querySelector('#service');
const status = document.querySelector('#form-status');
const links = document.querySelector('#contact-links');
for (const [value, protocol] of [[siteConfig.phone, 'tel:'], [siteConfig.email, 'mailto:']]) {
  if (!value) continue;
  const link = document.createElement('a');
  link.textContent = value;
  link.href = protocol + value;
  links.append(link);
}
if (siteConfig.serviceArea) {
  const area = document.createElement('p');
  area.textContent = siteConfig.serviceArea;
  links.append(area);
}
if (siteConfig.email) {
  form.querySelector('button').textContent = 'Открыть письмо ↗';
  document.querySelector('#form-note').textContent = 'Откроется ваша почтовая программа с описанием задачи. Отправьте письмо, когда будете готовы.';
}
document.querySelectorAll('[data-service]').forEach(link => {
  link.addEventListener('click', () => { service.value = link.dataset.service; });
});
form.addEventListener('submit', event => {
  event.preventDefault();
  const description = document.querySelector('#description').value.trim();
  if (!description) { status.textContent = 'Добавьте короткое описание задачи.'; return; }
  const brief = `${service.value}\n\n${description}`;
  if (siteConfig.email) {
    location.href = `mailto:${siteConfig.email}?subject=${encodeURIComponent('Задача: ' + service.value)}&body=${encodeURIComponent(brief)}`;
    status.textContent = 'Письмо подготовлено для открытия в почтовой программе. Оно ещё не отправлено.';
    return;
  }
  const url = URL.createObjectURL(new Blob([brief], { type: 'text/plain;charset=utf-8' }));
  const download = document.createElement('a');
  download.href = url;
  download.download = 'opisanie-rabot.txt';
  document.body.append(download);
  download.click();
  download.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  status.textContent = 'Описание подготовлено для скачивания. Заявка не отправлена.';
});