from flask import Flask, send_file
import requests
import os
import time
import shutil

app = Flask(__name__)
EDGE_CACHE = "edge_cache"
PRIORITY_OS = ["http://127.0.0.1:5000", "http://127.0.0.1:5001", "http://127.0.0.1:5002"]
MAX_CACHE_SIZE = 200 * 1024  # 200KB
cache_metadata = {}  # filename -> last_accessed_timestamp

# Clean and recreate cache folder
if os.path.exists(EDGE_CACHE):
    shutil.rmtree(EDGE_CACHE)
os.makedirs(EDGE_CACHE, exist_ok=True)

def get_cache_size():
    return sum(os.path.getsize(os.path.join(EDGE_CACHE, f)) for f in os.listdir(EDGE_CACHE))

def evict_files(required_space):
    global cache_metadata
    sorted_files = sorted(cache_metadata.items(), key=lambda item: item[1])
    freed_space = 0
    for filename, _ in sorted_files:
        file_path = os.path.join(EDGE_CACHE, filename)
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            os.remove(file_path)
            freed_space += file_size
            del cache_metadata[filename]
            print(f"[EVICT] Removed {filename} ({file_size} bytes)")
            if freed_space >= required_space:
                break

@app.route('/get/<filename>', methods=['GET'])
def get_file(filename):
    cache_path = os.path.join(EDGE_CACHE, filename)
    if os.path.exists(cache_path):
        cache_metadata[filename] = time.time()
        return send_file(cache_path)
    for origin in PRIORITY_OS:
        url = f"{origin}/fetch/{filename}"
        r = requests.get(url)
        if r.status_code == 200:
            file_size = len(r.content)
            current_cache = get_cache_size()
            if file_size + current_cache > MAX_CACHE_SIZE:
                evict_files(file_size + current_cache - MAX_CACHE_SIZE)
            with open(cache_path, 'wb') as f:
                f.write(r.content)
            cache_metadata[filename] = time.time()
            print(f"[CACHE] Stored {filename} ({file_size} bytes)")
            return send_file(cache_path)
    return "File not found", 404

if __name__ == '__main__':
    print("[INIT] Cleared edge_cache/ on startup")
    app.run(host='127.0.0.1', port=6000)
