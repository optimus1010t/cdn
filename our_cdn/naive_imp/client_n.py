import requests
import os
import time

CLIENT_FOLDER = "client_n_content"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 6007

os.makedirs(CLIENT_FOLDER, exist_ok=True)

def download_file(filename):
    try:
        server_url = f"http://{SERVER_IP}:{SERVER_PORT}/get/{filename}"

        start = time.perf_counter()
        r = requests.get(server_url)
        end = time.perf_counter()

        duration = end - start
        if r.status_code == 200:
            file_size_bytes = len(r.content)
            speed_kbps = (file_size_bytes / 1024) / duration if duration > 0 else 0

            save_path = os.path.join(CLIENT_FOLDER, filename)
            with open(save_path, 'wb') as f:
                f.write(r.content)

            print(f"Downloaded from {SERVER_IP}:{SERVER_PORT} to {save_path}")
            print(f"Time taken to download: {duration:.4f} seconds")
            print(f"File size: {file_size_bytes / 1024:.2f} KB")
            print(f"Average speed: {speed_kbps:.2f} KB/sec")
        else:
            print(f"Server responded with status {r.status_code}")
    except Exception as e:
        print(f"Failed to contact {SERVER_IP}:{SERVER_PORT} - {e}")

if __name__ == '__main__':
    print("Simple File Fetch Client")
    filename = input("Enter filename to fetch: ")
    download_file(filename)
