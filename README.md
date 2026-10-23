# Laboratorio 5: Visualización + reglas / alertas

IoT + Cloud + Sistemas Distribuidos, Universidad Autónoma de Bucaramanga.
Escenario: sensor de monitoreo de paciente (`patient01`) con tres variables:
temperatura (°C), frecuencia cardíaca (bpm) y SpO2 (%).

## Arquitectura

publisher (Python) -> Mosquitto (MQTT) -> Telegraf -> InfluxDB 2.7 <- Grafana OSS 11.2


| Servicio | Imagen | Función |
|---|---|---|
| publisher | python:3.12-slim + paho-mqtt | Publica las 3 variables cada 10 s por MQTT |
| mosquitto | eclipse-mosquitto:2 | Broker MQTT |
| telegraf | telegraf:1.30 | Suscriptor MQTT que escribe en InfluxDB |
| influxdb | influxdb:2.7 | Base de datos de series de tiempo (TSDB) |
| grafana | grafana/grafana-oss:11.2.0 | Dashboard y alertas; solo lee InfluxDB |

Protocolo elegido: **MQTT**. Grafana no participa en la ingesta.

## Contrato de datos

- Topic: `lab5/patient01/telemetry`
- Payload JSON: `device`, `temperature`, `heart_rate`, `spo2`, `ts` (unix, segundos)
- InfluxDB: org `uab`, bucket `telemetria`, measurement `telemetry`, tag `device`
- Campos (float): `temperature`, `heart_rate`, `spo2`
- Telegraf añade además los tags `host` y `topic`; las consultas de Grafana los descartan con `drop`.

## Requisitos

- Una VM (probado en Debian 12 en Azure) con Docker Engine y el plugin Docker Compose v2.
- Instalación de Docker desde el repositorio oficial de Docker. En Debian no existe el paquete `docker-compose-v2`.

## Cómo levantar el stack

1. Clonar el repositorio y entrar en la carpeta.
2. Crear el archivo de variables a partir de la plantilla:
   ```bash
   cp .env.example .env
   openssl rand -hex 24      # usar el resultado como INFLUX_TOKEN
   nano .env                 # completar todos los valores
   ```
   Variables: `INFLUX_USER`, `INFLUX_PASSWORD`, `INFLUX_ORG`, `INFLUX_BUCKET`,
   `INFLUX_TOKEN`, `GF_ADMIN_PASSWORD`, `WEBHOOK_URL` (URL del contact point de la alerta).
   El archivo `.env` real no se versiona.
3. Levantar:
   ```bash
   docker compose up -d --build
   docker compose ps
   ```

## Verificación

```bash
# Mensajes en el broker
docker compose exec mosquitto mosquitto_sub -t 'lab5/#' -C 2

# Puntos guardados en InfluxDB
set -a; source .env; set +a
docker compose exec influxdb influx query \
  'from(bucket:"telemetria") |> range(start:-5m) |> limit(n:6)' \
  --org uab --token "$INFLUX_TOKEN"
```

## Acceso a Grafana

Grafana escucha solo en `127.0.0.1:3000` de la VM. Se accede por túnel SSH,
sin abrir puertos en Azure:

```bash
ssh -i <llave.pem> -L 3000:localhost:3000 azureuser@<IP_PUBLICA>
```

Después abrir `http://localhost:3000` (usuario `admin`, clave `GF_ADMIN_PASSWORD`).

Se aprovisiona automáticamente desde `grafana/provisioning/`:
- Datasource InfluxDB (`uid: influx-lab5`, lenguaje Flux)
- Dashboard "Monitoreo de paciente patient01" (rango por defecto: últimos 4 días)
- Regla de alerta y contact point (webhook)

## Alerta

| Elemento | Valor |
|---|---|
| Regla | FC alta paciente patient01 |
| Consulta | Máximo de `heart_rate` en los últimos 2 minutos |
| Condición | Mayor a 120 bpm |
| Evaluación | Cada 1 min, periodo pendiente de 1 min |
| Sin datos | Se trata como OK |
| Acción | Webhook (URL en la variable `WEBHOOK_URL`) |

Para forzar el disparo (envía ~1 minuto de valores anormales):

```bash
docker compose exec publisher python force_alert.py
```

## Estructura

docker-compose.yml
.env.example
mosquitto/mosquitto.conf
telegraf/telegraf.conf
publisher/{Dockerfile, publisher.py, force_alert.py}
grafana/provisioning/{datasources, dashboards, alerting}/
evidencias/


## Evidencias

La carpeta `evidencias/` contiene las salidas de consola de la ingesta y las
capturas del dashboard, la alerta disparada y la notificación recibida.

## Notas y limitaciones

- La toma de datos presenta huecos debido al apagado de la VM para ahorrar créditos de Azure.
- Mosquitto usa `allow_anonymous true`: es aceptable en el laboratorio porque el puerto 1883 no se publica fuera de la red de Docker, pero no es una configuración de producción.
- No ejecutar `docker compose down -v`: borra los volúmenes y con ellos la toma de datos.
