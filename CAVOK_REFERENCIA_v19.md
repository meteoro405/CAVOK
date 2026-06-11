# CAVOK — Documento de Referencia Completo
## Versión actual: v19 · Fecha: Junio 2026

---

## 1. QUÉ ES EL PROYECTO

**CAVOK** es una Progressive Web App (PWA) de meteo aeronáutica mundial. El usuario escribe una ciudad o código ICAO y obtiene las condiciones meteorológicas en tiempo real del aeropuerto más cercano, con datos METAR reales. Incluye diagrama SVG de pistas con indicador de viento.

**Autor / dueño:** Meteoro405  
**GitHub:** `meteoro405` (mismo que el proyecto De Cuestas, Abras y Quebradas)  
**Stack:** HTML/CSS/JS puro — sin frameworks, sin build steps, sin node_modules  
**Deploy:** GitHub Pages  
**Nombre del término aeronáutico:** CAVOK = "Ceiling And Visibility OK"

---

## 2. ARQUITECTURA DE ARCHIVOS

```
cavok/cavok_vX/
├── index.html            ← App completa (HTML + CSS + JS inline)
├── aeropuertos_mundo.js  ← Tabla AEROPUERTOS[] con 3.301 aeropuertos mundiales
├── pistas.js             ← Datos PISTAS{} con 4.549 pistas de 3.213 aeropuertos
├── manifest.json         ← PWA manifest
├── sw.js                 ← Service Worker (cachea shell, no cachea API)
├── icon-192.png          ← Ícono PWA (avión blanco sobre fondo amarillo)
├── icon-512.png          ← Ícono PWA grande
├── gen_aeropuertos.py    ← Generador de aeropuertos_mundo.js desde OurAirports CSV
└── gen_pistas.py         ← Generador de pistas.js desde OurAirports CSV
```

### ZIP de distribución
Siempre: `cavok_vX.zip` con estructura interna `cavok/cavok_vX/{archivos}`  
(todo en minúsculas, sin espacios)

### Archivos fuente (no se distribuyen, solo para regenerar)
- `airports.csv` — OurAirports airports data (dominio público)
- `runways.csv` — OurAirports runways data (dominio público)

---

## 3. APIs

### CheckWX (meteo METAR)
- **Versión:** v2 (IMPORTANTE: v1 y v2 tienen estructuras JSON distintas)
- **Endpoint:** `GET https://api.checkwx.com/v2/metar/{ICAO}/decoded`
- **Header:** `X-API-Key: 27d70fc182ef4d169f9f202a8762a17b`
- **Plan:** gratuito, 2.000 req/día
- **Caché:** sessionStorage por hora (`metar_{ICAO}_{fecha}T{hora}`)
- **Host allowlist:** hay que registrar `localhost`, `127.0.0.1`, `meteoro405.github.io` en el dashboard de CheckWX para que funcione en desarrollo y en producción

### Estructura de respuesta CheckWX v2 (CRÍTICO — difiere de v1)
```json
{
  "data": [{
    "icao": "EGLL",
    "flight_category": "VFR",
    "temperature": { "celsius": 13 },
    "humidity": 76,                          ← v2: número directo (v1 era .percent)
    "wind": { "degrees": 250, "speed_kts": 15, "direction": "WSW" },
    "visibility": { "meters": 9999 },
    "clouds": [{ "code": "BKN", "feet": 2500, "meters": 762 }],  ← v2: .feet (v1 era .base_feet_agl)
    "ceiling": { "code": "BKN", "feet": 2500, "meters": 762 },   ← v2: campo separado
    "pressure": { "mb": 1015, "hg": 29.97 },                     ← v2: .pressure.mb (v1 era barometer.hpa)
    "raw_text": "METAR EGLL ...",
    "observed": "2026-06-06T23:50:00Z"
  }]
}
```

### Compatibilidad v1/v2 en el código
El código usa `??` para soportar ambas versiones:
```js
humidity:  typeof data.humidity === 'object' ? data.humidity.percent : data.humidity
pressure:  data.pressure?.mb ?? data.pressure?.hpa ?? data.barometer?.hpa
clouds alt: c.feet ?? c.base_feet_agl
ceiling:   data.ceiling?.feet ?? (cálculo manual desde clouds)
```

### OurAirports (aeropuertos + pistas)
- **Fuente:** dominio público
- `airports.csv`: https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv
- `runways.csv`: https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/runways.csv
- Se usan OFFLINE — descargados y procesados con los scripts generadores

---

## 4. FUNCIONALIDADES

