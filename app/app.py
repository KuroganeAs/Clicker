from flask import Flask, render_template, jsonify, Response
from prometheus_client import generate_latest, Counter, Gauge, Histogram
import time
import math
import psutil

app = Flask(__name__)

# --- PROMETHEUS METRICS ---
# 1. TRAFFIC: Menghitung total request masuk
REQUEST_COUNT = Counter('game_requests_total', 'Total Requests Received')

# 2. LATENCY: Mengukur durasi proses request
LATENCY = Histogram('game_latency_seconds', 'Time spent processing a click')

# 3. RESOURCE: CPU & Memory
SCORE = Gauge('game_score', 'Current Score')
MEMORY_GAUGE = Gauge('game_memory_usage_bytes', 'Memory consumed')

memory_leak_storage = []
current_score = 0

@app.route('/')
def index():
    return render_template('game.html')

@app.route('/click')
def click():
    global current_score
    start_time = time.time()  # MENCATAT WAKTU MULAI
    
    # 1. Record Traffic
    REQUEST_COUNT.inc()
    
    # 2. Update Score
    current_score += 1
    SCORE.set(current_score)

    # 3. BURN CPU (Membuat Latency Buatan)
    # Loop ini membuat server 'berpikir' keras, menambah durasi loading
    x = 0
    for i in range(200000): 
        x += math.sqrt(i) * math.tan(i)

    # 4. BURN MEMORY
    memory_leak_storage.append('A' * 1024 * 1024) # 1MB junk
    current_mem_usage = len(memory_leak_storage) * 1024 * 1024
    MEMORY_GAUGE.set(current_mem_usage)

    # 5. HITUNG LATENCY (Waktu Selesai - Waktu Mulai)
    duration = time.time() - start_time
    LATENCY.observe(duration)  # Kirim ke Prometheus

    # 6. Cek Status System
    cpu_percent = psutil.cpu_percent(interval=None)
    mem_percent = psutil.virtual_memory().percent

    return jsonify({
        "score": current_score,
        "cpu": cpu_percent,
        "memory": mem_percent,
        "latency": round(duration, 4), # Kirim Latency ke Game UI (4 angka desimal)
        "traffic": current_score       # Total Traffic saat ini
    })

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

