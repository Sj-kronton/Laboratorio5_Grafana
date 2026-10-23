import json, os, time
import paho.mqtt.client as mqtt

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.connect(os.getenv("MQTT_HOST", "localhost"), 1883, 60)
c.loop_start()
for _ in range(6):  # ~1 min de valores anormales
    c.publish("lab5/patient01/telemetry", json.dumps({
        "device": "patient01", "temperature": 39.5,
        "heart_rate": 135.0, "spo2": 90.0, "ts": int(time.time())}), qos=1)
    time.sleep(10)
c.loop_stop()
c.disconnect()
