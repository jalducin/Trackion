# Estándares — Frontend (SPA vanilla, paleta metálica)

> Específicos de Trackion. El frontend vive en `frontend/`. Inspirado en el layout de mesa de ayuda
> de referencia (Base), pero con identidad visual propia **metálica** y sin dependencias de PHP.

## 1. Stack

- HTML5 + CSS3 + JavaScript vanilla (ES módulos). Sin framework ni build step obligatorio.
- Una SPA ligera: `index.html` (app autenticada) + `login.html`. Lógica en `js/` (`api.js`, `app.js`).
- Configuración de endpoint en `js/config.js` (`API_BASE`). El token JWT se guarda en `localStorage.trackion_token`.

## 2. Identidad visual — paleta metálica

Variables CSS en `:root` (tokens). Estética metálica: grises acerados, degradados sutiles tipo
"brushed metal", acentos fríos y realces especulares. Evitar planos saturados.

```css
:root{
  --metal-900:#1b1e23; --metal-800:#23272e; --metal-700:#2d323b; /* fondos */
  --metal-500:#5b6473; --metal-300:#9aa3b2; --metal-100:#d7dce3; /* texto/bordes */
  --steel:#8a93a3; --chrome:#c7ccd4; --gunmetal:#3a4049;          /* superficies metálicas */
  --accent:#3fb7c4;    /* acento frío (cian acerado) */
  --accent-2:#7c5cff;  /* acento secundario */
  --ok:#3ecf8e; --warn:#e0a83d; --danger:#e0564b;
  --grad-metal:linear-gradient(145deg,#3a4049 0%,#23272e 60%,#1b1e23 100%);
  --grad-chrome:linear-gradient(180deg,#e9edf2 0%,#c7ccd4 45%,#9aa3b2 55%,#c7ccd4 100%);
}
```

- Botones/headers con `--grad-chrome`/`--grad-metal`; bordes `1px` claros para el realce metálico.
- Estados de prioridad/ticket con `--ok/--warn/--danger` sobre fondo metálico.

## 3. Estructura

```
frontend/
├── index.html            # app: dashboard, lista de tickets, detalle, catálogos
├── login.html            # acceso
├── css/
│   └── style.css         # tokens + componentes (paleta metálica)
└── js/
    ├── config.js         # API_BASE
    ├── api.js            # cliente fetch (Authorization: Bearer trackion_token)
    └── app.js            # render + navegación + handlers de UI
```

## 4. Convenciones

- Texto de UI en español. Identificadores JS en inglés.
- Sin secretos en el frontend; solo el `API_BASE` público.
- Accesibilidad básica: labels, foco visible, contraste suficiente sobre los metálicos.
- Verificación manual del agente: flujo login → ver lista → crear ticket → abrir detalle → comentar/asignar.
