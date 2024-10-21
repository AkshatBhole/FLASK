# app.py
import sqlite3
from flask import Flask, request, jsonify
import speech_recognition as sr
import re
import razorpay
import cv2

# Razorpay API credentials (replace with actual credentials)
RAZORPAY_API_KEY = "your_razorpay_api_key"
RAZORPAY_API_SECRET = "your_razorpay_secret_key"

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET))

app = Flask(__name__)

# Database functions
def create_transactions_table():
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            amount INTEGER NOT NULL,
            recipient TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_transaction(amount, recipient, status):
    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (amount, recipient, status) VALUES (?, ?, ?)
    ''', (amount, recipient, status))
    conn.commit()
    conn.close()

# Voice command processing functions
def recognize_voice_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized command: {command}")
            return command
        except sr.UnknownValueError:
            print("Could not understand the command.")
        except sr.RequestError:
            print("Speech recognition service is unavailable.")
    return None

def parse_voice_command(command):
    # Extract amount, recipient, and PIN from the command
    amount_match = re.search(r'transfer\s+(\d+)\s+rs', command)
    recipient_match = re.search(r'to\s+(\w+)', command)
    pin_match = re.search(r'pin\s+(\d{4})', command)
    
    if amount_match and recipient_match and pin_match:
        amount = int(amount_match.group(1))
        recipient = recipient_match.group(1)
        pin = pin_match.group(1)
        return amount, recipient, pin
    else:
        print("Failed to extract transaction details.")
        return None, None, None

# PIN verification function
def verify_pin(input_pin, stored_pin="1234"):
    # In a real application, the stored PIN should be securely hashed and verified
    if input_pin == stored_pin:
        print("PIN verification successful.")
        return True
    else:
        print("Invalid PIN.")
        return False

# Payment processing functions
def create_payment_order(amount, recipient_upi):
    # Convert amount to paise
    amount_in_paise = amount * 100

    payment_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1, # Auto capture payment
        "notes": {
            "recipient": recipient_upi
        }
    }

    try:
        order = client.order.create(payment_data)
        print(f"Payment order created: {order}")
        return order
    except Exception as e:
        print(f"Failed to create payment order: {e}")
        return None

# Face detection function
def detect_face(image_path):
    # Load the pre-trained face detection model
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Read the image
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        print("Face detected!")
        return True
    else:
        print("No face detected.")
        return False

# API route
@app.route('/process_voice_command', methods=['POST'])
def process_voice_command():
    voice_command = recognize_voice_command()
    if not voice_command:
        return jsonify({"error": "Could not recognize voice command"}), 400

    amount, recipient, pin = parse_voice_command(voice_command)
    if not amount or not recipient or not pin:
        return jsonify({"error": "Invalid command format"}), 400

    # Verify the PIN
    if not verify_pin(pin):
        return jsonify({"error": "PIN verification failed"}), 403

    # Security check: Face detection
    face_detected = detect_face('user_image.jpg')  # Pass the user image path
    if not face_detected:
        return jsonify({"error": "Face detection failed"}), 403

    # Create payment order
    order = create_payment_order(amount, recipient)
    if not order:
        return jsonify({"error": "Payment order creation failed"}), 500

    # Log the transaction
    log_transaction(amount, recipient, "Created")

    return jsonify({"message": "Payment order created", "order_id": order['id']}), 200

# Run the app
if __name__ == '__main__':
    create_transactions_table()  # Ensure the table exists before starting the app
    app.run(debug=True)
