import os
import re
import smtplib
import random
import string
from flask import session
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, flash, url_for, g,jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from cryptography.fernet import Fernet
from passwordmanager import save_password, get_saved_passwords, update_password, delete_password_entry
from database import get_db, close_db, init_db  
from dotenv import load_dotenv
from database import get_password 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///password_manager.db'
db = SQLAlchemy(app)

# Load environment variables
load_dotenv()

# Debugging step to confirm values are loaded
print(f"EMAIL_USER: {os.getenv('EMAIL_USER')}")
print(f"EMAIL_PASSWORD: {os.getenv('EMAIL_PASSWORD')}")

# Define Password model
class Password(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    website = db.Column(db.String(100), nullable=False, unique=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()


# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey"

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"  # Redirect users to login page if not logged in

# Load encryption key
def load_encryption_key():
    key_path = "key.env"
    if os.path.exists(key_path):
        with open(key_path, "rb") as file:
            key = file.read()
        try:
            Fernet(key)  # Validate key
            return key
        except ValueError:
            print("Invalid key format, generating a new key...")
            os.remove(key_path)
    key = Fernet.generate_key()
    with open(key_path, "wb") as file:
        file.write(key)
    return key

# Initialize cipher
fernet_key = load_encryption_key()
cipher = Fernet(fernet_key)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    close_db(db)

    if user:
        return User(id=user[0], username=user[1], email=user[2])
    return None

@app.route('/')
def home():
    return redirect(url_for('login'))  # Always go to login page first 

def send_otp_email(user_email):
    # Generate a 6-digit OTP
    otp = ''.join(random.choices(string.digits, k=6))
    session['otp'] = otp  # Store OTP in Flask session

    # Replace these with your actual Gmail credentials
    sender_email = "bindhumadhav2006@gmail.com"  # Enter your Gmail address here
    sender_password = "vcvqkxsmymkdhvxn"  # Enter your Gmail App Password here
    subject = "Your OTP for Login"
    body = f"Your OTP is: {otp}"

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = user_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Start TLS encryption
        server.login(sender_email, sender_password)  # Login to Gmail
        server.sendmail(sender_email, user_email, msg.as_string())  # Send email
        server.quit()  # Close connection
        print(f"OTP {otp} sent successfully to {user_email}")  # Debug log
        return True
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your email and app password.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False
@app.route('/get_credentials', methods=['GET'])
def get_credentials():
    website = request.args.get('website')
    if not website:
        return jsonify({'error': 'Website parameter missing'}), 400

    password_entry = get_password(website)
    if password_entry:
        return jsonify({
            'website': password_entry['website'],
            'username': password_entry['username'],
            'password': password_entry['password']
        })
    else:
        return jsonify({'error': 'No credentials found for this website'}), 404

# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))  

    if request.method == 'POST':
        entered_username = request.form['username']
        entered_password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (entered_username,))
        user = cursor.fetchone()
        cursor.close()
        close_db(db)

        if user:
            encrypted_password = user[3]  # Stored encrypted password
            print(f"Encrypted password from DB: {encrypted_password}")  # Debug
            try:
                # Ensure encrypted_password is a string before encoding
                if not isinstance(encrypted_password, str):
                    flash("Stored password data is corrupted.", "error")
                    return render_template('login.html')

                decrypted_password = cipher.decrypt(encrypted_password.encode()).decode()
                if decrypted_password == entered_password:
                    session['temp_user'] = user[1]  # Username
                    session['temp_user_id'] = user[0]  # User ID
                    session['temp_user_email'] = user[2]  # Email

                    if send_otp_email(user[2]):
                        flash("OTP sent to your email. Please verify.", "info")
                        return redirect(url_for('verify_otp'))  
                    else:
                        flash("Failed to send OTP. Try again.", "error")
                else:
                    flash("Invalid username or password.", "error")
            except ValueError as e:
                flash(f"Decryption failed: {str(e)}. Possible corrupted data or key mismatch.", "error")
            except Exception as e:
                flash(f"Unexpected error during decryption: {str(e)}", "error")
        else:
            flash("Invalid username or password.", "error")

    return render_template('login.html')
# ✅ Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))  

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                flash("Username already exists.", "error")
                return redirect(url_for('signup'))

            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email already exists.", "error")
                return redirect(url_for('signup'))

            encrypted_password = cipher.encrypt(password.encode()).decode()
            encrypted_password = cipher.encrypt(password.encode()).decode()
            print(f"Newly encrypted password: {encrypted_password}")  # Debug
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, encrypted_password))
            db.commit()

            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))

        except Exception as e:
            flash(f"Error: {e}", "error")
            db.rollback()

        finally:
            cursor.close()
            close_db(db)

    return render_template('signup.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_user' not in session:
        return redirect(url_for('login'))  # If session expired, go back to login

    if request.method == 'POST':
        entered_otp = request.form['otp']

        if entered_otp == session.get('otp'):
            logged_in_user = User(id=session['temp_user_id'], username=session['temp_user'], email="")
            login_user(logged_in_user)
            session.pop('otp')  # Remove OTP after successful login
            session.pop('temp_user')
            session.pop('temp_user_id')
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid OTP. Try again.", "error")

    return render_template('verify_otp.html')

@app.route('/get_site_password', methods=['GET'])
def get_site_password():
    website = request.args.get('website')
    password = get_password(website)
    if password:
        return jsonify({"success": True, "username": password["username"], "password": password["password"]})
    else:
        return jsonify({"success": False})


# ✅ Dashboard Route
@app.route('/dashboard')
@login_required  
def dashboard():
    passwords = get_saved_passwords(current_user.id)
    return render_template('dashboard.html', user=current_user.username, passwords=passwords)

# ✅ Save Password Route
@app.route('/save_password', methods=['POST'])
@login_required
def save_password_route():
    website = request.form['website']
    username = request.form['username']
    password = request.form['password']

    try:
        save_password(current_user.id, website, username, password)
        flash("Password saved successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for('dashboard'))

# ✅ Edit Password Route
@app.route('/edit_password/<int:password_id>', methods=['GET', 'POST'])
@login_required
def edit_password(password_id):
    db = get_db()
    cursor = db.cursor()

    # Fetch existing password details
    cursor.execute("SELECT id, website, username, password FROM passwords WHERE id = ? AND user_id = ?", 
                   (password_id, current_user.id))
    password_entry = cursor.fetchone()

    if not password_entry:
        flash("Password entry not found.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        new_password = request.form['password']
        
        # Encrypt the new password
        encrypted_password = cipher.encrypt(new_password.encode()).decode()

        try:
            cursor.execute("UPDATE passwords SET password = ? WHERE id = ? AND user_id = ?", 
                           (encrypted_password, password_id, current_user.id))
            db.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f"Error updating password: {e}", "error")
            db.rollback()

    cursor.close()
    close_db(db)

    return render_template('edit_password.html', password=password_entry)


# ✅ Resend OTP Route
@app.route('/resend_otp')
def resend_otp():
    user_email = session.get('temp_user_email')
    if user_email:
        if send_otp_email(user_email):
            flash("OTP resent successfully.", "info")
        else:
            flash("Failed to resend OTP.", "error")
    else:
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for('login'))
    return redirect(url_for('verify_otp'))

@app.route('/autofill/<int:password_id>', methods=['POST'])
@login_required
def autofill(password_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT website, username, password FROM passwords WHERE id = ? AND user_id = ?", 
                   (password_id, current_user.id))
    password_entry = cursor.fetchone()
    cursor.close()
    close_db(db)

    if password_entry:
        decrypted_password = cipher.decrypt(password_entry[2].encode()).decode()
        return jsonify({
            'website': password_entry[0],
            'username': password_entry[1],
            'password': decrypted_password
        })
    else:
        return jsonify({'error': 'Password not found'}), 404

@app.route('/get-password')
def get_password():
    website = request.args.get('website')
    password = Password.query.filter_by(website=website).first()
    return password.password if password else "No password found"

# ✅ Delete Password Route
@app.route('/delete_password/<int:password_id>', methods=['POST'])
@login_required
def delete_password(password_id):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM passwords WHERE id = ? AND user_id = ?", (password_id, current_user.id))
        db.commit()
        flash("Password deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting password: {e}", "error")
        db.rollback()

    cursor.close()
    close_db(db)

    return redirect(url_for('dashboard'))

# ✅ Logout Route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))  

# Close DB Connection After Request
@app.teardown_appcontext
def close_db_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        close_db(db)

if __name__ == '__main__':
    app.run(debug=False)
