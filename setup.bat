@echo off
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt
set FLASK_APP=app.py
set FLASK_ENV=development
flask run