### Buscador
- Búsqueda fuzzy local sobre `AEROPUERTOS[]` por ciudad, ICAO y alias
- Fallback automático a `GET https://api.checkwx.com/v2/station/search/{texto}` si no hay resultado local
- Sugerencias con teclado (↑↓ Enter Escape)
- Historial de últimas 8 búsquedas (localStorage, chips con ✕ individual + "Limpiar historial")

### Tablero
- Múltiples tarjetas comparables simultáneamente
- Persistente en localStorage (`cavok_tablero`)
- Botón "Quitar todos" con confirm() cuando hay 2+

### Tarjeta de aeropuerto
Contiene en orden:
1. **Cabecera:** placa ICAO (amarillo sobre negro), nombre ciudad, tiempo desde reporte, botones ⟳ y ✕
2. **Banda de categoría:** VFR (verde) / MVFR (amarillo) / IFR (rojo) / LIFR (rojo)
3. **Métricas:** Temperatura · Humedad · Viento · Visibilidad · Nubes (con techo) · Presión
4. **🛬 Pistas (n):** diagrama SVG desplegable
5. **METAR crudo:** `<details>` desplegable

### Nubes y techo
- Deduplica capas con mismo texto (queda la de mayor altitud)
- Ordena de peor a mejor condición (OVC > BKN > SCT > FEW)
- Muestra techo en itálico gris: "· Techo 600 ft (183 m)"
- `techoHtml` se declara como `let techoHtml = ''` ANTES del if de nubes (bug corregido en v18)
- Se inserta como `${esc(nubes)}${techoHtml}` — nubes va por esc(), techoHtml NO (es HTML con span)

### Diagrama de pistas
- SVG 300×210px generado en runtime con `renderPistas(icao, metar)`
- Proyección equirectangular local desde coordenadas reales de cabeceras
- Norte arriba, designadores en amarillo, eje punteado
- Flecha de viento superpuesta (ángulo = `metar.wind.degrees`)
- Fallback por rumbo cuando no hay coordenadas
- Lista de pistas: `17/35 · 2.110 m × 45 m · Hormigón`
- Fuente: "Norte arriba · flecha = viento actual · datos OurAirports"

### PWA
- `manifest.json`: name="CAVOK · Meteo Aeronáutica Mundial", theme_color="#F5B941"
- Service Worker (`sw.js`): cachea shell (index.html, pistas.js, aeropuertos_mundo.js, íconos), NO cachea CheckWX ni Google Fonts
- Banner de instalación: aparece cuando browser dispara `beforeinstallprompt`
- Si usuario cierra sin instalar: reaparece en 3 días (`cavok_pwa_posponer` en localStorage)
- iOS: el banner NO aparece automáticamente (Safari no implementa `beforeinstallprompt`)
- Para actualizar SW tras nueva versión: el usuario debe desinstalar y reinstalar la PWA, o limpiar site data en DevTools

---

## 5. DISEÑO Y TOKENS CSS

```css
--amarillo: #F5B941       /* señalética de rodaje — color principal */
--vfr:  #3FC97E           /* verde */
--mvfr: #EBB748           /* amarillo */
--ifr:  #EF6363           /* rojo */
--lifr: #EF6363           /* rojo */

/* Tema oscuro (default) */
--bg: #0C1220  --panel: #141C2E  --panel2: #1B2540
--texto: #E9EEF7  --muted: #8A96AC  --linea: #26304A
--placa-bg: #05070D

/* Tema claro */
--bg: #EDF0F5  --panel: #FFFFFF  --panel2: #F2F4F9
--texto: #1A2233  --muted: #5B6678  --linea: #D7DCE6
--placa-bg: #10141F
```

**Tipografías (Google Fonts):**
- `Saira Condensed` 600/700 — títulos display (h1 del header)
- `Barlow` 400/500/600 — cuerpo de texto
- `JetBrains Mono` 400/600/700 — valores numéricos, ICAO, código

**Logo (SVG inline en el header):**
- Etiqueta de equipaje aeroportuaria
- Fondo amarillo (`var(--amarillo)`), sin franja negra superior
- Agujero del hilo a la izquierda con cordel punteado
- "CAVOK" en JetBrains Mono 700, font-size 22, letter-spacing 4, color `var(--placa-bg)`
- Sin "by Meteoro405" en el logo (está solo en el subtítulo del header)
- ViewBox: `0 0 200 36`, width en CSS: 170px

**Header layout (Variante A):**
```
[bloque-logo: columna]          [botón tema]
  [SVG etiqueta]
  [h1: Meteo Aeronáutica Mundial]
  [p: Condiciones en tiempo real · by Meteoro405]
```
En mobile (≤560px): header centrado, h1 26px, botón tema absolute top-right

