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

@app.route('/about')
def about():
    return 'About'
