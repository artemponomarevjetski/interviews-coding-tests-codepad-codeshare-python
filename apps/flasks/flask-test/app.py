from flask import Flask, send_from_directory
import os
import socket
import socket
from datetime import datetime
import time

app = Flask(__name__)

# Function to check if a port is available
def find_free_port(starting_port=5000):
    port = starting_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))
            if result != 0:  # Port is available
                return port
            port += 1  # Increment port number if the port is already in use

@app.route('/')
def display_image():
    image_path = os.path.join(os.getcwd(), 'test-snapshot', 'snap_latest.png')
    print(f"Current working directory: {os.getcwd()}")  # Log current working directory
    print(f"Looking for image at: {image_path}")  # Log image path
    if os.path.exists(image_path):
        return send_from_directory(os.path.dirname(image_path), 'snap_latest.png')
    else:
        return "Image not found", 404

if __name__ == "__main__":
    # Find an available port starting from 5000
    available_port = find_free_port(5000)
    
    # Print the available port and run the Flask app
    print(f"Flask app running on: http://127.0.0.1:{available_port}")
    app.run(host="0.0.0.0", port=available_port, debug=True)

