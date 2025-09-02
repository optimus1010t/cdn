from flask import Flask, send_file
import os

app = Flask(__name__)
SERVER_FOLDER = "server_n_content"  # Folder to serve files from

os.makedirs(SERVER_FOLDER, exist_ok=True)

@app.route('/get/<filename>', methods=['GET'])
def get_file(filename):
    file_path = os.path.join(SERVER_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    return "File not found", 404

@app.route('/', methods=['GET'])
def health_check():
    return "Server is up"

if __name__ == '__main__':
    print("Starting basic file server on port 6000...")
    app.run(host='127.0.0.1', port=6007)
