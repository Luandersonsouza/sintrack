import requests
from datetime import datetime, timedelta
from config import Config

def buscar_noticias():
    params = {
        'q': 'acidente OR trânsito OR congestionamento alagoas',
        'lang': 'pt',
        'max': 10,
        'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'token': Config.GNEWS_API_KEY
    }
    
    try:
        response = requests.get('https://gnews.io/api/v4/search', params=params)
        return response.json().get('articles', [])
    except Exception as e:
        print(f"Erro ao buscar notícias: {e}")
        return []