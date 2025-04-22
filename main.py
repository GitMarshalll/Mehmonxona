# hotel_booking_system/main.py
from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3

app = Flask(__name__)


def create_tables():
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            room_type TEXT,
            is_available INTEGER DEFAULT 1
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            room_id INTEGER,
            check_in TEXT,
            check_out TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return jsonify({'message': 'User registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists'}), 409
    finally:
        conn.close()


@app.route('/rooms', methods=['GET'])
def get_rooms():
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms WHERE is_available = 1")
    rooms = cursor.fetchall()
    conn.close()
    return jsonify({'available_rooms': rooms})


@app.route('/add_room', methods=['POST'])
def add_room():
    data = request.get_json()
    room_number = data['room_number']
    room_type = data['room_type']
    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO rooms (room_number, room_type) VALUES (?, ?)", (room_number, room_type))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Room added successfully'})


@app.route('/book', methods=['POST'])
def book_room():
    data = request.get_json()
    user_id = data['user_id']
    room_id = data['room_id']
    check_in = data['check_in']
    check_out = data['check_out']

    conn = sqlite3.connect('hotel.db')
    cursor = conn.cursor()

    # Check room availability
    cursor.execute('''SELECT * FROM bookings WHERE room_id=? 
                      AND (check_in BETWEEN ? AND ? OR check_out BETWEEN ? AND ?)''',
                   (room_id, check_in, check_out, check_in, check_out))
    if cursor.fetchone():
        return jsonify({'status': 'error', 'message': 'Room not available'}), 409

    # Book the room
    cursor.execute("""INSERT INTO bookings (user_id, room_id, check_in, check_out) 
                      VALUES (?, ?, ?, ?)""", (user_id, room_id, check_in, check_out))
    conn.commit()

    # Set room to unavailable
    cursor.execute("UPDATE rooms SET is_available = 0 WHERE id = ?", (room_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Room booked successfully'})


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
