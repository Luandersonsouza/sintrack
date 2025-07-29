from importlib.metadata import version
from flask import Flask, render_template

import folium
from folium.plugins import HeatMap
import pandas as pd
import tempfile

from datetime import datetime
import click
from flask.cli import AppGroup

import sys
import time
from pathlib import Path
import os
PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

from services.gnews_client import buscar_noticias
from models import Noticia, db
from services.classificador import classificar_gravidade  # Importação adicionada

# Inicializa a aplicação e extensões
app = Flask(__name__)

# ========== CONFIGURAÇÕES ==========
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/sintrack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ========== FUNÇÕES AUXILIARES ==========
def criar_dados():
    """Criar dados simples para o mapa"""
    dados = pd.DataFrame({
        'latitude': [-9.6601, -9.6403, -9.6204],
        'longitude': [-35.7400, -35.7100, -35.7300],
        'intensidade': [45, 55, 70],
        'info': [
            "Engarrafamento devido a obras",
            "Acidente: Moto x Carro",
            "Atropelamento leve",
        ],
        'tipo': [
            "engarrafamento",
            "acidente",
            "atropelamento",
        ]
    })
    return dados

def criar_mapa():
    """Criar mapa do Folium"""
    dados = criar_dados()
    bounds = [[-9.85, -35.85], [-9.50, -35.60]]

    mapa = folium.Map(
        location=[-9.6488, -35.7089],
        zoom_start=12,
        min_lat=bounds[0][0],
        max_lat=bounds[1][0],
        min_lon=bounds[0][1],
        max_lon=bounds[1][1],
        max_bounds=True
    )

    icones = {
        "acidente": {"icon": "car-crash", "color": "red", "prefix": "fa"},
        "buraco": {"icon": "road", "color": "black", "prefix": "fa"},
        "atropelamento": {"icon": "person-walking", "color": "darkred", "prefix": "fa"},
        "semaforo": {"icon": "traffic-light", "color": "orange", "prefix": "fa"},
        "engarrafamento": {"icon": "car", "color": "blue", "prefix": "fa"}
    }

    HeatMap(
        data=dados[['latitude', 'longitude', 'intensidade']].values.tolist(),
        radius=15,
        blur=10,
    ).add_to(mapa)

    for idx, row in dados.iterrows():
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=row['info'],
            icon=folium.Icon(
                icon=icones[row['tipo']]["icon"],
                color=icones[row['tipo']]["color"],
                prefix=icones[row['tipo']]["prefix"]
            )
        ).add_to(mapa)
    
    return mapa

def carregar_noticias():
    """Simular dados de notícias raspadas"""
    return [
        {
            'titulo': 'Colisão entre ônibus e carro deixa 3 feridos na BR-101',
            'resumo': 'Acidente ocorreu na altura do km 12, sentido norte...',
            'local': 'Maceió',
            'data': datetime(2023, 6, 15),
            'gravidade': 'grave',
            'fonte': 'Gazeta Web'
        },
        {
            'titulo': 'Motociclista fica ferido após colisão na Av. Rio Branco',
            'resumo': 'Vítima foi levada para hospital municipal...',
            'local': 'Arapiraca',
            'data': datetime(2023, 6, 14),
            'gravidade': 'moderado',
            'fonte': 'Tribuna Independente'
        },
        {
            'titulo': 'Batida entre dois veículos causa congestionamento',
            'resumo': 'Trânsito ficou lento na região por cerca de 2 horas...',
            'local': 'Rio Largo',
            'data': datetime(2023, 6, 13),
            'gravidade': 'leve',
            'fonte': 'Cada Minuto'
        }
    ]

# ========== COMANDOS CLI ==========
noticias_cli = AppGroup('noticias', help='Comandos para gerenciamento de notícias')

@noticias_cli.command('atualizar')
def atualizar_noticias():
    """Atualiza as notícias a partir de fontes externas"""
    try:
        click.echo("🔄 Buscando notícias atualizadas...")
        novas_noticias = buscar_noticias()
        
        adicionadas = 0
        for noticia in novas_noticias:
            if not Noticia.query.filter_by(url_fonte=noticia['url']).first():
                nova = Noticia(
                    titulo=noticia['title'],
                    conteudo=noticia['description'],
                    fonte=noticia['source']['name'],
                    url_fonte=noticia['url'],
                    data_publicacao=datetime.strptime(noticia['publishedAt'], '%Y-%m-%dT%H:%M:%SZ'),
                    gravidade=classificar_gravidade(noticia['title'], noticia['description'])  # Agora está definido
                )
                db.session.add(nova)
                adicionadas += 1
        
        db.session.commit()
        click.echo(f"✅ {adicionadas} novas notícias adicionadas ao banco de dados")
        
    except Exception as e:
        click.echo(f"❌ Erro ao atualizar notícias: {str(e)}", err=True)

app.cli.add_command(noticias_cli)

