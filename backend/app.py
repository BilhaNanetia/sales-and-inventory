from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from requests.auth import HTTPBasicAuth
from functools import wraps
import os
import datetime
import sqlite3
import requests
import base64
import logging




# Set up Flask app
TEMPLATE_DIR = os.path.abspath('../frontend/templates')
STATIC_DIR = os.path.abspath('../frontend/static')
DB_PATH = os.path.abspath('../sales_record.db')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

MPESA_ENVIRONMENT = 'sandbox'  # Change to 'production' when moving to production
CONSUMER_KEY = 'OAa4XdMA4ONufa3eyk7PLpKD7KH9oTfSWNewuMDA0ZCaj1YZ'
CONSUMER_SECRET = '4AqHGRBEIbVASnObx1B3xOvW64xV6rnOw7uAjNQ6eFDzTUIdahpHgBetJpbhYogL'
SHORTCODE = '174379'
LIPA_NA_MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

def get_mpesa_access_token():
    url = f'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    if MPESA_ENVIRONMENT == 'sandbox':
        url = f'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
    return response.json()['access_token']

def lipa_na_mpesa_online(phone_number, amount):
    access_token = get_mpesa_access_token()
    api_url = f'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    if MPESA_ENVIRONMENT == 'sandbox':
        api_url = f'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(f'{SHORTCODE}{LIPA_NA_MPESA_PASSKEY}{timestamp}'.encode()).decode('utf-8')

    payload = {
        'BusinessShortCode': SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': amount,
        'PartyA': phone_number,
        'PartyB': SHORTCODE,
        'PhoneNumber': phone_number,
        'CallBackURL': 'https://mydomain.com/path',
        'AccountReference': 'BeeMoto Sales',
        'TransactionDesc': 'Payment for motorbike spares'
    }

    logger.debug(f"Sending request to M-Pesa API: {api_url}")
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Payload: {payload}")

    response = requests.post(api_url, json=payload, headers=headers)

    logger.debug(f"M-Pesa API response status code: {response.status_code}")
    logger.debug(f"M-Pesa API response content: {response.text}")

    return response.json()


# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, password, role):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.role = role

# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Decorator to check for admin access
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'], user['email'], user['password'], user['role'])
    return None

# Authentication routes
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
            if user:
                flash('Username or email already exists')
                return redirect(url_for('signup'))
            
            hashed_password = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                         (username, email, hashed_password))
            conn.commit()
        
        flash('Account created successfully')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['email'], user['password'], user['role'])
            login_user(user_obj)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

# InventoryManager class for managing inventory operations
class InventoryManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def add_item(self, item, quantity, price):
        self.cursor.execute('SELECT id, quantity FROM inventory WHERE LOWER(item) = LOWER(?)', (item,))
        existing_item = self.cursor.fetchone()

        if existing_item:
            item_id, current_quantity = existing_item
            new_quantity = current_quantity + quantity
            self.cursor.execute('UPDATE inventory SET quantity = ?, price = ? WHERE id = ?',
                                (new_quantity, price, item_id))
        else:
            self.cursor.execute('INSERT INTO inventory (item, quantity, price) VALUES (?, ?, ?)',
                                (item, quantity, price))
        self.conn.commit()

    def update_quantity(self, item_id, quantity):
        self.cursor.execute('UPDATE inventory SET quantity = quantity - ? WHERE id = ?',
                            (quantity, item_id))
        self.conn.commit()

    def get_item(self, item_id):
        self.cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
        return self.cursor.fetchone()

    def get_all_items(self):
        self.cursor.execute('SELECT * FROM inventory ORDER BY item ASC')
        return self.cursor.fetchall()

    def check_low_stock(self):
        self.cursor.execute('SELECT * FROM inventory WHERE quantity <= 10')
        return self.cursor.fetchall()
    
    def delete_item(self, item_id):
        self.cursor.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
    def increment_quantity(self, item_name, quantity):
        self.cursor.execute('UPDATE inventory SET quantity = quantity + ? WHERE item = ?',
                            (quantity, item_name))
        self.conn.commit()
        return self.cursor.rowcount > 0

# Initialize InventoryManager
inventory_manager = InventoryManager(DB_PATH)

