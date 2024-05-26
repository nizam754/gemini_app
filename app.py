from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import time
import hmac
import hashlib
import base64
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')  # Change this to a real secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET').encode()
BASE_URL = os.getenv('BASE_URL')

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'user' and password == 'pass':  # Simple check, replace with real authentication
            user = User(id=1)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    ticker = get_ticker('btcusd')
    return render_template('dashboard.html', ticker=ticker)

@app.route('/order', methods=['POST'])
@login_required
def order():
    symbol = request.form['symbol']
    amount = request.form['amount']
    price = request.form['price']
    side = request.form['side']
    order = place_order(symbol, amount, price, side)
    flash(f'Order placed: {order}')
    return redirect(url_for('dashboard'))

def get_ticker(symbol):
    """Get ticker information for a specific symbol."""
    endpoint = f'/pubticker/{symbol}'
    url = BASE_URL + endpoint
    response = requests.get(url)
    return response.json()

def place_order(symbol, amount, price, side, order_type='exchange limit'):
    """Place an order on the Gemini exchange."""
    endpoint = '/order/new'
    url = BASE_URL + endpoint
    nonce = str(int(time.time() * 1000))
    payload = {
        "request": endpoint,
        "nonce": nonce,
        "symbol": symbol,
        "amount": str(amount),
        "price": str(price),
        "side": side,
        "type": order_type
    }
    encoded_payload = json.dumps(payload).encode()
    b64 = base64.b64encode(encoded_payload)
    signature = hmac.new(API_SECRET, b64, hashlib.sha384).hexdigest()

    headers = {
        'Content-Type': 'text/plain',
        'Content-Length': '0',
        'X-GEMINI-APIKEY': API_KEY,
        'X-GEMINI-PAYLOAD': b64,
        'X-GEMINI-SIGNATURE': signature,
        'Cache-Control': 'no-cache'
    }

    response = requests.post(url, headers=headers)
    return response.json()

if __name__ == "__main__":
    app.run(debug=True)
