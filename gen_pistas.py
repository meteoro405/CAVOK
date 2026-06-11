#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_pistas.py — Generador de pistas.js para CAVOK
Fuente: OurAirports runways.csv (dominio público)
  https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/runways.csv

Lee la lista de ICAO directamente desde index.html (regex sobre la tabla
AEROPUERTOS), así pistas.js queda siempre sincronizado con la app.

Uso:
  python3 gen_pistas.py            (requiere runways.csv e index.html en el directorio)
"""
import csv, json, re, sys

ARCHIVO_HTML = 'index.html'
ARCHIVO_CSV  = 'runways.csv'
ARCHIVO_OUT  = 'pistas.js'
FT_A_M = 0.3048

# ICAO de la app → ICAO en OurAirports (códigos renombrados)
EQUIVALENCIAS = { 'SPJC': 'SPIM' }   # Lima Jorge Chávez cambió SPIM→SPJC en 2020

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def main():
    # ICAOs desde aeropuertos_mundo.js (preferido) o index.html
    import os
    if os.path.exists('aeropuertos_mundo.js'):
        fuente = open('aeropuertos_mundo.js', encoding='utf-8').read()
    else:
        fuente = open(ARCHIVO_HTML, encoding='utf-8').read()
    icaos = set(re.findall(r"icao:'([A-Z]{4})'", fuente))
    if not icaos:
        sys.exit('ERROR: no se encontraron ICAO')
    print(f'ICAOs en la tabla local: {len(icaos)}')
    # mapa inverso: ICAO OurAirports → ICAO de la app
    inverso = {v: k for k, v in EQUIVALENCIAS.items()}

    # 2) Pistas desde el CSV
    pistas = {}
    with open(ARCHIVO_CSV, encoding='utf-8') as f:
        for fila in csv.DictReader(f):
            icao = inverso.get(fila['airport_ident'], fila['airport_ident'])
            if icao not in icaos:
                continue
            if fila['closed'] == '1':
                continue
            le_id = fila['le_ident'].strip()
            he_id = fila['he_ident'].strip()
            if not le_id:
                continue
            # excluir helipuertos (H1, H2…)
            if le_id.upper().startswith('H') and not he_id:
                continue

            le_lat, le_lon = num(fila['le_latitude_deg']), num(fila['le_longitude_deg'])
            he_lat, he_lon = num(fila['he_latitude_deg']), num(fila['he_longitude_deg'])
            hdg = num(fila['le_heading_degT'])
            if hdg is None:
                # derivar del designador (17 → 170°)
                m = re.match(r'(\d{1,2})', le_id)
                hdg = int(m.group(1)) * 10 if m else None

            largo_ft, ancho_ft = num(fila['length_ft']), num(fila['width_ft'])
            p = {
                'ids': [le_id, he_id or '—'],
                'le':  [round(le_lat, 5), round(le_lon, 5)] if le_lat is not None and le_lon is not None else None,
                'he':  [round(he_lat, 5), round(he_lon, 5)] if he_lat is not None and he_lon is not None else None,
                'hdg': round(hdg, 1) if hdg is not None else None,
                'm':     round(largo_ft * FT_A_M) if largo_ft else None,
                'ancho': round(ancho_ft * FT_A_M) if ancho_ft else None,
                'sup': fila['surface'].strip().upper()[:12]
            }
            pistas.setdefault(icao, []).append(p)

    sin_datos = sorted(icaos - set(pistas))
    print(f'Aeropuertos con pistas: {len(pistas)}')
    if sin_datos:
        print(f'Sin datos de pistas ({len(sin_datos)}): {", ".join(sin_datos)}')

    # 3) Escribir pistas.js (una línea por aeropuerto, legible y diffeable)
    lineas = [f'  "{icao}": {json.dumps(pistas[icao], ensure_ascii=False, separators=(",", ":"))}'
              for icao in sorted(pistas)]
    contenido = (
        '/* Generado por gen_pistas.py — NO editar a mano.\n'
        '   Fuente: OurAirports runways.csv (dominio público) */\n'
        'const PISTAS = {\n' + ',\n'.join(lineas) + '\n};\n'
    )
    open(ARCHIVO_OUT, 'w', encoding='utf-8').write(contenido)
    total = sum(len(v) for v in pistas.values())
    print(f'OK → {ARCHIVO_OUT} ({len(pistas)} aeropuertos, {total} pistas)')

if __name__ == '__main__':
    main()
