import os
from flask import Flask, request, jsonify
from stravalib.client import Client

app = Flask(_name_)

# Suas credenciais do Strava
CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"
REFRESH_TOKEN = "13a16ad7c8dd6aafdba6fc88a88b55d2e58d762"

@app.route('/webhook', methods=['GET'])
def validar_webhook():
    """
    O Strava faz uma requisição GET para validar a assinatura do webhook.
    """
    verify_token = "MEU_TOKEN_SECRETO_DE_VALIDACAO"
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            print("Webhook validado com sucesso pelo Strava!")
            return jsonify({"hub.challenge": challenge}), 200
        else:
            return "Falha na validação", 403
    return "Parâmetros inválidos", 400

@app.route('/webhook', methods=['POST'])
def receber_evento():
    """
    O Strava envia um POST sempre que uma nova atividade é criada.
    """
    evento = request.json
    print(f"Evento recebido do Strava: {evento}")

    if evento and evento.get('aspect_type') == 'create' and evento.get('object_type') == 'activity':
        activity_id = evento.get('object_id')
        owner_id = evento.get('owner_id')
        print(f"Nova atividade detectada! ID: {activity_id} (Usuário: {owner_id})")

    return jsonify({"status": "recebido"}), 200

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)
