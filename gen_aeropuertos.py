#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_aeropuertos.py — Genera aeropuertos_mundo.js desde OurAirports airports.csv
Fuente: https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv

Criterios de inclusión:
  - large_airport (siempre) o medium_airport con servicio programado
  - ICAO de exactamente 4 letras
  - No cerrado

Produce: aeropuertos_mundo.js  (reemplaza la tabla AEROPUERTOS inline del HTML)

Uso:
  python3 gen_aeropuertos.py
"""
import csv, json, re, unicodedata, sys, collections

ARCHIVO_CSV = 'airports.csv'
ARCHIVO_OUT = 'aeropuertos_mundo.js'

# Nombres de país en español (ISO 3166-1 alpha-2 → nombre)
PAISES = {
    'AD':'Andorra','AE':'Emiratos Árabes','AF':'Afganistán','AG':'Antigua y Barbuda',
    'AL':'Albania','AM':'Armenia','AO':'Angola','AR':'Argentina','AT':'Austria',
    'AU':'Australia','AZ':'Azerbaiyán','BA':'Bosnia y Herzegovina','BB':'Barbados',
    'BD':'Bangladesh','BE':'Bélgica','BF':'Burkina Faso','BG':'Bulgaria',
    'BH':'Baréin','BI':'Burundi','BJ':'Benín','BN':'Brunéi','BO':'Bolivia',
    'BR':'Brasil','BS':'Bahamas','BT':'Bután','BW':'Botsuana','BY':'Bielorrusia',
    'BZ':'Belice','CA':'Canadá','CD':'Congo (RDC)','CF':'Rep. Centroafricana',
    'CG':'Congo','CH':'Suiza','CI':'Costa de Marfil','CL':'Chile','CM':'Camerún',
    'CN':'China','CO':'Colombia','CR':'Costa Rica','CU':'Cuba','CV':'Cabo Verde',
    'CY':'Chipre','CZ':'Chequia','DE':'Alemania','DJ':'Yibuti','DK':'Dinamarca',
    'DM':'Dominica','DO':'Rep. Dominicana','DZ':'Argelia','EC':'Ecuador',
    'EE':'Estonia','EG':'Egipto','ER':'Eritrea','ES':'España','ET':'Etiopía',
    'FI':'Finlandia','FJ':'Fiyi','FM':'Micronesia','FR':'Francia','GA':'Gabón',
    'GB':'Reino Unido','GD':'Granada','GE':'Georgia','GH':'Ghana','GM':'Gambia',
    'GN':'Guinea','GQ':'Guinea Ecuatorial','GR':'Grecia','GT':'Guatemala',
    'GW':'Guinea-Bisáu','GY':'Guyana','HN':'Honduras','HR':'Croacia','HT':'Haití',
    'HU':'Hungría','ID':'Indonesia','IE':'Irlanda','IL':'Israel','IN':'India',
    'IQ':'Irak','IR':'Irán','IS':'Islandia','IT':'Italia','JM':'Jamaica',
    'JO':'Jordania','JP':'Japón','KE':'Kenia','KG':'Kirguistán','KH':'Camboya',
    'KI':'Kiribati','KM':'Comoras','KN':'San Cristóbal y Nieves','KP':'Corea del Norte',
    'KR':'Corea del Sur','KW':'Kuwait','KZ':'Kazajistán','LA':'Laos','LB':'Líbano',
    'LC':'Santa Lucía','LI':'Liechtenstein','LK':'Sri Lanka','LR':'Liberia',
    'LS':'Lesoto','LT':'Lituania','LU':'Luxemburgo','LV':'Letonia','LY':'Libia',
    'MA':'Marruecos','MC':'Mónaco','MD':'Moldavia','ME':'Montenegro','MG':'Madagascar',
    'MH':'Islas Marshall','MK':'Macedonia del Norte','ML':'Malí','MM':'Myanmar',
    'MN':'Mongolia','MR':'Mauritania','MT':'Malta','MU':'Mauricio','MV':'Maldivas',
    'MW':'Malaui','MX':'México','MY':'Malasia','MZ':'Mozambique','NA':'Namibia',
    'NE':'Níger','NG':'Nigeria','NI':'Nicaragua','NL':'Países Bajos','NO':'Noruega',
    'NP':'Nepal','NR':'Nauru','NZ':'Nueva Zelanda','OM':'Omán','PA':'Panamá',
    'PE':'Perú','PG':'Papúa Nueva Guinea','PH':'Filipinas','PK':'Pakistán',
    'PL':'Polonia','PT':'Portugal','PW':'Palaos','PY':'Paraguay','QA':'Catar',
    'RO':'Rumanía','RS':'Serbia','RU':'Rusia','RW':'Ruanda',
    'SA':'Arabia Saudita','SB':'Islas Salomón','SC':'Seychelles','SD':'Sudán',
    'SE':'Suecia','SG':'Singapur','SI':'Eslovenia','SK':'Eslovaquia','SL':'Sierra Leona',
    'SM':'San Marino','SN':'Senegal','SO':'Somalia','SR':'Surinam','SS':'Sudán del Sur',
    'ST':'Santo Tomé y Príncipe','SV':'El Salvador','SY':'Siria','SZ':'Esuatini',
    'TD':'Chad','TG':'Togo','TH':'Tailandia','TJ':'Tayikistán','TL':'Timor Oriental',
    'TM':'Turkmenistán','TN':'Túnez','TO':'Tonga','TR':'Turquía','TT':'Trinidad y Tobago',
    'TV':'Tuvalu','TZ':'Tanzania','UA':'Ucrania','UG':'Uganda','US':'Estados Unidos',
    'UY':'Uruguay','UZ':'Uzbekistán','VC':'San Vicente y las Granadinas',
    'VE':'Venezuela','VN':'Vietnam','VU':'Vanuatu','WS':'Samoa',
    'YE':'Yemen','ZA':'Sudáfrica','ZM':'Zambia','ZW':'Zimbabue',
    # Territorios frecuentes
    'AW':'Aruba','BM':'Bermudas','CW':'Curazao','GF':'Guayana Francesa',
    'GP':'Guadalupe','GU':'Guam','HK':'Hong Kong','MO':'Macao','MQ':'Martinica',
    'NC':'Nueva Caledonia','PF':'Polinesia Francesa','PR':'Puerto Rico',
    'RE':'Reunión','TW':'Taiwán','VI':'Islas Vírgenes (EE.UU.)',
    'XK':'Kosovo',
}

def norm(s):
    return unicodedata.normalize('NFD', s.lower()).encode('ascii','ignore').decode()

def limpiar_nombre(nombre):
    """Simplifica el nombre del aeropuerto para mostrarlo como ciudad."""
    # Quitar sufijos comunes
    for suf in [' International Airport', ' Airport', ' Intl', ' International',
                ' Regional Airport', ' Regional', ' Municipal Airport', ' Municipal',
                ' Aeropuerto Internacional', ' Aeropuerto', ' Aéroport International',
                ' Aéroport', ' Flughafen', ' Lufthavn', ' Aeroporto']:
        nombre = nombre.replace(suf, '')
    return nombre.strip()

def main():
    candidatos = []
    with open(ARCHIVO_CSV, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r['type'] not in ('large_airport', 'medium_airport'):
                continue
            icao = (r['icao_code'] or r['ident'] or '').strip()
            if not icao or len(icao) != 4 or not icao[0].isalpha():
                continue
            if r['scheduled_service'] != 'yes' and r['type'] != 'large_airport' and icao not in ('SADP','SADM','SADF'):
                continue
            candidatos.append(r)

    print(f'Candidatos: {len(candidatos)} aeropuertos en {len(set(r["iso_country"] for r in candidatos))} países')

    # Construir entradas JS
    # Prioridad: municipality > nombre limpio del aeropuerto
    # Alias: variantes normalizadas del nombre
    entradas = []
    vistos = set()

    for r in candidatos:
        icao = (r['icao_code'] or r['ident']).strip()
        if icao in vistos:
            continue
        vistos.add(icao)

        pais_iso  = r['iso_country'].strip()
        pais_nombre = PAISES.get(pais_iso, pais_iso)
        municipio = r['municipality'].strip()
        nombre_apt = limpiar_nombre(r['name'].strip())

        # Ciudad a mostrar
        if municipio:
            ciudad = f"{municipio} ({pais_iso})"
        else:
            ciudad = f"{nombre_apt} ({pais_iso})"

        # Alias para búsqueda fuzzy
        alias_set = set()
        for texto in [municipio, nombre_apt, pais_nombre.lower()]:
            if texto:
                alias_set.add(norm(texto))
                # Versión sin país
                alias_set.add(texto.lower())
        # Quitar el que ya está en ciudad (normalizado) para no duplicar
        alias_set.discard(norm(municipio))
        alias_set.discard(municipio.lower())
        alias = sorted(a for a in alias_set if a and len(a) > 1)[:6]

        entradas.append({
            'ciudad': ciudad,
            'icao': icao,
            'alias': alias
        })

    # Ordenar: primero por país, luego por ciudad
    entradas.sort(key=lambda e: (e['icao'][:2], e['ciudad']))

    # Generar JS
    lineas = []
    pais_actual = None
    for e in entradas:
        prefijo = e['icao'][:2]
        if prefijo != pais_actual:
            pais_actual = prefijo
            lineas.append(f'\n  /* {prefijo} */')
        ciudad_esc = e['ciudad'].replace("'", "\\'")
        alias_js   = json.dumps(e['alias'], ensure_ascii=False)
        lineas.append(f"  {{ ciudad:'{ciudad_esc}', icao:'{e['icao']}', alias:{alias_js} }},")

    contenido = (
        '/* Generado por gen_aeropuertos.py — NO editar a mano.\n'
        '   Fuente: OurAirports airports.csv (dominio público)\n'
        f'   Total: {len(entradas)} aeropuertos en {len(set(e["icao"][:2] for e in entradas))} prefijos */\n'
        'const AEROPUERTOS = [\n'
        + '\n'.join(lineas)
        + '\n];\n'
    )

    open(ARCHIVO_OUT, 'w', encoding='utf-8').write(contenido)
    print(f'OK → {ARCHIVO_OUT} ({len(entradas)} aeropuertos)')

if __name__ == '__main__':
    main()