# SalesRecord class for managing sales operations
class SalesRecord:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def add_sale(self, item, quantity, price):
        date = datetime.date.today().isoformat()
        self.cursor.execute('INSERT INTO sales (date, item, quantity, price) VALUES (?, ?, ?, ?)',
                            (date, item, quantity, price))
        self.conn.commit()

    def get_daily_total(self, date):
        self.cursor.execute('SELECT SUM(quantity * price) FROM sales WHERE date = ?', (date,))
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def get_daily_sales(self, date):
        self.cursor.execute('SELECT id, item, quantity, price FROM sales WHERE date = ?', (date,))
        return self.cursor.fetchall()
    
    def delete_sale(self, sale_id):
        self.cursor.execute('SELECT item, quantity FROM sales WHERE id = ?', (sale_id,))
        deleted_sale = self.cursor.fetchone()
        
        if deleted_sale:
            self.cursor.execute('DELETE FROM sales WHERE id = ?', (sale_id,))
            self.conn.commit()
            return deleted_sale
        return None
    
    def get_weekly_total(self, start_date):
        end_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d') + datetime.timedelta(days=6)).strftime('%Y-%m-%d')
        self.cursor.execute('SELECT SUM(quantity * price) FROM sales WHERE date BETWEEN ? AND ?',
                        (start_date, end_date))
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def get_monthly_total(self, year, month):
        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-31"  # This works for all months
        self.cursor.execute('SELECT SUM(quantity * price) FROM sales WHERE date BETWEEN ? AND ?',
                            (start_date, end_date))
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def get_yearly_total(self, year):
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        self.cursor.execute('SELECT SUM(quantity * price) FROM sales WHERE date BETWEEN ? AND ?',
                            (start_date, end_date))
        result = self.cursor.fetchone()[0]
        return result if result else 0

# Initialize SalesRecord
record = SalesRecord(DB_PATH)

# Route handlers
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/add_inventory', methods=['POST'])
@login_required
@admin_required
def add_inventory():
    data = request.json
    inventory_manager.add_item(data['item'], data['quantity'], data['price'])
    return jsonify({'success': True, 'message': 'Inventory updated successfully'})

@app.route('/get_inventory', methods=['GET'])
@login_required
def get_inventory():
    items = inventory_manager.get_all_items()
    return jsonify({'items': items})

@app.route('/delete_inventory', methods=['POST'])
@login_required
@admin_required
def delete_inventory():
    data = request.json
    item_id = data.get('item_id')
    
    if item_id is None:
        return jsonify({'success': False, 'error': 'No item ID provided'}), 400
    
    success = inventory_manager.delete_item(item_id)
    
    if success:
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
    else:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

@app.route('/check_low_stock', methods=['GET'])
@login_required
def check_low_stock():
    low_stock_items = inventory_manager.check_low_stock()
    return jsonify({'low_stock_items': low_stock_items})

@app.route('/add_sale', methods=['POST'])
@login_required
def add_sale():
    data = request.json
    print(f"Received data: {data}")  # For debugging
    try:
        item_id = int(data['item_id'])
        quantity = int(data['quantity'])
    except (KeyError, ValueError) as e:
        print(f"Error parsing data: {e}")  # For debugging
        return jsonify({'success': False, 'error': f'Invalid item_id or quantity: {e}'}), 400

    item = inventory_manager.get_item(item_id)
    if item is None:
        return jsonify({'success': False, 'error': 'Item not found'}), 404

    item_name, item_quantity, item_price = item[1], item[2], item[3]  

    if item_quantity < quantity:
        return jsonify({
            'success': False, 
            'error': f'Insufficient stock. Requested: {quantity}, Available: {item_quantity}'
        }), 400
    
    try:
        inventory_manager.update_quantity(item_id, quantity)
        record.add_sale(item_name, quantity, item_price)
    except Exception as e:
        print(f"Error adding sale: {e}")  # For debugging
        return jsonify({'success': False, 'error': f'An error occurred while processing the sale: {e}'}), 500

    return jsonify({'success': True})

