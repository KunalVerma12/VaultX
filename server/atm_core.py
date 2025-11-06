# atm_core.py
import json
import os
import hashlib
from datetime import datetime

DATA_FILE = "users.json"
MAX_DEPOSIT = 50000.0


def sha256(text: str) -> str:
    """Return a secure SHA-256 hash of the given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ATM:
    def __init__(self, data_file=DATA_FILE):
        self.data_file = data_file
        self.users = self._load()
        self.current_user = None  # active username

    # ---------- Persistence ----------
    def _load(self):
        """Load users.json safely, handle corruption gracefully."""
        if not os.path.exists(self.data_file):
            return {}
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("⚠️ users.json corrupted or unreadable — resetting.")
            return {}

    def _save(self):
        """Write all user data back to users.json safely."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.users, f, indent=4)
        except IOError as e:
            raise RuntimeError(f"Failed to write data file: {e}")

    # ---------- Account management ----------
    def create_account(self, username: str, password: str, pin: str):
        """Create new account with password & pin hashes."""
        username = username.strip()
        if not username or not password or not pin:
            return False, "All fields are required."
        if username in self.users:
            return False, "Username already exists."

        self.users[username] = {
            "password_hash": sha256(password),
            "pin_hash": sha256(str(pin)),
            "balance": 0.0,
            "transactions": [],
            "rating": None,
            "logged_in": False,
        }
        self._save()
        return True, f"Account '{username}' created."

    def login(self, username: str, password: str):
        username = username.strip()
        if username not in self.users:
            return False, "No such user."

        user = self.users[username]

        # ✅ Hash comparison — MUST use password_hash
        if user.get("password_hash") != sha256(password):
            return False, "Incorrect password."

        # Logout everyone else
        for u in self.users.values():
            u["logged_in"] = False

        user["logged_in"] = True
        self.current_user = username
        self._save()

        return True, f"Welcome back, {username}!"


    def logout(self):
        """Safely log out current user."""
        if self.current_user:
            self.users[self.current_user]["logged_in"] = False
            self._save()
        self.current_user = None

    # ---------- Utilities ----------
    def _add_transaction(self, username, ttype, amount):
        """Record transaction with timestamp."""
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        entry = {"type": ttype, "amount": amount, "timestamp": ts}
        self.users[username]["transactions"].append(entry)
        self._save()

    def get_balance(self, username=None):
        username = username or self.current_user
        if not username:
            return 0.0
        return float(self.users[username]["balance"])

    def get_transactions(self, username=None):
        username = username or self.current_user
        if not username:
            return []
        return list(self.users[username]["transactions"])

    # ---------- Money operations ----------
    def deposit(self, amount: float):
        if self.current_user is None:
            return False, "Login required."
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, "Invalid amount."
        if amount <= 0:
            return False, "Amount must be positive."
        if amount > MAX_DEPOSIT:
            return False, f"Deposit exceeds max of {MAX_DEPOSIT}."

        self.users[self.current_user]["balance"] += amount
        self._add_transaction(self.current_user, "Deposit", amount)
        return True, f"Deposited ₹{amount:.2f}. New balance: ₹{self.get_balance():.2f}"

    def withdraw(self, amount: float, pin: str):
        if self.current_user is None:
            return False, "Login required."
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, "Invalid amount."
        if amount <= 0:
            return False, "Amount must be positive."
        if sha256(pin) != self.users[self.current_user]["pin_hash"]:
            return False, "Incorrect PIN."
        if amount > self.users[self.current_user]["balance"]:
            return False, "Insufficient funds."

        self.users[self.current_user]["balance"] -= amount
        self._add_transaction(self.current_user, "Withdraw", amount)
        return True, f"Withdrew ₹{amount:.2f}. New balance: ₹{self.get_balance():.2f}"

    def transfer(self, to_username: str, amount: float, pin: str):
        if self.current_user is None:
            return False, "Login required."
        to_username = to_username.strip()
        if to_username not in self.users:
            return False, "Recipient not found."
        if to_username == self.current_user:
            return False, "Cannot transfer to yourself."

        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return False, "Invalid amount."
        if amount <= 0:
            return False, "Amount must be positive."
        if sha256(pin) != self.users[self.current_user]["pin_hash"]:
            return False, "Incorrect PIN."
        if amount > self.users[self.current_user]["balance"]:
            return False, "Insufficient funds."

        # Transfer between users
        self.users[self.current_user]["balance"] -= amount
        self.users[to_username]["balance"] += amount
        self._add_transaction(self.current_user, f"Transfer to {to_username}", -amount)
        self._add_transaction(to_username, f"Transfer from {self.current_user}", amount)
        return True, f"Transferred ₹{amount:.2f} to {to_username}. New balance: ₹{self.get_balance():.2f}"

    # ---------- PIN & Password ----------
    def change_pin(self, old_pin, new_pin):
        if not self.current_user:
            return False, "No user logged in."
        user_data = self.users[self.current_user]

        if sha256(str(old_pin)) != user_data["pin_hash"]:
            return False, "Incorrect old PIN."

        user_data["pin_hash"] = sha256(str(new_pin))
        self._save()
        return True, "PIN changed successfully."

    def change_password(self, current_password: str, new_password: str):
        if self.current_user is None:
            return False, "Login required."
        if sha256(current_password) != self.users[self.current_user]["password_hash"]:
            return False, "Incorrect current password."
        if not new_password:
            return False, "New password required."

        self.users[self.current_user]["password_hash"] = sha256(new_password)
        self._save()
        return True, "Password changed successfully."

    # ---------- Ratings ----------
    def submit_rating(self, rating: int):
        if self.current_user is None:
            return False, "Login required."
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return False, "Invalid rating."
        if rating < 1 or rating > 5:
            return False, "Rating must be 1–5."
        self.users[self.current_user]["rating"] = rating
        self._save()
        return True, f"Thanks for rating {rating} star(s)!"

    # ---------- Export ----------
    def export_transactions_csv(self, username=None, csv_path=None):
        """Save user's transactions to a CSV file."""
        import csv

        username = username or self.current_user
        if username is None:
            return False, "Login required."

        transactions = self.get_transactions(username)
        if not csv_path:
            csv_path = f"transactions_{username}.csv"

        try:
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["type", "amount", "timestamp"])
                for t in transactions:
                    writer.writerow([t.get("type"), t.get("amount"), t.get("timestamp")])
            return True, csv_path
        except IOError as e:
            return False, f"Failed to write CSV: {e}"
