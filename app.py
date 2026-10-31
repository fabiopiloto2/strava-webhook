import os
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Suas credenciais do Strava
CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"
REFRESH_TOKEN = "13a16ad7c8dd6aafdba6fc88a88b55d2e58d762"

def obter_access_token():
    try:
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'refresh_token': REFRESH_TOKEN
            }
        )
        return response.json().get('access_token')
    except Exception as e:
        print(f"Erro ao obter access token: {e}")
        return None

def registrar_webhook_automatico():
    try:
        url = "https://www.strava.com/api/v3/push_subscriptions"
        payload = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'callback_url': "https://strava-webhook-vi7k.onrender.com/webhook",
            'verify_token': "MEU_TOKEN_SECRETO_DE_VALIDACAO"
        }
        response = requests.post(url, data=payload)
        print(f"Tentativa de registro automático no Strava. Status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao registrar webhook: {e}")

threading.Thread(target=registrar_webhook_automatico).start()

@app.route('/webhook', methods=['GET'])
def validar_webhook():
    verify_token = "MEU_TOKEN_SECRETO_DE_VALIDACAO"
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token and mode == 'subscribe' and token == verify_token:
        return jsonify({"hub.challenge": challenge}), 200
    return "Falha na validação", 403

@app.route('/webhook', methods=['POST'])
def receber_evento():
    evento = request.json
    print(f"Evento recebido do Strava: {evento}")

    if evento and evento.get('aspect_type') == 'create' and evento.get('object_type') == 'activity':
        activity_id = evento.get('object_id')
        print(f"Nova atividade detetada pelo Webhook! ID: {activity_id}")
        # Aqui o servidor processa o evento fresco em tempo real

    return jsonify({"status": "recebido"}), 200

@app.route('/historico', methods=['GET'])
def ver_historico():
    access_token = obter_access_token()
    if not access_token:
        return jsonify({"erro": "Não foi possível obter o token de acesso"}), 500
    
    headers = {'Authorization': f'Bearer {access_token}'}
    # Buscamos um volume maior de atividades para garantir o histórico de referência
    response = requests.get("https://www.strava.com/api/v3/athlete/activities?per_page=20", headers=headers)
    
    if response.status_code == 200:
        atividades = response.json()
        if not atividades:
            return jsonify({"mensagem": "Nenhuma atividade encontrada."}), 200
            
        # Criamos um índice limpo e focado no essencial para facilitar a análise de desempenho
        historico_indexado = []
        for a in atividades:
            historico_indexado.append({
                "id": a.get("id"),
                "nome": a.get("name"),
                "tipo": a.get("type"),
                "data": a.get("start_date_local"),
                "distancia_km": round(a.get("distance", 0) / 1000, 2),
                "tempo_minutos": round(a.get("moving_time", 0) / 60, 1),
                "ritmo_medio": a.get("average_speed")
            })
            
        return jsonify({
            "total_atividades_carregadas": len(historico_indexado),
            "historico": historico_indexado
        }), 200
    else:
        return jsonify({"erro": "Erro ao buscar atividades", "detalhes": response.text}), response.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
