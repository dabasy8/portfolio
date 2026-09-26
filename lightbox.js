// Lightbox: click any gallery thumbnail to view the full-size image/video.
// Arrow keys / swipe move through the current project; Esc closes.
(function () {
  var items = Array.prototype.slice.call(document.querySelectorAll('.gallery-item'));
  if (!items.length) return;

  var box = document.createElement('div');
  box.className = 'lightbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-modal', 'true');
  box.innerHTML =
    '<span class="lightbox-counter"></span>' +
    '<button class="lightbox-close" aria-label="Close">&times;</button>' +
    '<button class="lightbox-prev" aria-label="Previous">&#8249;</button>' +
    '<button class="lightbox-next" aria-label="Next">&#8250;</button>' +
    '<figure class="lightbox-figure"><div class="lightbox-media"></div>' +
    '<figcaption class="lightbox-caption"></figcaption></figure>';
  document.body.appendChild(box);

  var media = box.querySelector('.lightbox-media');
  var caption = box.querySelector('.lightbox-caption');
  var counter = box.querySelector('.lightbox-counter');
  var group = [], index = 0, lastFocus = null;

  function show(i) {
    index = (i + group.length) % group.length;
    var item = group[index];
    var href = item.getAttribute('href');
    var thumb = item.querySelector('img');
    var project = item.closest('.project-block');
    var title = project ? project.querySelector('h3').textContent : '';
    var cap = item.querySelector('.caption');
    media.innerHTML = '';
    var el;
    if (/\.(mp4|webm|mov)$/i.test(href)) {
      el = document.createElement('video');
      el.src = href; el.controls = true; el.autoplay = true; el.loop = true; el.muted = true;
      el.setAttribute('playsinline', '');
    } else {
      el = document.createElement('img');
      // Show the light thumbnail instantly, then swap in the full-size original.
      el.src = thumb ? thumb.currentSrc || thumb.src : href;
      el.alt = thumb ? thumb.alt : '';
      var full = new Image();
      full.onload = function () { if (group[index] === item) el.src = href; };
      full.src = href;
    }
    media.appendChild(el);
    caption.textContent = [title, cap ? cap.textContent : ''].filter(Boolean).join(' — ');
    counter.textContent = (index + 1) + ' / ' + group.length;
    var multi = group.length > 1;
    box.querySelector('.lightbox-prev').hidden = !multi;
    box.querySelector('.lightbox-next').hidden = !multi;
  }

  function open(item) {
    var project = item.closest('.project-block') || document;
    group = Array.prototype.slice.call(project.querySelectorAll('.gallery-item'));
    lastFocus = document.activeElement;
    box.classList.add('open');
    document.body.classList.add('lightbox-lock');
    show(group.indexOf(item));
    box.querySelector('.lightbox-close').focus();
  }

  function close() {
    box.classList.remove('open');
    document.body.classList.remove('lightbox-lock');
    media.innerHTML = '';
    if (lastFocus) lastFocus.focus();
  }

  items.forEach(function (item) {
    item.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return; // allow open-in-new-tab
      e.preventDefault();
      open(item);
    });
  });

  box.querySelector('.lightbox-close').addEventListener('click', close);
  box.querySelector('.lightbox-prev').addEventListener('click', function () { show(index - 1); });
  box.querySelector('.lightbox-next').addEventListener('click', function () { show(index + 1); });
  box.addEventListener('click', function (e) { if (e.target === box) close(); });

  document.addEventListener('keydown', function (e) {
    if (!box.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(index - 1);
    else if (e.key === 'ArrowRight') show(index + 1);
  });

  var startX = null;
  box.addEventListener('touchstart', function (e) { startX = e.touches[0].clientX; }, { passive: true });
  box.addEventListener('touchend', function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    startX = null;
  });
})();
