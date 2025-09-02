from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import threading
import time
import socket
import uvicorn

app = FastAPI()

EDGE_SERVERS = [("127.0.0.1", 6000), ("127.0.0.1", 6001), ("127.0.0.1", 6002)]
EDGE_STATUS = {
    (ip, port): {"score": 0.0, "status": False, "last_ping": 0.0}
    for ip, port in EDGE_SERVERS
}
TIMEOUT = 1.0
PING_INTERVAL = 10.0

def compute_score(ip: str, port: int, client_ip: str) -> float:
    if ip == client_ip:
        return 10001
    return 10000 - port  # higher score = higher priority

def ping_edge(ip: str, port: int, timeout=TIMEOUT) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

@app.get("/resolve")
async def resolve(request: Request):
    client_ip = request.client.host
    alive_edges = []
    for (ip, port), meta in EDGE_STATUS.items():
        if meta["status"]:
            score = compute_score(ip, port, client_ip)
            alive_edges.append({"ip": ip, "port": port, "score": score})
    sorted_edges = sorted(alive_edges, key=lambda x: x["score"], reverse=True)
    return JSONResponse(content={"edges": sorted_edges})

def edge_monitor(interval=PING_INTERVAL):
    while True:
        for ip_port in EDGE_STATUS:
            ip, port = ip_port
            alive = ping_edge(ip, port)
            EDGE_STATUS[ip_port]["status"] = alive
            EDGE_STATUS[ip_port]["last_ping"] = time.time()
            # Placeholder score; final score depends on client in `/resolve`
            EDGE_STATUS[ip_port]["score"] = 0 if alive else -1
        time.sleep(interval)

# Start monitor thread
threading.Thread(target=edge_monitor, daemon=True).start()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=6004)