@app.route('/initiate_payment', methods=['POST'])
@login_required
def initiate_payment():
    try:
        data = request.json
        phone_number = data.get('phone_number')
        amount = data.get('amount')

        # Validate input
        if not phone_number or not amount:
            return jsonify({
                'success': False,
                'error': 'Phone number and amount are required'
            }), 400

        # Validate and format phone number format 
        if phone_number.startswith('0') and len(phone_number) == 10:
            # Convert 07XXXXXXXX to 254XXXXXXXXX
            phone_number = '254' + phone_number[1:]
        elif not (phone_number.startswith('254') and len(phone_number) == 12):
            return jsonify({
                'success': False,
                'error': 'Invalid phone number format. Use 07XXXXXXXX or 254XXXXXXXXX'
            }), 400
        
        # Validate amount (assuming amount should be positive)
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid amount. Must be a positive number'
            }), 400

        # Initiate M-Pesa payment
        response = lipa_na_mpesa_online(phone_number, amount)

        # Check if the response is valid and contains the expected fields
        if not isinstance(response, dict):
            raise ValueError("Invalid response from M-Pesa API")

        
        if 'errorCode' in response:
            return jsonify({
                'success': False,
                'error': f"M-Pesa API error: {response.get('errorMessage', 'Unknown error')}",
                'errorCode': response.get('errorCode')
            }), 400

        # If successful, the response should contain a CheckoutRequestID
        if 'CheckoutRequestID' in response:
            return jsonify({
                'success': True,
                'message': 'Payment initiated successfully',
                'checkoutRequestId': response['CheckoutRequestID']
            }), 200
        
        # If we don't get an error or a CheckoutRequestID
        raise ValueError("Unexpected response from M-Pesa API")
  
    except ValueError as e:
        app.logger.error(f"Value error in initiate_payment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except requests.RequestException as e:
        # Handle any network-related errors
        app.logger.error(f"Network error in initiate_payment: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Network error occurred: {str(e)}'
        }), 500
    except Exception as e:
        # Catch any other unexpected errors
        app.logger.error(f'Unexpected error in initiate_payment: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500

@app.route('/get_daily_total', methods=['GET'])
@admin_required
def get_daily_total():
    date = request.args.get('date')
    total = record.get_daily_total(date)
    return jsonify({'total': total})

@app.route('/get_daily_sales', methods=['GET'])
def get_daily_sales():
    date = request.args.get('date')
    sales = record.get_daily_sales(date)
    return jsonify({'sales': [{'id': sale[0], 'item': sale[1], 'quantity': sale[2], 'price': sale[3]} for sale in sales]})

@app.route('/delete_sale', methods=['POST'])
@login_required
def delete_sale():
    data = request.json
    sale_id = data.get('id')
    if sale_id is None:
        return jsonify({'success': False, 'error': 'No sale ID provided'}), 400
    
    deleted_sale = record.delete_sale(sale_id)
    if deleted_sale:
        item_name, quantity = deleted_sale
        inventory_updated = inventory_manager.increment_quantity(item_name, quantity)
        if inventory_updated:
            return jsonify({'success': True, 'message': 'Sale deleted and inventory updated'})
        else:
            return jsonify({'success': True, 'message': 'Sale deleted but inventory update failed'}), 500
    else:
        return jsonify({'success': False, 'error': 'Sale not found'}), 404
    
@app.route('/search_inventory', methods=['GET'])
@login_required
def search_inventory():
    query = request.args.get('query', '').lower()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM inventory
            WHERE LOWER(item) LIKE ?
            OR LOWER(category) LIKE ?
            OR LOWER(CAST(id AS TEXT)) LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%'))
        items = cursor.fetchall()

    # Sort the items alphabetically by item name
    items.sort(key=lambda x: x[1].lower())

    return jsonify({
        'items': [{'id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3], 'category': item[4]} for item in items]
    })


@app.route('/filter_inventory_by_category', methods=['GET'])
@login_required
def filter_inventory_by_category():
    category_filter = request.args.get('category', '').lower()  

    if not category_filter:
        return jsonify({'error': 'Category parameter is required'}), 400  

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM inventory
            WHERE LOWER(category) LIKE ?
        """, (f'%{category_filter}%',))
        items = cursor.fetchall()

    # Sort the items alphabetically by item name
    items.sort(key=lambda x: x[1].lower())

    return jsonify({
        'items': [{'id': item[0], 'name': item[1], 'quantity': item[2], 'price': item[3], 'category': item[4]} for item in items]
    })


@app.route('/get_weekly_total', methods=['GET'])
@admin_required
def get_weekly_total():
    start_date = request.args.get('start_date')
    total = record.get_weekly_total(start_date)
    return jsonify({'total': total, 'start_date': start_date})

@app.route('/get_monthly_total', methods=['GET'])
@admin_required
def get_monthly_total():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    total = record.get_monthly_total(year, month)
    return jsonify({'total': total})

@app.route('/get_yearly_total', methods=['GET'])
@admin_required
def get_yearly_total():
    year = int(request.args.get('year'))
    total = record.get_yearly_total(year)
    return jsonify({'total': total})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)