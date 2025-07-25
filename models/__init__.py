from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .noticia import Noticia  # Importar após db ser criado