from flask import Flask, render_template, request

from test_functions import write
from log import logger

SECRET_KEY = "SECRET_KEY"
SERV_IP = '0.0.0.0'
PORT = 5001

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/', methods=('GET', 'POST'))
def map():
    """Главная страница"""
    status_info = ""
    if request.method == 'POST':
        value = request.form.get("zone")
        if value:
            tx_power = request.form.get("tx_power")
            logger.info(f"Select TX Power is {tx_power}!")
            status_info += write(value, int(tx_power))
    return render_template('map.html', status_info=status_info)


@app.after_request
def add_header(r):
    """что бы избавиться от кеширования"""
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


if __name__ == "__main__":
    app.run(host=SERV_IP, port=PORT)
