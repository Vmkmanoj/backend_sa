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

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and user[1] == password: 
        return jsonify({"message": "Login successful!", "token": "fake-jwt-token", "id": user[0]}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/habits', methods=['POST'])
def add_habit():
    data = request.get_json()
    if not data or "name" not in data or "user_id" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    habit_name = data["name"]
    user_id = int(data["user_id"])  

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"message": "User not found"}), 404

    cursor.execute("INSERT INTO habit (name, user_id) VALUES (%s, %s) RETURNING id", (habit_name, user_id))
    new_habit_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({"id": new_habit_id, "name": habit_name, "user_id": user_id}), 201


@app.route('/habits/<int:user_id>', methods=['GET'])
def get_habits(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM habit WHERE user_id = %s", (user_id,))
        habits = cursor.fetchall()

        return jsonify([{"id": h[0], "name": h[1]} for h in habits])
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()  # Close cursor to avoid memory leaks
        if conn:
            conn_pool.putconn(conn)  # Return connection to pool instead of closing

@app.route('/habit-log', methods=['POST'])
def log_habit():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO habit_log (habit_id, date, completed) VALUES (%s, %s, %s)", 
                   (data["habit_id"], date.today(), data.get("completed", False)))
    cursor.execute("UPDATE habit SET streak = streak + 1 WHERE id = %s", (data["habit_id"],))
    conn.commit()
    conn.close()
    return jsonify({"message": "Habit logged!"})
@app.route("/habits/<int:habit_id>", methods=["PUT"])
def update_habit(habit_id):
    data = request.get_json()
    new_name = data.get("name")
    if not new_name:
        return jsonify({"error": "Name is required"}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE habit SET name = %s WHERE id = %s RETURNING id, name", (new_name, habit_id))
    updated_habit = cursor.fetchone()
    conn.commit()
    conn.close()
    if updated_habit:
        return jsonify({"message": "Habit updated", "habit": {"id": updated_habit[0], "name": updated_habit[1]}}), 200
    else:
        return jsonify({"error": "Habit not found"}), 404
@app.route("/habits/<int:habit_id>", methods=["DELETE"])
def delete_habit(habit_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit WHERE id = %s RETURNING id", (habit_id,))
    deleted_habit = cursor.fetchone()
    conn.commit()
    conn.close()
    if deleted_habit:
        return jsonify({"message": "Habit deleted"}), 200
    else:
        return jsonify({"error": "Habit not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)


