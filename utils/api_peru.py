import requests
from flask import current_app

BASE_URL = "https://dniruc.apisperu.com/api/v1"
DNI_URL  = BASE_URL + "/dni/{dni}?token={token}"
RUC_URL  = BASE_URL + "/ruc/{ruc}?token={token}"
TIMEOUT  = 8


def _get_token():
    return current_app.config.get('API_PERU_TOKEN', '')


def consultar_dni(dni: str) -> dict:
    dni = dni.strip()
    if len(dni) != 8 or not dni.isdigit():
        return {'ok': False, 'error': 'El DNI debe tener exactamente 8 dígitos.'}
    try:
        url  = DNI_URL.format(dni=dni, token=_get_token())
        r    = requests.get(url, timeout=TIMEOUT)
        data = r.json()
        if r.status_code == 200 and data.get('success', False):
            nombres  = data.get('nombres', '').title()
            ap_pat   = data.get('apellidoPaterno', '').title()
            ap_mat   = data.get('apellidoMaterno', '').title()
            return {
                'ok': True,
                'dni': dni,
                'nombres': nombres,
                'apellido_paterno': ap_pat,
                'apellido_materno': ap_mat,
                'nombre_completo': f"{nombres} {ap_pat} {ap_mat}".strip(),
                'nombre':   nombres.split()[0] if nombres else '',
                'apellido': f"{ap_pat} {ap_mat}".strip(),
            }
        return {'ok': False, 'error': data.get('message', 'DNI no encontrado.')}
    except requests.exceptions.Timeout:
        return {'ok': False, 'error': 'Tiempo de espera agotado.'}
    except Exception as e:
        return {'ok': False, 'error': f'Error: {str(e)}'}


def consultar_ruc(ruc: str) -> dict:
    ruc = ruc.strip()
    if len(ruc) != 11 or not ruc.isdigit():
        return {'ok': False, 'error': 'El RUC debe tener exactamente 11 dígitos.'}
    try:
        url  = RUC_URL.format(ruc=ruc, token=_get_token())
        r    = requests.get(url, timeout=TIMEOUT)
        data = r.json()
        if r.status_code == 200 and data.get('success', False):
            return {
                'ok': True,
                'ruc': ruc,
                'razon_social': data.get('razonSocial', '').title(),
                'estado':       data.get('estado', ''),
                'condicion':    data.get('condicion', ''),
                'direccion':    data.get('direccion', '').title(),
                'distrito':     data.get('distrito', '').title(),
                'provincia':    data.get('provincia', '').title(),
                'departamento': data.get('departamento', '').title(),
                'tipo':         data.get('tipo', ''),
            }
        return {'ok': False, 'error': data.get('message', 'RUC no encontrado.')}
    except requests.exceptions.Timeout:
        return {'ok': False, 'error': 'Tiempo de espera agotado.'}
    except Exception as e:
        return {'ok': False, 'error': f'Error: {str(e)}'}
