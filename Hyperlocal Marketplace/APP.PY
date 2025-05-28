import math
import os
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import mysql.connector

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
mail = Mail(app)

# DB Connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Haversine Distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Home/Login
@app.route('/')
def login():
    return render_template('login.html')

# Email OTP Page
@app.route('/verify_email', methods=['GET'])
def verify_email():
    return render_template('verify_email.html', show_otp=False)

# Send OTP
@app.route('/send_otp', methods=['POST'])
def send_otp():
    email = request.form['email']
    otp = str(random.randint(100000, 999999))

    session['otp'] = otp
    session['email'] = email

    msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"Hi Tarun, your OTP is: {otp}"
    mail.send(msg)

    flash("OTP has been sent to your email.", "info")
    return render_template('verify_email.html', show_otp=True)

# Verify OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form.get('otp')
    actual_otp = session.get('otp')

    if entered_otp == actual_otp:
        flash("OTP verified successfully!", "success")
        session.pop('otp', None)           # Optional: clear OTP from session
        session.pop('otp_sent', None)      # Optional: hide OTP form on reload
        return redirect(url_for('signup'))  # ⬅️ Redirect to signup route
    else:
        flash("Invalid OTP. Please try again.", "error")
        return redirect(url_for('verify_email'))

@app.route('/dashboard')
def dashboard():
    return "Welcome, OTP verified!"

# Signup Page
@app.route('/signup')
def signup():
    return render_template('signup.html')

# Register
@app.route('/register', methods=['POST'])
def register():
    try:
        user_type = request.form['user_type']
        email = request.form['email']
        password = request.form['password']
        phone_number = request.form['phone_number']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        if user_type == 'shopkeeper':
            shop_name = request.form['shop_name']
            shop_address = request.form['shop_address']
            cursor.execute("""
                INSERT INTO shopkeepers (email, password, shop_name, shop_address, phone_number, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (email, hashed_password, shop_name, shop_address, phone_number, latitude, longitude))

        elif user_type == 'buyer':
            delivery_address = request.form['delivery_address']
            cursor.execute("""
                INSERT INTO buyers (email, password, phone_number, delivery_address, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (email, hashed_password, phone_number, delivery_address, latitude, longitude))

        conn.commit()
        flash("Registration successful. Please log in.")
    except Exception as e:
        flash(f"Registration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

    return redirect(url_for('login'))

# Login Route
@app.route('/login', methods=['POST'])
def login_post():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check shopkeepers
    cursor.execute("SELECT * FROM shopkeepers WHERE email=%s", (email,))
    shopkeeper = cursor.fetchone()
    if shopkeeper and check_password_hash(shopkeeper['password'], password):
        return redirect(url_for('shop_dashboard', shop_id=shopkeeper['id']))

    # Check buyers
    cursor.execute("SELECT * FROM buyers WHERE email=%s", (email,))
    buyer = cursor.fetchone()
    if buyer and check_password_hash(buyer['password'], password):
        session['buyer_id'] = buyer['id']
        session['latitude'] = buyer['latitude']
        session['longitude'] = buyer['longitude']
        return redirect(url_for('buyer_dashboard', buyer_id=buyer['id']))

    flash("Invalid email or password.")
    return redirect(url_for('login'))

# Shopkeeper Dashboard
@app.route('/shop/<int:shop_id>', methods=['GET', 'POST'])
def shop_dashboard(shop_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST' and 'delete_product' in request.form:
        product_id = request.form['delete_product']
        cursor.execute("DELETE FROM products WHERE id = %s AND shopkeeper_id = %s", (product_id, shop_id))
        conn.commit()
        flash('Product deleted successfully.')
        return redirect(url_for('shop_dashboard', shop_id=shop_id))

    cursor.execute("SELECT * FROM shopkeepers WHERE id = %s", (shop_id,))
    shopkeeper = cursor.fetchone()

    cursor.execute("SELECT * FROM products WHERE shopkeeper_id = %s", (shop_id,))
    products = cursor.fetchall()

    conn.close()
    return render_template('shop_dashboard.html', shopkeeper=shopkeeper, products=products)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    flash("Product deleted successfully.", "success")
    conn.close()
    return redirect(url_for('shop_dashboard', shop_id=session.get('shop_id')))

# Buyer Dashboard
@app.route('/buyer_dashboard', methods=['GET', 'POST'])
def buyer_dashboard():
    user_lat = session.get('latitude', 0.0)
    user_lon = session.get('longitude', 0.0)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    search_query = request.form.get('search', '')
    if search_query:
        cursor.execute("""
            SELECT p.*, s.shop_name, s.latitude, s.longitude 
            FROM products p 
            JOIN shopkeepers s ON p.shopkeeper_id = s.id 
            WHERE LOWER(p.name) LIKE %s
        """, ('%' + search_query.lower() + '%',))
    else:
        cursor.execute("""
            SELECT p.*, s.shop_name, s.latitude, s.longitude 
            FROM products p 
            JOIN shopkeepers s ON p.shopkeeper_id = s.id
        """)

    all_products = cursor.fetchall()

    products_within_10km = []
    for product in all_products:
        shop_lat = product['latitude']
        shop_lon = product['longitude']
        distance = haversine(float(user_lat), float(user_lon), float(shop_lat), float(shop_lon))
        if distance <= 10:
            product['distance'] = round(distance, 2)
            products_within_10km.append(product)

    conn.close()
    return render_template('buyer_dashboard.html', products=products_within_10km, search_query=search_query)

# Upload Product
@app.route('/upload_product/<int:shop_id>', methods=['POST'])
def upload_product(shop_id):
    name = request.form['product_name']
    price = request.form['price']
    image = request.files['product_image']

    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            image.save(image_path)
            conn = get_db_connection()
            cursor = conn.cursor()
            description = "N/A"
            quantity = 1
            image_url = filename

            cursor.execute("""
                INSERT INTO products (shopkeeper_id, name, price, description, quantity, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (shop_id, name, price, description, quantity, image_url))

            conn.commit()
            flash("Product uploaded successfully!")
        except Exception as e:
            flash(f"Error uploading product: {e}")
        finally:
            conn.close()
    else:
        flash("No image file provided.")

    return redirect(url_for('shop_dashboard', shop_id=shop_id))

if __name__ == '__main__':
    app.run(debug=True)
