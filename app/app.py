from flask import Flask, render_template, jsonify, Response
from prometheus_client import generate_latest, Counter, Gauge, Histogram
import time
import math
import psutil  # To read system CPU/RAM

app = Flask(__name__)

# --- PROMETHEUS METRICS ---
SCORE = Gauge('game_score', 'Total Clicks/Users')
REQUEST_COUNT = Counter('game_requests_total', 'Total Requests')
LATENCY = Histogram('game_latency_seconds', 'Time spent processing a click')
MEMORY_GAUGE = Gauge('game_memory_usage_bytes', 'Memory consumed by the app')

# Global variables for simulation
memory_leak_storage = []
current_score = 0

@app.route('/')
def index():
    return render_template('game.html')

@app.route('/click')
def click():
    global current_score
    start_time = time.time()
    
    # 1. Update Score
    current_score += 1
    SCORE.set(current_score)
    REQUEST_COUNT.inc()

    # 2. BURN CPU (The Heavy Math)
    # We do a loop to force the CPU to work hard for this specific request
    x = 0
    for i in range(150000): 
        x += math.sqrt(i) * math.tan(i)

    # 3. BURN MEMORY (The Leak)
    # We append 1MB of junk data to RAM every click and NEVER delete it
    junk_data = 'A' * 1024 * 1024 # ~1MB string
    memory_leak_storage.append(junk_data)
    
    # Update Prometheus Metric for Memory
    current_mem_usage = len(memory_leak_storage) * 1024 * 1024
    MEMORY_GAUGE.set(current_mem_usage)

    # 4. Measure Latency
    duration = time.time() - start_time
    LATENCY.observe(duration)

    # 5. Check System Health (For the Frontend Warning)
    # This reads the actual Container CPU/RAM usage
    cpu_percent = psutil.cpu_percent(interval=None)
    mem_percent = psutil.virtual_memory().percent

    return jsonify({
        "score": current_score,
        "cpu": cpu_percent,
        "memory": mem_percent,
        "latency": duration
    })

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)