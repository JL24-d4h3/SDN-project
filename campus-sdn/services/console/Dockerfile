# Console — imagen del servicio propio, construida sobre el esqueleto común.
FROM python:3.12-slim

WORKDIR /app

COPY contracts/events /app/contracts/events
COPY policy /app/policy
COPY services/common /app/services/common
COPY services/console /app/services/console

RUN pip install --no-cache-dir /app/services/common httpx "uvicorn[standard]"

EXPOSE 8008

CMD ["uvicorn", "services.console.main:app", "--host", "0.0.0.0", "--port", "8008"]
