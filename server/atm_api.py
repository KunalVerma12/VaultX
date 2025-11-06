# atm_api.py
from flask import Flask, request, jsonify, send_file
from atm_core import ATM
from flask_cors import CORS
import json, os
from hashlib import sha256
import csv
from io import StringIO
import datetime
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

otp_storage = {}

app = Flask(__name__)
CORS(app)
atm = ATM("users.json")  # same backend data file

# 🏠 Health check
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "ATM Flask API is running"}), 200

# JSON file path
USER_FILE = os.path.join(os.path.dirname(__file__), "users.json")

with open(USER_FILE, 'r') as f:
    users = json.load(f)

def load_users():
    """Loads all user data from JSON file."""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_users(users):
    """Saves all user data safely to JSON file."""
    try:
        with open(USER_FILE, "w") as f:
            json.dump(users, f, indent=4)
        print("[INFO] Users saved successfully!")
    except Exception as e:
        print(f"[ERROR] Could not save users: {e}")

#otp generation
@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json()
    email = data['email']

    # Generate a 6-digit OTP
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = otp

    # Email config (use your Gmail)
    sender_email = "kunal153334@gmail.com"
    sender_password = "aumuiutwsbxowdnk"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "ATM Portal - Email Verification OTP"
    body = f"Your OTP for ATM signup is {otp}. It’s valid for 5 minutes."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return jsonify({"message": "OTP sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Verify OTP & Create Hashed Account
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data['email']
    entered_otp = data['otp']
    username = data['username']
    password = data['password']

    USER_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

    # Load existing users safely
    if not os.path.exists(USER_FILE) or os.stat(USER_FILE).st_size == 0:
        users = {}
    else:
        with open(USER_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)

    # OTP check
    if email not in otp_storage or otp_storage[email] != entered_otp:
        return jsonify({"error": "Invalid OTP"}), 400

    # ✅ Use the same SHA256 hashing as the rest of the program
    password_hash = sha256(password.encode()).hexdigest()

    users[username] = {
        "email": email,
        "password_hash": password_hash,
        "pin_hash": sha256("0000".encode()).hexdigest(),  # default PIN if not provided
        "balance": 0.0,
        "transactions": [],
        "rating": None,
        "logged_in": False
    }

    # ✅ Safely write the updated users.json
    try:
        with open(USER_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4)
        print(f"[INFO] User '{username}' saved successfully to {USER_FILE}")
    except Exception as e:
        print(f"[ERROR] Could not save user data: {e}")
        return jsonify({"error": f"File write error: {str(e)}"}), 500

    # Clean up OTP
    otp_storage.pop(email, None)

    # ✅ Refresh in-memory ATM state so new user becomes visible for login
    atm.users = users
    atm._save()

    print(f"[INFO] New verified user added: {username} ({email})")

    return jsonify({"message": "Email verified & signup successful!"}), 200






# 🧾 Create Account (fixed)
@app.route("/create", methods=["POST"])
def create_account():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    pin = data.get("pin") or ""

    if not username or not password or not pin:
        return jsonify({"success": False, "message": "All fields required"}), 400

    # Load existing users
    users = load_users()

    # Check if username already exists
    if username in users:
        return jsonify({"success": False, "message": "Username already exists"}), 400

    # Hash password and PIN
    password_hash = sha256(password.encode()).hexdigest()
    pin_hash = sha256(pin.encode()).hexdigest()

    # Create new user with full schema (matching Apple etc.)
    users[username] = {
        "password_hash": password_hash,
        "pin_hash": pin_hash,
        "balance": 0.0,
        "transactions": [],
        "rating": None,
        "logged_in": False
    }

    # Save back to JSON
    save_users(users)
    atm.users = users  # update in-memory object

    return jsonify({"success": True, "message": "Account created successfully!"}), 200


# 🔑 Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # 🔁 Always reload the latest users.json before attempting login
    try:
        with open(atm.data_file, "r", encoding="utf-8") as f:
            atm.users = json.load(f)
    except Exception as e:
        print(f"[ERROR] Could not reload users.json: {e}")
        return jsonify({"error": "Server data issue"}), 500

    success, message = atm.login(username, password)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400




# 💰 Deposit
@app.route("/deposit", methods=["POST"])
def deposit():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    data = request.get_json()
    amount = float(data.get("amount", 0))

    success, message = atm.deposit(amount)
    return jsonify({
        "success": success,
        "message": message,
        "balance": atm.get_balance()
    }), (200 if success else 400)


# 💸 Withdraw
@app.route("/withdraw", methods=["POST"])
def withdraw():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    data = request.get_json()
    amount = float(data.get("amount", 0))
    pin = str(data.get("pin", "")).strip()  # ✅ Get the PIN from frontend

    if not pin:
        return jsonify({"success": False, "message": "PIN is required"}), 400

    success, message = atm.withdraw(amount, pin)  # ✅ Pass pin argument

    return jsonify({
        "success": success,
        "message": message,
        "balance": atm.get_balance()
    }), (200 if success else 400)


# 🔁 Transfer
@app.route("/transfer", methods=["POST"])
def transfer():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    data = request.get_json()
    to_user = data.get("to_user")
    amount = float(data.get("amount", 0))
    pin = data.get("pin")  # ✅ added pin extraction

    success, message = atm.transfer(to_user, amount, pin)
    return jsonify({
        "success": success,
        "message": message,
        "balance": atm.get_balance()
    }), (200 if success else 400)


# 📊 Balance check
@app.route("/balance", methods=["GET"])
def balance():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    user = atm.users[atm.current_user]
    return jsonify({
        "success": True,
        "balance": user["balance"],
        "transactions": user.get("transactions", [])
    }), 200


# 🔐 Change PIN
@app.route("/change_pin", methods=["POST"])
def change_pin():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    data = request.get_json()
    old_pin = data.get("old_pin")
    new_pin = data.get("new_pin")

    success, message = atm.change_pin(old_pin, new_pin)
    return jsonify({"success": success, "message": message}), (200 if success else 400)

# 📊 Download Transaction History
@app.route("/download_csv", methods=["GET"])
def download_csv():
    if not atm.current_user:
        return jsonify({"success": False, "message": "No user logged in"}), 401

    user = atm.users.get(atm.current_user)
    transactions = user.get("transactions", [])

    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Type", "Amount", "Timestamp"])  # Header
    for t in transactions:
        writer.writerow([
            t.get("type", ""),
            t.get("amount", ""),
            t.get("timestamp", "")
        ])

    # Send CSV file to user
    from io import BytesIO
    mem = BytesIO()
    mem.write(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)
    filename = f"{atm.current_user}_transactions.csv"
    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

# ⭐ Save user rating
@app.route("/rate", methods=["POST"])
def rate_project():
    data = request.get_json() or {}
    rating = float(data.get("rating", 0))

    # ✅ Save rating if user still logged in
    if atm.current_user and atm.current_user in atm.users:
        atm.users[atm.current_user]["rating"] = rating
        atm._save()
        print(f"[INFO] {atm.current_user} rated the project {rating}⭐")
    else:
        # ✅ Handle anonymous rating after logout
        print(f"[INFO] Anonymous rating received: {rating}⭐")

    return jsonify({
        "success": True,
        "message": f"Thanks for rating us {rating} ⭐!"
    }), 200



if __name__ == "__main__":
    app.run(debug=True)

