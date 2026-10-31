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
        # Mostra o erro exato do Strava nos logs do Render
        print("Resposta detalhada do Strava:", response.text)
        return response.json().get('access_token')
    except Exception as e:
        print(f"Erro ao obter access token: {e}")
        return None
