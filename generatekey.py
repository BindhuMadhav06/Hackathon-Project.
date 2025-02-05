from cryptography.fernet import Fernet
import os

# Generate a key and save it to a file
def generate_key():
    key = Fernet.generate_key()
    with open("key.env", "wb") as file:
        file.write(key)
    print(f"🔑 New Key Generated: {key}")  # Debugging purpose

# Run the key generation
if __name__ == "__main__":
    if not os.path.exists("key.env"):
        generate_key()
        print("✅ Key generated successfully!")
    else:
        print("⚠️ Key already exists. Delete `key.env` if you want to generate a new one.")
