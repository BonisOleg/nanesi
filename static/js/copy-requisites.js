document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-copy-text]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy-text') || '';
      if (!text) return;
      var label = btn.getAttribute('data-copy-label') || 'Копіювати';
      var copied = btn.getAttribute('data-copied-label') || 'Скопійовано';

      function markCopied() {
        btn.textContent = copied;
        btn.classList.add('is-copied');
        window.setTimeout(function () {
          btn.textContent = label;
          btn.classList.remove('is-copied');
        }, 1800);
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(markCopied).catch(function () {
          fallbackCopy(text, markCopied);
        });
      } else {
        fallbackCopy(text, markCopied);
      }
    });
  });

  function fallbackCopy(text, onDone) {
    var area = document.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.left = '-9999px';
    area.style.top = '0';
    document.body.appendChild(area);
    area.select();
    area.setSelectionRange(0, area.value.length);
    try {
      document.execCommand('copy');
      onDone();
    } catch (e) {
      /* ignore */
    }
    document.body.removeChild(area);
  }
});
