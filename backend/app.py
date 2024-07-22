import os
import datetime
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Set up Flask app
TEMPLATE_DIR = os.path.abspath('../frontend/templates')
STATIC_DIR = os.path.abspath('../frontend/static')
DB_PATH = os.path.abspath('../sales_record.db')

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key

# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

# Database connection helper function
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user:
        return User(user['id'], user['username'], user['email'], user['password'])
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
            user_obj = User(user['id'], user['username'], user['email'], user['password'])
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
        self.cursor.execute('SELECT * FROM inventory')
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

@app.route('/get_daily_total', methods=['GET'])
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

@app.route('/get_monthly_total', methods=['GET'])
def get_monthly_total():
    year = int(request.args.get('year'))
    month = int(request.args.get('month'))
    total = record.get_monthly_total(year, month)
    return jsonify({'total': total})

@app.route('/get_yearly_total', methods=['GET'])
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