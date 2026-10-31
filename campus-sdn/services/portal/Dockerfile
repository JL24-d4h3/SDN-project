# Portal (I3) — imagen del servicio propio, construida sobre el esqueleto
# común (plan 09 §5: los servicios propios se construyen, no se descargan).
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY services/common /app/services/common
COPY services/portal /app/services/portal

RUN pip install --no-cache-dir /app/services/common httpx "uvicorn[standard]"

EXPOSE 8080

CMD ["uvicorn", "services.portal.main:app", "--host", "0.0.0.0", "--port", "8080"]
