from datetime import datetime
from . import db

class Noticia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    fonte = db.Column(db.String(100), nullable=False)
    url_fonte = db.Column(db.String(200), unique=True)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    gravidade = db.Column(db.String(20))  # 'leve', 'moderado', 'grave'
    
    def __repr__(self):
        return f'<Noticia {self.titulo}>'