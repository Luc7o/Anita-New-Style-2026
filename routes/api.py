from flask import Blueprint, jsonify
from utils.api_peru import consultar_dni, consultar_ruc

bp = Blueprint('api', __name__)

# ── Rutas 100% públicas ── el token queda oculto en el servidor (.env)

@bp.route('/consultar/dni/<dni>')
def api_dni(dni):
    return jsonify(consultar_dni(dni))

@bp.route('/consultar/ruc/<ruc>')
def api_ruc(ruc):
    return jsonify(consultar_ruc(ruc))
