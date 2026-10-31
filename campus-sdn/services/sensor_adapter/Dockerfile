# Sensor adapter — imagen del servicio propio, construida sobre el esqueleto
# común. La NIC del espejo la lee Suricata; este servicio solo consume su log.
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY services/common /app/services/common
COPY services/sensor_adapter /app/services/sensor_adapter

RUN pip install --no-cache-dir /app/services/common "uvicorn[standard]"

EXPOSE 8009

CMD ["uvicorn", "services.sensor_adapter.main:app", "--host", "0.0.0.0", "--port", "8009"]
