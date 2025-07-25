from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
import re
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

def classificar_gravidade(titulo, conteudo):
    """Classifica a gravidade com regras específicas para trânsito"""
    try:
        nltk.data.find('sentiment/vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon')
    
    # Palavras-chave para cada nível
    palavras_grave = ['morto', 'fatal', 'tombou', 'atropelamento', 'grave']
    palavras_moderado = ['ferido', 'colisão', 'batida', 'acidente', 'hospital']
    
    # Verificação por palavras-chave
    texto = f"{titulo} {conteudo}".lower()
    
    if any(palavra in texto for palavra in palavras_grave):
        return "grave"
    elif any(palavra in texto for palavra in palavras_moderado):
        return "moderado"
    
    # Análise de sentimento como fallback
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(texto)["compound"]
    
    if score < -0.3:  # Limiar ajustado
        return "moderado"
    elif score < -0.6:
        return "grave"
    return "leve"