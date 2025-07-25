import click
from flask.cli import AppGroup
from models.noticia import Noticia
from services.gnews_client import buscar_noticias
from services.classificador import classificar_gravidade
from app import db

noticias_cli = AppGroup('noticias', help='Comandos para gerenciar notícias')

@noticias_cli.command('atualizar')
def atualizar_noticias():
    """Busca novas notícias e salva no banco de dados"""
    click.echo("Iniciando atualização de notícias...")
    
    artigos = buscar_noticias()
    
    for artigo in artigos:
        if not Noticia.query.filter_by(url_fonte=artigo['url']).first():
            nova_noticia = Noticia(
                titulo=artigo['title'],
                conteudo=artigo['description'],
                fonte=artigo['source']['name'],
                url_fonte=artigo['url'],
                gravidade=classificar_gravidade(artigo['title'], artigo['description'])
            )
            db.session.add(nova_noticia)
    
    db.session.commit()
    click.echo(f"✅ {len(artigos)} notícias processadas")