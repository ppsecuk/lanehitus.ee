const quickContacts = document.querySelector('#quick-contact-links');
for (const link of document.querySelectorAll('#contact-links a')) {
  if (quickContacts.querySelector(`a[href="${link.getAttribute('href')}"]`)) continue;
  quickContacts.append(link.cloneNode(true));
}
const contactTitle = document.querySelector('#contact-title');
const description = document.querySelector('#description');
function updateContactPrompt() {
  const consulting = service.value === 'Консультация';
  contactTitle.textContent = consulting ? 'Давайте обсудим ваш вопрос' : 'Расскажите о задаче';
  description.placeholder = consulting ? 'Что вы хотите узнать или обсудить?' : 'Что нужно сделать, где находится объект и какие сроки вам подходят?';
}
service.addEventListener('change', updateContactPrompt);
document.querySelectorAll('[data-service]').forEach(link => {
  link.addEventListener('click', () => {
    updateContactPrompt();
    description.focus({ preventScroll: true });
  });
});
