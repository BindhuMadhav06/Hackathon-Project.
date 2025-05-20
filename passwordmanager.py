import os  
from cryptography.fernet import Fernet
from database import get_db, close_db

# Load Encryption Key
def load_encryption_key():
    key_path = "key.env"
    
    if os.path.exists(key_path):
        with open(key_path, "rb") as file:
            key = file.read()
        try:
            Fernet(key)  # Validate key format
            return key
        except ValueError:
            print("Invalid key format, generating a new key...")
            os.remove(key_path)  
            key = Fernet.generate_key()  
            with open(key_path, "wb") as file:
                file.write(key)
            return key
    else:
        key = Fernet.generate_key()
        with open(key_path, "wb") as file:
            file.write(key)
        return key

fernet_key = load_encryption_key()
cipher = Fernet(fernet_key)  

# ✅ Save Password Function
def save_password(user_id, website, username, password):
    db = get_db()
    cursor = db.cursor()
    
    try:
        encrypted_password = cipher.encrypt(password.encode()).decode()
        cursor.execute("INSERT INTO passwords (user_id, website, username, password) VALUES (?, ?, ?, ?)", 
                       (user_id, website, username, encrypted_password))
        db.commit()
    except Exception as e:
        print(f"Error saving password: {e}")
        raise
    finally:
        cursor.close()
        close_db(db)

# ✅ Get Saved Passwords Function (with debugging)
def get_saved_passwords(user_id):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT id, website, username, password FROM passwords WHERE user_id = ?", (user_id,))
        passwords = cursor.fetchall()

        decrypted_passwords = []
        for password in passwords:
            print("🔒 Encrypted Password in DB:", password[3])  # Debugging Step
            
            try:
                decrypted_password = cipher.decrypt(password[3].encode()).decode()
            except Exception as e:
                print("❌ Decryption Failed for:", password[3])
                raise e  # Show actual error
            
            decrypted_passwords.append({
                'id': password[0],
                'website': password[1],
                'username': password[2],
                'password': decrypted_password
            })
        return decrypted_passwords

    except Exception as e:
        print(f"Error fetching saved passwords: {e}")
        raise
    finally:
        cursor.close()
        close_db(db)  

# ✅ Update Password Function
def update_password(password_id, new_password, user_id):
    db = get_db()
    cursor = db.cursor()

    try:
        encrypted_password = cipher.encrypt(new_password.encode()).decode()
        cursor.execute("UPDATE passwords SET password = ? WHERE id = ? AND user_id = ?", 
                       (encrypted_password, password_id, user_id))
        db.commit()
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()
        close_db(db)

# ✅ Delete Password Function
def delete_password_entry(password_id, user_id):
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("DELETE FROM passwords WHERE id = ? AND user_id = ?", (password_id, user_id))
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting password: {e}")
        db.rollback()
        return False
    finally:
        cursor.close()
        close_db(db)