---

## 6. LOCALSTORAGE — CLAVES

Prefijo: `cavok_`
| Clave | Contenido |
|---|---|
| `cavok_tablero` | `[{icao, ciudad}]` — aeropuertos en el tablero |
| `cavok_historial` | `[{icao, ciudad}]` — últimas 8 búsquedas |
| `cavok_tema` | `'oscuro'` o `'claro'` |
| `cavok_pwa_posponer` | timestamp — cuándo se cerró el banner de instalación |

SessionStorage (no persiste entre sesiones):
- `metar_{ICAO}_{yyyy-mm-dd}T{HH}` — respuesta METAR cacheada por hora

---

## 7. GENERADORES PYTHON

### gen_aeropuertos.py
- Lee `airports.csv` de OurAirports
- Filtra: `large_airport` siempre + `medium_airport` con `scheduled_service=yes`, ICAO de 4 letras
- Produce `aeropuertos_mundo.js` con `const AEROPUERTOS = [...]`
- Cada entrada: `{ ciudad:'Madrid (ES)', icao:'LEMD', alias:['madrid','barajas',...] }`
- Parches manuales de alias en el script para ciudades con nombre de municipio distinto al conocido (LEAS→oviedo/gijon, KJFK→new york/jfk, EGLL→london/heathrow, etc.)
- **Resultado:** 3.301 aeropuertos en 234 países

### gen_pistas.py
- Lee `runways.csv` de OurAirports
- Lee lista de ICAOs desde `aeropuertos_mundo.js` (preferido) o `index.html`
- Descarta: pistas cerradas, helipuertos (le_ident empieza con H)
- Convierte pies a metros (factor 0.3048)
- Tabla de equivalencias ICAO: `{'SPJC': 'SPIM'}` (Lima cambió código en 2020)
- Produce `pistas.js` con `const PISTAS = {"SAEZ": [...], ...}`
- Cada pista: `{ids:['17','35'], le:[-34.60,-58.61], he:[-34.61,-58.60], hdg:165.3, m:2110, ancho:45, sup:'CON'}`
- **Resultado:** 3.213 aeropuertos, 4.549 pistas (88 sin datos en OurAirports)

**Para regenerar datos actualizados:**
```bash
curl -o airports.csv https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv
curl -o runways.csv https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/runways.csv
python3 gen_aeropuertos.py   # → aeropuertos_mundo.js
python3 gen_pistas.py        # → pistas.js
```

---

## 8. CONVENCIONES DE TRABAJO

- **Versión:** se incrementa en cada cambio, sin excepción. Actualmente v19.
- **Validación JS:** siempre `node --check archivo.js` antes de empaquetar
- **ZIP:** siempre `rm -f cavok_vX.zip` antes de generar, estructura `cavok/cavok_vX/`
- **Verificaciones Python:** asserts explícitos antes de empaquetar
- **No se entrega** `index.html` suelto además del ZIP (es redundante)
- **Cambios de texto/datos:** se hacen con Python str.replace() o re.sub(), nunca manualmente
- **CSS duplicado:** vigilar al hacer re.sub() en bloques CSS — puede dejar residuos

---

## 9. BUGS CORREGIDOS (historial relevante)

| Versión | Bug | Causa | Fix |
|---|---|---|---|
| v12 | Nubes repetidas (Calgary: "BKN · BKN · BKN") | Se mostraban todas las capas sin deduplicar | Agrupar por texto, conservar altitud máxima de cada tipo |
| v13 | Techo no aparecía | CheckWX v2 tiene `ceiling` separado y `clouds[].feet` en vez de `.base_feet_agl` | Usar `c.feet ?? c.base_feet_agl` y `data.ceiling?.feet` |
| v15 | Humedad, presión, nubes no mostraban | CheckWX v2 cambió estructura JSON (humidity=número, pressure.mb, clouds.feet) | Compatibilidad v1/v2 con `??` |
| v16 | Nubes mostraba `<span class='techo'>…</span>` como texto literal | `techoStr` tenía HTML pero pasaba por `esc()` | Separar `nubes` (texto) de `techoHtml` (HTML), insertar por separado |
| v18 | "—undefined" en Nubes cuando no hay nubes | `var techoHtml` declarado DENTRO del if, no accesible fuera | `let techoHtml = ''` declarado ANTES del if |
| v19 | Media query mobile dejó CSS residual | re.sub() incompleto en bloque CSS | Limpiar con segundo re.sub() |

---

## 10. AEROPUERTOS ESPECIALES EN LA TABLA LOCAL

