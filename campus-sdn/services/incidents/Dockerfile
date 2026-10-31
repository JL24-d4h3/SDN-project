# Incidents — imagen del servicio propio, construida sobre el esqueleto común.
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY services/common /app/services/common
COPY services/incidents /app/services/incidents

RUN pip install --no-cache-dir /app/services/common "uvicorn[standard]"

EXPOSE 8005

CMD ["uvicorn", "services.incidents.main:app", "--host", "0.0.0.0", "--port", "8005"]
