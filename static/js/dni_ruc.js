/* ═══════════════════════════════════════════════════════════════════════════
   ANITA NEW STYLE — Auto-completado DNI / RUC
   Se activa automáticamente en cualquier campo con:
     - data-tipo="dni"  → consulta DNI (8 dígitos)
     - data-tipo="ruc"  → consulta RUC (11 dígitos)
   O en inputs con id/name que contengan "dni" o "ruc"
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── Configuración de campos a rellenar ────────────────────────────────── */
  // Mapeo: clave del resultado API → selectores posibles del campo destino
  const MAPA_DNI = {
    nombre:   ['#nombre', '[name="nombre"]', '#first_name'],
    apellido: ['#apellido', '[name="apellido"]', '#last_name'],
    nombre_completo: ['#nombre_completo', '[name="nombre_completo"]', '#envio_nombre', '[name="nombre"]'],
  };

  const MAPA_RUC = {
    razon_social: ['#razon_social', '[name="razon_social"]', '#nombre', '[name="nombre"]'],
    direccion:    ['#direccion',    '[name="direccion"]'],
    distrito:     ['#distrito',     '[name="distrito"]'],
    provincia:    ['#provincia',    '[name="provincia"]'],
    departamento: ['#departamento', '[name="departamento"]'],
  };

  /* ── Helpers ───────────────────────────────────────────────────────────── */
  function crearBadge(input) {
    let badge = input.parentElement.querySelector('.dni-badge');
    if (!badge) {
      badge = document.createElement('div');
      badge.className = 'dni-badge';
      input.parentElement.appendChild(badge);
    }
    return badge;
  }

  function mostrarEstado(badge, tipo, mensaje) {
    badge.className = 'dni-badge dni-badge--' + tipo;
    badge.innerHTML = mensaje;
    badge.style.display = 'block';
    if (tipo === 'ok') {
      setTimeout(() => { badge.style.opacity = '0'; setTimeout(() => badge.style.display = 'none', 400); }, 4000);
    }
  }

  function setSpinner(input, activo) {
    let ico = input.parentElement.querySelector('.dni-spinner');
    if (activo) {
      if (!ico) {
        ico = document.createElement('span');
        ico.className = 'dni-spinner';
        ico.innerHTML = '⟳';
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(ico);
      }
      ico.style.display = 'block';
    } else if (ico) {
      ico.style.display = 'none';
    }
  }

  function rellenarCampos(mapa, datos, form) {
    const contexto = form || document;
    let rellenados = 0;
    for (const [clave, selectores] of Object.entries(mapa)) {
      const valor = datos[clave];
      if (!valor) continue;
      for (const sel of selectores) {
        const el = contexto.querySelector(sel);
        if (el && !el.readOnly) {
          el.value = valor;
          el.dispatchEvent(new Event('input'));
          el.classList.add('campo-autocompletado');
          setTimeout(() => el.classList.remove('campo-autocompletado'), 2500);
          rellenados++;
          break;
        }
      }
    }
    return rellenados;
  }

  /* ── Consulta DNI ──────────────────────────────────────────────────────── */
  async function consultarDNI(dni, input) {
    const badge = crearBadge(input);
    const form  = input.closest('form');
    setSpinner(input, true);
    mostrarEstado(badge, 'loading', '🔍 Consultando DNI...');
    try {
      const r    = await fetch(`/api/consultar/dni/${dni}`);
      const data = await r.json();
      if (data.ok) {
        const n = rellenarCampos(MAPA_DNI, data, form);
        mostrarEstado(badge, 'ok',
          `✅ ${data.nombre_completo}`);
      } else {
        mostrarEstado(badge, 'error', '❌ ' + data.error);
      }
    } catch {
      mostrarEstado(badge, 'error', '❌ Sin conexión al servidor.');
    } finally {
      setSpinner(input, false);
    }
  }

  /* ── Consulta RUC ──────────────────────────────────────────────────────── */
  async function consultarRUC(ruc, input) {
    const badge = crearBadge(input);
    const form  = input.closest('form');
    setSpinner(input, true);
    mostrarEstado(badge, 'loading', '🔍 Consultando RUC...');
    try {
      const r    = await fetch(`/api/consultar/ruc/${ruc}`);
      const data = await r.json();
      if (data.ok) {
        rellenarCampos(MAPA_RUC, data, form);
        const estado = data.estado === 'ACTIVO'
          ? '<span style="color:#2e7d32">● ACTIVO</span>'
          : `<span style="color:#c62828">● ${data.estado}</span>`;
        mostrarEstado(badge, 'ok',
          `✅ ${data.razon_social} — ${estado} — ${data.condicion}`);
      } else {
        mostrarEstado(badge, 'error', '❌ ' + data.error);
      }
    } catch {
      mostrarEstado(badge, 'error', '❌ Sin conexión al servidor.');
    } finally {
      setSpinner(input, false);
    }
  }

  /* ── Detectar y activar campos ─────────────────────────────────────────── */
  function activarCampo(input) {
    if (input._dniRucActivado) return;
    input._dniRucActivado = true;

    const tipo = input.dataset.tipo
      || (/(^|\b)(dni)(\b|$)/i.test(input.id + ' ' + (input.name||'')) ? 'dni' : null)
      || (/(^|\b)(ruc)(\b|$)/i.test(input.id + ' ' + (input.name||'')) ? 'ruc' : null);

    if (!tipo) return;

    const longitud = tipo === 'dni' ? 8 : 11;
    let timer;

    input.setAttribute('maxlength', longitud);
    input.setAttribute('inputmode', 'numeric');
    input.setAttribute('pattern', `[0-9]{${longitud}}`);
    input.setAttribute('placeholder', tipo === 'dni' ? '12345678' : '12345678901');

    input.addEventListener('input', function () {
      clearTimeout(timer);
      const val = this.value.replace(/\D/g, '');
      this.value = val;
      if (val.length === longitud) {
        timer = setTimeout(() => {
          tipo === 'dni' ? consultarDNI(val, this) : consultarRUC(val, this);
        }, 400);
      }
    });

    input.addEventListener('paste', function (e) {
      setTimeout(() => {
        const val = this.value.replace(/\D/g, '').slice(0, longitud);
        this.value = val;
        if (val.length === longitud) {
          tipo === 'dni' ? consultarDNI(val, this) : consultarRUC(val, this);
        }
      }, 50);
    });
  }

  /* ── Escanear DOM y observar cambios ───────────────────────────────────── */
  function escanear(raiz) {
    raiz = raiz || document;
    raiz.querySelectorAll('input[data-tipo="dni"], input[data-tipo="ruc"]').forEach(activarCampo);
    raiz.querySelectorAll('input[type="text"], input[type="number"], input:not([type])').forEach(inp => {
      const id   = (inp.id   || '').toLowerCase();
      const name = (inp.name || '').toLowerCase();
      if (id === 'dni' || name === 'dni' || id === 'ruc' || name === 'ruc') {
        activarCampo(inp);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', () => escanear());

  // Observar si se agregan campos dinámicamente (por AJAX/modales)
  const obs = new MutationObserver(muts => {
    muts.forEach(m => m.addedNodes.forEach(n => {
      if (n.nodeType === 1) escanear(n);
    }));
  });
  obs.observe(document.body, { childList: true, subtree: true });

  // Exponer globalmente por si se necesita activar manualmente
  window.AnitaDNI = { consultar: consultarDNI, consultarRUC, escanear };
})();
