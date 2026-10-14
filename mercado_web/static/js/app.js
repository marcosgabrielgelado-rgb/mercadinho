// Small progressive enhancements for the catalogue.
document.addEventListener('DOMContentLoaded', () => {
  const search = document.querySelector('input[type="search"]');
  if (search) {
    search.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') search.value = '';
    });
  }
  document.querySelectorAll('.flash').forEach((flash) => {
    window.setTimeout(() => {
      flash.classList.add('flash-leave');
      window.setTimeout(() => flash.remove(), 350);
    }, 5000);
  });
});
