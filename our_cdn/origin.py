from flask import Flask, request, send_from_directory
import os
import time
import threading
import requests
import argparse


app = Flask(__name__)
lock = threading.Lock()  # Lock for thread safety
IS_REPLICATING = 0  # Flag to indicate if the server is replicating files
UPLOAD_FOLDER = "origin_content"
FILE_LIST = "file_list.txt"
NEW_FILES_LIST = ["new_files.txt","new_files_while_replicating.txt"]
UPDATE_TIME = 30  # Time in seconds to wait before replicating files
MY_SERVER_URL = "http://127.0.0.1:5000/replicate"  # default URL of this server for sending files, will be changed in __main__
ORIGIN_SERVERS = ["http://127.0.0.1:5000/replicate","http://127.0.0.1:5001/replicate", "http://127.0.0.1:5002/replicate"]  # Add other origin server URLs here
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure the file list and new files list exist
if not os.path.exists(FILE_LIST):
    open(FILE_LIST, 'w').close()
if not os.path.exists(NEW_FILES_LIST[0]):
    open(NEW_FILES_LIST[0], 'w').close()
if not os.path.exists(NEW_FILES_LIST[1]):
    open(NEW_FILES_LIST[1], 'w').close()

@app.route('/upload', methods=['POST'])
def upload():
    global IS_REPLICATING
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Add the file to the appropriate new files list
    with lock:
        if IS_REPLICATING == 0:
            with open(NEW_FILES_LIST[0], 'a') as f:
                f.write(f"{file.filename}\n")
        else:
            with open(NEW_FILES_LIST[1], 'a') as f:
                f.write(f"{file.filename}\n")

    return 'Upload successful'

@app.route('/replicate', methods=['POST'])
def replicate():
    file = request.files['file']
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Update the file list
    with open(FILE_LIST, 'r+') as f:
        files = f.read().splitlines()
        if file.filename not in files:
            files.append(file.filename)
            files.sort()  # Sort alphabetically
            f.seek(0)
            f.write('\n'.join(files) + '\n')
            f.truncate()

    return 'Replication successful'

