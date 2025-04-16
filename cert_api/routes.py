from flask import Blueprint, jsonify

api = Blueprint('api', __name__)

@api.route('/api/history')
def history():
    return jsonify({"message": "History endpoint"})

@api.route('/api/status')
def status():
    return jsonify({"message": "Status endpoint"})

@api.route('/api/alerts')
def alerts():
    return jsonify({"message": "Alerts endpoint"})