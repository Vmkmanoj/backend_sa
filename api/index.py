from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, JWTManager
from flask_cors import CORS
import psycopg2.pool
from datetime import date

app = Flask(__name__)
CORS(app)

# Database connection pool
DATABASE_URL = "postgresql://neondb_owner:npg_vw3df1GEKtgD@ep-shy-tooth-a5qd2qrz-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"
conn_pool = psycopg2.pool.SimpleConnectionPool(1, 10, DATABASE_URL)

app.config["JWT_SECRET_KEY"] = "your_secret_key"
jwt = JWTManager(app)

def get_db_connection():
    return conn_pool.getconn()

@app.route("/")
def home():
    return jsonify({"message": "Hello, Flask on Vercel!"})

@app.route('/register', methods=['POST'])
def register():
    data = request.json

    if not all(k in data for k in ["name", "email", "phone", "password"]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = %s", (data["email"],))
    existing_user = cursor.fetchone()

    if existing_user:
        conn.close()
        return jsonify({"error": "User already exists"}), 400

    cursor.execute(
        "INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s) RETURNING id",
        (data["name"], data["email"], data["phone"], data["password"])
    )

    user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({
        "message": "User registered successfully!",
        "user": {
            "id": user_id,
            "name": data["name"],
            "email": data["email"],
            "phone": data["phone"]
        }
    }), 201
