# VaultX
A full-stack ATM simulator built using Flask, React, Node.js, and Python. VaultX provides secure transactions and account management — all wrapped in a sleek modern UI
# 🏗️ Project Structure
```markdown
ATM-Chatbot/
│
├── atm_api.py          # Backend API built with Flask
├── atm_core.py         # Core ATM functionalities (deposit, withdraw, etc.)
├── atm_test.py         # Backend testing file
├── users.json          # Database simulation file for storing user data
│
├── client/             # Frontend built with React
│   ├── src/
│   ├── public/
│   └── package.json
│
└── README.md
```
# ⚙️ Features
🔐 **User Authentication** – Secure login & signup system using PIN and hashed passwords.
- 💸 **Deposit, Withdraw, and Balance Inquiry** – Fully functional transaction handling.
- 🔄 **Transfer System** – Allows fund transfer between users.
- 🗂️ **CSV Support** – Export and import user data in `.csv` format for easy backup and analytics.
- 🧠 **JSON Data Storage** – Persistent user records maintained using a `users.json` file.
- 🧩 **Flask API Backend** – Manages server-side logic, data, and routing.
- ⚛️ **React Frontend** – Interactive UI built with modern components.
- 🎨 **Responsive Design** – Styled with CSS for a clean, intuitive layout.
- 🔑 **Hashing for Security** – PINs and passwords stored securely with hashing algorithms.
- ⭐ **Fun Rating System** – Users can rate their ATM experience for interactive engagement.

# 🚀 Setup Instructions
#Navigate to backend folder  
cd server

#Install dependencies  
pip install flask flask-cors

#Run backend  
python atm_api.py
Backend will start at http://127.0.0.1:5000/
# 💻 Frontend Setup (React)
#Navigate to client folder  
cd client

#Install dependencies  
npm install

#Start frontend  
npm start
Frontend runs on http://localhost:3000/ and connects to Flask backend.
# 🧠 Technologies Used
Frontend: React, HTML, CSS, JavaScript

Backend: Flask (Python)

Data Storage: JSON file

Version Control: Git & GitHub
 # 🧑‍💻 Future Enhancements
 🧩 Add database integration (MongoDB or MySQL)

🔒 JWT-based authentication

🤖 Smarter chatbot using NLP

📊 Admin dashboard with user analytics
# 🤝 Contributing
Pull requests are welcome!
If you’d like to contribute, fork the repo and create a new branch for your feature or fix.
# 👩‍💻 Author
Developed by [Kunal V](https://github.com/KunalVerma12)

A full-stack developer passionate about blending technology, creativity, and security.
# 🪪 License
This project is licensed under the MIT License.