Algunos aeropuertos tienen alias extendidos hardcodeados en `gen_aeropuertos.py` porque el municipio en OurAirports difiere del nombre conocido:

| ICAO | Ciudad OurAirports | Alias agregados |
|---|---|---|
| LEAS | Ranón | oviedo, gijon, asturias |
| KJFK | New York | new york, nueva york, jfk |
| KEWR | Newark | new york, newark |
| KLAX | Los Angeles | los angeles, los ángeles |
| EGLL | London | london, londres, heathrow |
| EGKK | London | london, gatwick |
| RJAA | Narita | tokyo, tokio |
| RJTT | Tokyo | tokyo, tokio, haneda |
| LSZH | Zürich | zurich |
| EDDM | München | munich |
| LIRF | Rome | roma, fiumicino |
| SBGR | São Paulo | sao paulo, san pablo |
| SCEL | Santiago | santiago, chile |
| SAEZ | Buenos Aires | buenos aires, ezeiza |
| SABE | Buenos Aires | buenos aires, aeroparque |

---

## 11. PENDIENTES / IDEAS FUTURAS

- **Vuelos (salidas):** implementado y luego removido porque AviationStack free plan no permite llamadas desde browser (CORS). La solución correcta es un **proxy serverless** (Netlify Functions o Cloudflare Workers, ambos gratuitos). El código de render ya estaba funcionando, solo falta el backend.
- **iOS PWA install prompt:** Safari no dispara `beforeinstallprompt`. Se puede detectar Safari/iOS y mostrar un tooltip manual ("tocá compartir → Agregar a inicio").
- **Auto-update del SW:** cuando se sube una nueva versión, los usuarios con la PWA instalada no actualizan hasta cerrar todas las pestañas o limpiar site data. Se puede implementar un `postMessage` del SW al cliente para mostrar un banner "Nueva versión disponible — Actualizar".
- **Mapa del aeropuerto:** OurAirports tiene coordenadas de todas las estaciones, se podría mostrar un mini-mapa con Leaflet.
- **IGN mapas:** para el proyecto De Cuestas (no CAVOK) se mencionó como fuente de imágenes de rutas.

---

## 12. RELACIÓN CON OTROS PROYECTOS DE METEORO405

- **De Cuestas, Abras y Quebradas** (`meteoro405.github.io/caminos-argentina`): app PWA de rutas escénicas argentinas, actualmente en v98. Comparte el módulo METAR original del que deriva CAVOK. Tiene su propio documento de referencia `PROYECTO_REFERENCIA_v98.md`.
- **MiGarage** (`meteoro405.github.io/mi-auto`): tracker de mantenimiento vehicular, actualmente en v4.

---

## 13. FRAGMENTOS DE CÓDIGO CLAVE

### loadMetar() — función base probada
```javascript
async function loadMetar(icao, forzar = false){
  const cacheKey = claveCacheHora(icao);
  if (forzar) sessionStorage.removeItem(cacheKey);
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) return JSON.parse(cached);
  try {
    const res = await fetch(`https://api.checkwx.com/v2/metar/${icao}/decoded`, {
      headers: { 'X-API-Key': '27d70fc182ef4d169f9f202a8762a17b' }
    });
    if (!res.ok) return null;
    const json = await res.json();
    const data = json?.data?.[0];
    if (!data) return null;
    try { sessionStorage.setItem(cacheKey, JSON.stringify(data)); } catch(e){}
    return data;
  } catch(e){ return null; }
}
```

### Lectura de campos v2 con fallback v1
```javascript
const hum = data.humidity != null
  ? `${typeof data.humidity==='object' ? data.humidity.percent : data.humidity}%`
  : '—';

const presionVal = data.pressure?.mb ?? data.pressure?.hpa ?? data.barometer?.hpa ?? null;

// En nubes:
const alt = c.feet ?? c.base_feet_agl ?? 0;

// Techo:
const techoFt = data.ceiling?.feet
  ?? data.clouds.filter(c => ['BKN','OVC','VV'].includes(c.code))
       .map(c => c.feet ?? c.base_feet_agl ?? 0)
       .filter(Boolean).sort((a,b)=>a-b)[0]
  ?? null;
```

### Patrón correcto para HTML en template strings (NO escapar)
```javascript
let techoHtml = '';   // ← declarar FUERA del if
if (data.clouds?.length){
  // ... cálculos ...
  techoHtml = techoFt
    ? `<span class='techo'> · Techo ${techoFt} ft (${techoM} m)</span>`
    : '';
}
// En el template:
`${esc(nubes)}${techoHtml}`   // nubes → esc(), techoHtml → directo
```
