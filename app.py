import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Credenciais do Strava
CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"
REFRESH_TOKEN = "13a16ad7c8dd6aafdba6fc88a88b55d2e58d762"

# Configurações de E-mail (Lidas do Render)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

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

def enviar_email(assunto, corpo):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = EMAIL_DESTINATARIO
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(corpo, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

@app.route('/enviar-historico-email', methods=['GET'])
def enviar_historico_email():
    if not EMAIL_REMETENTE or not EMAIL_SENHA or not EMAIL_DESTINATARIO:
        return jsonify({"erro": "Variáveis de ambiente de e-mail não configuradas corretamente no Render."}), 500

    per_page = request.args.get('per_page', default=10, type=int)
    
    access_token = obter_access_token()
    if not access_token:
        return jsonify({"erro": "Não foi possível obter o token do Strava"}), 500
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}", headers=headers)
    
    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar atividades no Strava", "detalhes": response.text}), response.status_code
        
    atividades = response.json()
    if not atividades:
        return jsonify({"mensagem": "Nenhuma atividade encontrada."}), 200

    enviados = 0
    for a in atividades:
        atividade_id = a.get("id")
        nome = a.get("name")
        data = a.get("start_date_local", "data_desconhecida")
        tipo = a.get("type")
        distancia_km = round(a.get("distance", 0) / 1000, 2)
        tempo_min = round(a.get("moving_time", 0) / 60, 1)
        
        assunto = f"[Strava] Relatório de Treino: {nome} ({tipo})"
        corpo = f"""Detalhes do Treino:\n
- ID: {atividade_id}
- Nome: {nome}
- Tipo: {tipo}
- Data: {data}
- Distância: {distancia_km} km
- Tempo em Movimento: {tempo_min} minutos
"""
        sucesso = enviar_email(assunto, corpo)
        if sucesso:
            enviados += 1

    return jsonify({
        "status": "sucesso",
        "total_enviados": enviados
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
