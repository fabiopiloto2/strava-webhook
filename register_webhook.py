import requests

# Suas credenciais e dados configurados
CLIENT_ID = 292584
CLIENT_SECRET = "1d5172f10e55ee584968381005db4156b3c1811b"
CALLBACK_URL = "https://strava-webhook-vi7k.onrender.com/webhook"
VERIFY_TOKEN = "MEU_TOKEN_SECRETO_DE_VALIDACAO"

# Fazendo a requisição POST para o Strava registar o Webhook
response = requests.post(
    "https://www.strava.com/api/v3/push_subscriptions",
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'callback_url': CALLBACK_URL,
        'verify_token': VERIFY_TOKEN
    }
)

print("Status Code:", response.status_code)
print("Resposta:", response.json())