# ========== ROTAS ==========
@app.route('/')
def index():
    """Página principal com mapa"""
    try:
        mapa = criar_mapa()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            mapa.save(f.name)
            temp_file = f.name
        
        with open(temp_file, 'r', encoding='utf-8') as f:
            mapa_html = f.read()
        
        os.unlink(temp_file)
        return render_template('index.html', mapa=mapa_html)
        
    except Exception as e:
        mapa_emergencia = """
        <div style="width: 100%; height: 500px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; border: 2px dashed #ccc; border-radius: 10px;">
            <div style="text-align: center; color: #666;">
                <h3>🗺️ Mapa Temporariamente Indisponível</h3>
                <p>Carregando dados de Maceió...</p>
                <p>Erro: """ + str(e) + """</p>
            </div>
        </div>
        """
        return render_template('index.html', mapa=mapa_emergencia)

@app.route('/noticias')
def noticias():
    """Página de notícias sobre acidentes"""
    try:
        noticias = carregar_noticias()
        return render_template('noticias.html', noticias=noticias)
    except Exception as e:
        return render_template('noticias.html', noticias=[], erro=str(e))

@app.route('/test')
def test():
    return """
    <h1>🚀 SinTrack - Teste de Funcionamento</h1>
    <p>✅ Flask está funcionando!</p>
    <p><a href="/">← Mapa</a> | <a href="/noticias">Notícias →</a></p>
    """

@app.route('/mapa-simples')
def mapa_simples():
    """Mapa básico sem template (para debug)"""
    try:
        mapa = criar_mapa()
        return mapa._repr_html_()
    except Exception as e:
        return f"<h1>Erro no mapa: {e}</h1>"
    
@app.route('/favicon.ico')
def favicon():
    return '', 404

# ========== INICIALIZAÇÃO ==========
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        from datetime import datetime
        import platform
        
        # Cores ANSI personalizadas
        class Cores:
            AZUL = '\033[1;34m'
            VERDE = '\033[1;32m'
            CIANO = '\033[1;36m'
            AMARELO = '\033[1;33m'
            ROXO = '\033[1;35m'
            RESET = '\033[0m'
            NEGRITO = '\033[1m'
            SUBLINHADO = '\033[4m'
        
        # Arte ASCII personalizada
        ascii_art = rf"""
{Cores.CIANO}   _____ _       _____             _    
  / ____(_)     |  __ \           | |   
 | (___  _ _ __ | |__) |___  _ __ | | __
  \___ \| | '_ \|  _  // _ \| '_ \| |/ /
  ____) | | | | | | \ \ (_) | | | |   < 
 |_____/|_|_| |_|_|  \_\___/|_| |_|_|\_\{Cores.RESET}
        """
        
        
        
        print(f"{Cores.CIANO}Inicializando servidor...{Cores.RESET}")
        time.sleep(0.5)
        python_ver = platform.python_version()
        flask_ver = version('flask')
        hora_inicio = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        print(ascii_art)
        print(f"{Cores.AZUL}═{Cores.ROXO}╦{Cores.VERDE}═{Cores.AMARELO}╦{Cores.CIANO}═{'╦═'*20}{Cores.RESET}")
        print(f"{Cores.NEGRITO}🚀 INÍCIO DO SISTEMA{Cores.RESET}")
        print(f"{Cores.AZUL}• {Cores.VERDE}Ambiente:{Cores.RESET} {Cores.AMARELO}{'Desenvolvimento' if app.config['DEBUG'] else 'Produção'}{Cores.RESET}")
        print(f"{Cores.AZUL}• {Cores.VERDE}Python:{Cores.RESET} {Cores.AMARELO}v{python_ver}{Cores.RESET}")
        print(f"{Cores.AZUL}• {Cores.VERDE}Flask:{Cores.RESET} {Cores.AMARELO}v{flask_ver}{Cores.RESET}")
        print(f"{Cores.AZUL}• {Cores.VERDE}Hora:{Cores.RESET} {Cores.AMARELO}{hora_inicio}{Cores.RESET}")
        print(f"{Cores.AZUL}═{Cores.ROXO}╩{Cores.VERDE}═{Cores.AMARELO}╩{Cores.CIANO}═{'╩═'*20}{Cores.RESET}")
        print(f"{Cores.NEGRITO}🌐 ROTAS DISPONÍVEIS:{Cores.RESET}")
        print(f"  {Cores.AZUL}↳ {Cores.VERDE}Página Principal:{Cores.RESET} {Cores.SUBLINHADO}http://127.0.0.1:5000/{Cores.RESET}")
        print(f"  {Cores.AZUL}↳ {Cores.VERDE}Notícias:{Cores.RESET} {Cores.SUBLINHADO}http://127.0.0.1:5000/noticias{Cores.RESET}")
        print(f"  {Cores.AZUL}↳ {Cores.VERDE}Mapa Simples:{Cores.RESET} {Cores.SUBLINHADO}http://127.0.0.1:5000/mapa-simples{Cores.RESET}")
        print(f"{Cores.AZUL}═{'═'*45}{Cores.RESET}")
        print(f"{Cores.NEGRITO}⚙️ COMANDOS CLI:{Cores.RESET}")
        print(f"  {Cores.AMARELO}▶ flask noticias atualizar{Cores.RESET} - Atualiza o banco de notícias")
        print(f"  {Cores.AMARELO}▶ flask shell{Cores.RESET} - Abre shell interativo")
        print(f"{Cores.CIANO}═{'═'*45}{Cores.RESET}\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=True)