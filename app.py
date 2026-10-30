import os
from flask import Flask, request, jsonify
from stravalib.client import Client

app = Flask(_name_)

# Suas credenciais do Strava
CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"
REFRESH_TOKEN = 13a16ad7c8bdd6aafdba6fc88a88b55d2e58d762

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
    Aqui é onde o Strava avisa quando algo acontece (ex: nova atividade criada).
    """
    dados = request.json
    print(f"Evento recebido do Strava: {dados}")

    # Verificamos se é um evento de criação de uma nova atividade
    if dados.get('object_type') == 'activity' and dados.get('aspect_type') == 'create':
        owner_id = dados.get('owner_id')
        activity_id = dados.get('object_id')
        print(f"Nova atividade detectada! ID: {activity_id} do usuário {owner_id}")

        # Aqui podemos chamar a função para baixar os dados da atividade via API do Strava
        processar_nova_atividade(activity_id)

    return jsonify({"status": "recebido"}), 200

def processar_nova_atividade(activity_id):
    try:
        client = Client()
        response = client.refresh_access_token(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            refresh_token=REFRESH_TOKEN
        )
        client.access_token = response['access_token']
        
        # Pega os detalhes completos da atividade recém-criada
        atividade = client.get_activity(activity_id)
        print(f"Detalhes baixados: {atividade.name} - {atividade.distance} - {atividade.moving_time}")
        
        # [Opcional] Aqui você pode salvar em um banco de dados, enviar para uma IA, etc.
        
    except Exception as e:
        print(f"Erro ao processar atividade do Strava: {e}")

if _name_ == '_main_':
    app.run(host='0.0.0.0', port=5000)
