# Controller adapter — imagen del servicio propio, construida sobre el
# esqueleto común. Vive junto al controlador (VM de onos1, red host).
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY services/common /app/services/common
COPY services/controller_adapter /app/services/controller_adapter

RUN pip install --no-cache-dir /app/services/common httpx "uvicorn[standard]"

EXPOSE 8090

CMD ["uvicorn", "services.controller_adapter.main:app", "--host", "0.0.0.0", "--port", "8090"]
