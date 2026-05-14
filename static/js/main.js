/* ═══════════════════════════════════════════════════════════════════════════
   ANITA NEW STYLE — JavaScript principal
   ═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-cerrar alertas después de 5 segundos ────────────────────────────
  document.querySelectorAll('.alert-ans.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // ── Agregar al carrito con AJAX ──────────────────────────────────────────
  document.querySelectorAll('form.form-agregar-carrito, form[action*="agregar"]').forEach(form => {
    form.addEventListener('submit', function (e) {
      // Solo AJAX en tarjetas de producto (no en detalle)
      if (form.closest('.producto-card')) {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        const textoOrig = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        btn.disabled = true;

        fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(r => r.json())
          .then(data => {
            if (data.ok) {
              // Actualizar contador del carrito
              const badges = document.querySelectorAll('.badge-carrito');
              badges.forEach(b => {
                b.textContent = data.cant_carrito;
                b.style.display = data.cant_carrito > 0 ? 'flex' : 'none';
                // Animación bounce
                b.classList.add('badge-bounce');
                setTimeout(() => b.classList.remove('badge-bounce'), 600);
              });
              btn.innerHTML = '<i class="bi bi-check-lg"></i> ¡Agregado!';
              btn.style.background = '#2e7d32';
              btn.style.borderColor = '#2e7d32';
              btn.style.color = '#fff';
            }
          })
          .catch(() => {
            btn.innerHTML = textoOrig;
            btn.disabled = false;
          })
          .finally(() => {
            setTimeout(() => {
              btn.innerHTML = textoOrig;
              btn.style.background = '';
              btn.style.borderColor = '';
              btn.style.color = '';
              btn.disabled = false;
            }, 2000);
          });
      }
    });
  });

  // ── Navbar activo según ruta ─────────────────────────────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-ans .nav-link').forEach(link => {
    if (link.getAttribute('href') && link.getAttribute('href') !== '/' && path.startsWith(link.getAttribute('href'))) {
      link.classList.add('active');
    }
  });

  // ── Checkout: Tipo de entrega toggle ────────────────────────────────────
  const tipoEntregaRadios = document.querySelectorAll('input[name="tipo_entrega"]');
  const secDireccion = document.getElementById('secDireccion');
  if (tipoEntregaRadios.length && secDireccion) {
    tipoEntregaRadios.forEach(r => {
      r.addEventListener('change', () => {
        secDireccion.style.display = r.value === 'recojo' ? 'none' : 'block';
      });
    });
    // Estado inicial
    const checked = document.querySelector('input[name="tipo_entrega"]:checked');
    if (checked && checked.value === 'recojo') secDireccion.style.display = 'none';
  }

  // ── Tooltips Bootstrap ───────────────────────────────────────────────────
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // ── Confirmación para acciones destructivas ──────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Sticky navbar sombra al hacer scroll ─────────────────────────────────
  const navbar = document.querySelector('.navbar-ans');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.style.boxShadow = window.scrollY > 10
        ? '0 4px 20px rgba(139,69,19,.15)' : '0 2px 12px rgba(139,69,19,.08)';
    });
  }

  // ── Imágenes con fallback ────────────────────────────────────────────────
  document.querySelectorAll('img[onerror]').forEach(img => {
    if (!img.complete || img.naturalHeight === 0) {
      img.dispatchEvent(new Event('error'));
    }
  });
});

/* ── Función global para toggle contraseña ──────────────────────────────── */
function togglePass(inputId = 'password', iconId = 'eyeIcon') {
  const p = document.getElementById(inputId);
  const i = document.getElementById(iconId);
  if (!p || !i) return;
  if (p.type === 'password') {
    p.type = 'text';
    i.className = 'bi bi-eye-slash';
  } else {
    p.type = 'password';
    i.className = 'bi bi-eye';
  }
}
