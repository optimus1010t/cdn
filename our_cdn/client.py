import requests
import os
import time
import threading

CLIENT_FOLDER = "client_content"
DNS_URL = "http://127.0.0.1:6004/resolve"  # DNS module address
UPDATE_INTERVAL = 600  # 10 minutes

# Thread-safe shared state
edge_servers = []
edge_lock = threading.Lock()

os.makedirs(CLIENT_FOLDER, exist_ok=True)

def update_edge_servers():
    global edge_servers
    while True:
        try:
            response = requests.get(DNS_URL)
            if response.status_code == 200:
                new_edges = [(entry["ip"], entry["port"]) for entry in response.json().get("edges", [])]
                with edge_lock:
                    edge_servers = new_edges
                print(f"[INFO] Edge server list updated: {new_edges}")
            else:
                print("[WARN] Failed to fetch edge server list.")
        except Exception as e:
            print(f"[ERROR] DNS request failed: {e}")
        time.sleep(UPDATE_INTERVAL)

def download_file(filename):
    with edge_lock:
        edges = list(edge_servers)  # read copy

    if not edges:
        print("No edge servers available.")
        return

    for ip, port in edges:
        try:
            edge_url = f"http://{ip}:{port}/get/{filename}"
            print(f"[INFO] Requesting from {edge_url}...")

            start = time.perf_counter()
            r = requests.get(edge_url)
            end = time.perf_counter()
            elapsed = end - start

            if r.status_code == 200:
                file_size_bytes = len(r.content)
                speed_kbps = (file_size_bytes / 1024) / elapsed if elapsed > 0 else 0

                save_path = os.path.join(CLIENT_FOLDER, filename)
                with open(save_path, 'wb') as f:
                    f.write(r.content)

                print(f"[SUCCESS] Downloaded from {ip}:{port} to {save_path}")
                print(f"Time taken: {elapsed:.4f} seconds")
                print(f"File size: {file_size_bytes / 1024:.2f} KB")
                print(f"Average speed: {speed_kbps:.2f} KB/sec")
                return
            else:
                print(f"[WARN] Edge {ip}:{port} responded with status {r.status_code} in {elapsed:.3f} seconds")
        except Exception as e:
            print(f"[ERROR] Failed to contact {ip}:{port} - {e}")

    print("[FAIL] Failed to fetch the file from all available edges.")

if __name__ == '__main__':
    # Start DNS updater thread
    updater_thread = threading.Thread(target=update_edge_servers, daemon=True)
    updater_thread.start()

    print("User Download Interface")
    while True:
        filename = input("Enter filename to fetch (or leave empty to wait): ").strip()
        if filename:
            download_file(filename)
