import os
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"

# Configurações de E-mail (Lidas do Render)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

def obter_access_token_via_codigo():
    """Troca o código de autorização fresco diretamente pelo token de acesso e refresh token do Strava."""
    try:
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': 'd9ea4689125c25390ab01610e30db467f7c57153',
                'grant_type': 'authorization_code'
            }
        )
        dados = response.json()
        print("RESPOSTA DA TROCA DO CÓDIGO:", dados)
        return dados.get('access_token')
    except Exception as e:
        print(f"Erro ao obter token via código: {e}")
        return None

def atividade_ja_enviada(atividade_id):
    """Verifica no Gmail se já existe um e-mail enviado com o ID desta atividade."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_REMETENTE, EMAIL_SENHA)
        
        pasta_selecionada = False
        for pasta in ['"[Gmail]/Enviados"', '"[Gmail]/Sent Mail"', 'INBOX']:
            try:
                status, _ = mail.select(pasta)
                if status == 'OK':
                    pasta_selecionada = True
                    break
            except:
                continue
                
        if not pasta_selecionada:
            mail.logout()
            return False
        
        status, messages = mail.search(None, f'(BODY "{atividade_id}")')
        if status == 'OK' and messages[0]:
            mail.logout()
            return True
        
        mail.logout()
        return False
    except Exception as e:
        print(f"Erro ao verificar duplicados no e-mail: {e}")
        return False

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
@app.route('/')
def home():
    return "Servidor do Strava ativo! Aceda a /enviar-historico-email para enviar os treinos."

@app.route('/enviar-historico-email', methods=['GET'])
def enviar_historico_email():

    if not EMAIL_REMETENTE or not EMAIL_SENHA or not EMAIL_DESTINATARIO:
        return jsonify({"erro": "Variáveis de ambiente de e-mail não configuradas corretamente no Render."}), 500

    per_page = request.args.get('per_page', default=10, type=int)
    
    access_token = obter_access_token_via_codigo()
    if not access_token:
        return jsonify({"erro": "Não foi possível obter o token do Strava através do código"}), 500
    
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"https://www.strava.com/api/v3/athlete/activities?per_page={per_page}", headers=headers)
    
    if response.status_code != 200:
        return jsonify({"erro": "Erro ao buscar atividades no Strava", "detalhes": response.text}), response.status_code
        
    atividades = response.json()
    if not atividades:
        return jsonify({"mensagem": "Nenhuma atividade encontrada."}), 200

    enviados = 0
    ignorados = 0
    
    for a in atividades:
        atividade_id = str(a.get("id"))
        nome = a.get("name")
        data = a.get("start_date_local", "data_desconhecida")
        tipo = a.get("type")
        distancia_km = round(a.get("distance", 0) / 1000, 2)
        tempo_min = round(a.get("moving_time", 0) / 60, 1)
        
        if atividade_ja_enviada(atividade_id):
            ignorados += 1
            continue

        assunto = f"[Strava] Relatório de Treino: {nome} ({tipo})"
        corpo = f"Detalhes do Treino:\n\n- ID: {atividade_id}\n- Nome: {nome}\n- Tipo: {tipo}\n- Data: {data}\n- Distância: {distancia_km} km\n- Tempo em Movimento: {tempo_min} minutos"
        
        if enviar_email(assunto, corpo):
            enviados += 1

    return jsonify({
        "status": "sucesso",
        "novos_enviados": enviados,
        "duplicados_ignorados": ignorados
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