@app.route('/fetch/<filename>', methods=['GET'])
def fetch(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    global IS_REPLICATING
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        return 'File not found', 404
    filename = "DELETE_" + filename
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    open(file_path, 'w').close()  # Create an empty file to indicate deletion

    # Update the appropriate new files list
    with lock:
        if IS_REPLICATING == 0:
            with open(NEW_FILES_LIST[0], 'a') as f:
                f.write(f"{filename}\n")
        else:
            with open(NEW_FILES_LIST[1], 'a') as f:
                f.write(f"{filename}\n")

    return 'File deleted'

@app.route('/recover', methods=['POST'])
def recover():
    # Receive the file list from the recovering server
    received_file_list = request.json.get('file_list', [])
    sender_url = request.json.get('sender_url', '')

    # Read the local file list
    with open(FILE_LIST, 'r') as f:
        local_file_list = f.read().splitlines()

    # Find files that the recovering server is missing
    missing_files = [file for file in local_file_list if file not in received_file_list]

    # Send the missing files back to the recovering server
    for filename in missing_files:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as file:
                    requests.post(f"{sender_url}/replicate", files={'file': file})
                    print(f"Sent missing file {filename} to {sender_url}")
            except Exception as e:
                print(f"Failed to send {filename} to {sender_url}: {e}")

    return 'Recovery process completed', 200

def send_recent_files():
    global IS_REPLICATING
    while True:
        with lock:
            IS_REPLICATING = 1  # Set the flag to indicate replication is in progress

        print("Starting replication...")

        # Read the new files list
        new_files_list = NEW_FILES_LIST[0]
        with open(new_files_list, 'r') as f:
            recent_files = f.read().splitlines()

        # time.sleep(UPDATE_TIME)  # Wait for UPDATE_TIME seconds before sending files, just for checking functionality

        # Send recent files to other origin servers
        for filename in recent_files:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                for server_url in ORIGIN_SERVERS:
                    if server_url == MY_SERVER_URL:
                        continue
                    try:
                        with open(file_path, 'rb') as file:
                            requests.post(server_url, files={'file': file})
                    except Exception as e:
                        print(f"Failed to send {filename} to {server_url}: {e}")

        # Add these file names to files.txt
        with open(FILE_LIST, 'r+') as f:
            files = f.read().splitlines()
            for filename in recent_files:
                if filename not in files:
                    files.append(filename)
            files.sort()
            f.seek(0)
            f.write('\n'.join(files) + '\n')
            f.truncate()

        # Clear the new files list after processing
        open(new_files_list, 'w').close()

        with lock:
            with open(NEW_FILES_LIST[1], 'r') as temp_file, open(new_files_list, 'w') as new_file:
                new_file.write(temp_file.read())

            open(NEW_FILES_LIST[1], 'w').close()  # Clear the new files list after processing

            # Reset the IS_REPLICATING flag
            IS_REPLICATING = 0

        print("Replication completed, waiting for next cycle...")


        time.sleep(UPDATE_TIME)  # Wait for UPDATE_TIME seconds before the next iteration

def cleanup_task():
    while True:
        with lock:
            # Read the file list
            with open(FILE_LIST, 'r+') as f:
                files = f.read().splitlines()

            # Find and process matching DELETE_filename and filename
            to_remove = []
            for filename in files:
                if filename.startswith("DELETE_"):
                    original_filename = filename.replace("DELETE_", "", 1)
                    if original_filename in files:
                        # Delete the file from the upload folder
                        file_path = os.path.join(UPLOAD_FOLDER, original_filename)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Deleted file: {original_filename}")

                        # Remove the DELETE_filename from the file list
                        delete_file_path = os.path.join(UPLOAD_FOLDER, filename)
                        if os.path.exists(delete_file_path):
                            os.remove(delete_file_path)
                            print(f"Deleted file: {filename}")

                        # Mark both entries for removal
                        to_remove.append(filename)
                        to_remove.append(original_filename)

            # Remove the matching entries from the file list
            files = [file for file in files if file not in to_remove]

            # Write the updated file list back to FILE_LIST
            with open(FILE_LIST, 'w') as f:
                f.write('\n'.join(files) + '\n')

        # Wait for a specified interval before running again
        time.sleep(UPDATE_TIME)

def recovery_task():

    for server_url in ORIGIN_SERVERS:
        if server_url != MY_SERVER_URL:  # Skip sending to itself
            try:
                with open(FILE_LIST, 'r') as f:
                    local_file_list = f.read().splitlines()
                recovery_url = server_url.replace('/replicate', '/recover')
                requests.post(recovery_url, json={
                    'file_list': local_file_list,
                    'sender_url': MY_SERVER_URL.replace('/replicate', '')
                })
                print(f"Sent file list to {recovery_url} for recovery")
            except Exception as e:
                print(f"Failed to send file list to {recovery_url}: {e}")

# Start the background thread for sending recent files
threading.Thread(target=send_recent_files, daemon=True).start()

# Start the background thread for the cleanup task
threading.Thread(target=cleanup_task, daemon=True).start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start the origin server.")
    parser.add_argument('--port', type=int, default=5000, help="Port to run the server on (default: 5000)")
    args = parser.parse_args()

    MY_SERVER_URL = f"http://127.0.0.1:{args.port}/replicate"  # Update the server URL with the specified port
    print(f"Starting origin server on port {args.port}...")


    # Start the Flask app in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=args.port), daemon=True)
    flask_thread.start()

    # Wait for the Flask server to start
    time.sleep(2)  # Give the server some time to start

    # Start the recovery task
    recovery_task()

    # Keep the main thread alive
    flask_thread.join()