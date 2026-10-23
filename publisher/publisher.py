import json, math, os, random, time
import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
TOPIC = "lab5/patient01/telemetry"

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.connect(HOST, 1883, 60)
c.loop_start()

while True:
    t = time.time()
    h = (t % 86400) / 86400  # ciclo diario simulado
    msg = {
        "device": "patient01",
        "temperature": round(36.8 + 0.4 * math.sin(2 * math.pi * h) + random.uniform(-0.1, 0.1), 2),
        "heart_rate": round(75 + 10 * math.sin(2 * math.pi * h) + random.uniform(-4, 4), 1),
        "spo2": round(min(100.0, 97 + random.uniform(-1.5, 1.5)), 1),
        "ts": int(t),
    }
    c.publish(TOPIC, json.dumps(msg), qos=1)
    print(msg, flush=True)
    time.sleep(10)
