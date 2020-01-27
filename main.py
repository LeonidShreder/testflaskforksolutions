import datetime
import json
from cProfile import run
from flask import Flask, request, render_template
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import requests
from production import SHOP_ID, SHOP_SECRET_KEY

app = Flask(__name__)


def get_resource_as_string(name, charset='utf-8'):
    with app.open_resource(name) as f:
        return f.read().decode(charset)


app.jinja_env.globals['get_resource_as_string'] = get_resource_as_string
shop_order_id = 0


def generate_sign(params):
    plain_text = ''
    for key in sorted(params):
        if plain_text:
            plain_text += ':'
        plain_text += str(params[key])

    return hashlib.md5(plain_text.encode('utf-8')).hexdigest()


def init_log_handler():
    logHandler = RotatingFileHandler('log.log', maxBytes=1000, backupCount=1)
    logHandler.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(logHandler)


def log_transaction(currency, amount, datetime, description, shop_order_id):
    app.logger.info(
        json.dumps(str({'currency': currency, 'amount': amount, 'datetime': datetime,
                        'description': description, 'shop_order_id': shop_order_id})))


@app.route('/')
@app.route('/index')
def index():
    init_log_handler()
    return render_template('index.html')


def make_payment_eur(amount, currency, shop_order_id, description):
    currency_id = 978

    sign = generate_sign({'amount': amount, 'currency': currency_id, 'shop_id': SHOP_ID,
                          'shop_order_id': shop_order_id})
    try:
        r = requests.post('https://pay.piastrix.com/ru/pay', data=
        {'amount': amount, 'currency': currency_id, 'shop_id': SHOP_ID, 'sign': sign,
         'shop_order_id': shop_order_id, 'description': description})

        if r.status_code == requests.codes.ok:
            log_transaction(currency, amount, str(datetime.datetime.now()), description, shop_order_id)
            res = 'Successful payment in EUR'
        else:
            res = 'Error occurs during payment in EUR'
    except:
        res = 'Error occurs during payment in EUR'
    return res


def make_payment_usd(amount, currency, shop_order_id, description, payer_currency):

    currency_id = 840
    payer_currency = 840
    sign = generate_sign({'amount': amount, 'currency': currency_id, 'shop_id': SHOP_ID,
                          'shop_order_id': shop_order_id, 'payer_currency': payer_currency})
    try:
        r = requests.post('https://core.piastrix.com/bill/create', data=
        {'amount': amount, 'currency': currency_id, 'shop_id': SHOP_ID, 'sign': sign,
         'shop_order_id': shop_order_id, 'description': description, 'payer_currency': payer_currency})

        if r.status_code == requests.codes.ok:
            log_transaction(currency, amount, str(datetime.datetime.now()), description, shop_order_id)
            res = 'Successful payment in USD'
        else:
            res = 'Error occurs during payment in USD'
    except:
        res = 'Error occurs during payment in USD'

    return res


def make_payment_rub(amount, currency, shop_order_id, description):
    currency_id = 643
    payway = 'card_rub'
    sign = generate_sign({'amount': amount, 'currency': currency_id, 'payway': payway, 'shop_id': SHOP_ID,
                          'shop_order_id': shop_order_id})
    try:
        r = requests.post('https://payeer.com/ajax/api/api.php', data=
        {'amount': amount, 'currency': currency_id, 'shop_id': SHOP_ID, 'payway': payway, 'sign': sign,
         'shop_order_id': shop_order_id, 'description': description})

        if r.status_code == requests.codes.ok:
            log_transaction(currency, amount, str(datetime.datetime.now()), description,  shop_order_id)
            res = 'Successful payment in RUB'
        else:
            res = 'Error occurs during payment in RUB'
    except:
        res = 'Error occurs during payment in RUB'

    return res


@app.route('/pay', methods=['GET', 'POST'])
def pay():
    if request.method == 'POST':
        amount = float(request.form.get('amount', None))
        currency = request.form.get('currency', None)
        description = request.form.get('description', None)
        payer_currency = 643

        if not amount:
            return 'Empty payment'

        global shop_order_id
        shop_order_id += 1

        if currency == 'rub':
            return make_payment_rub(amount, currency, shop_order_id, description)
        if currency == 'eur':
            return make_payment_eur(amount, currency, shop_order_id, description)
        if currency == 'usd':
            return make_payment_usd(amount, payer_currency, currency, shop_order_id, description)



if __name__ == '__main__':
    app.run(debug=True)
