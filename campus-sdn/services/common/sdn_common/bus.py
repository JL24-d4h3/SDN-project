"""Publicación y consumo en el bus (RabbitMQ, exchange `plataforma`)."""

import json
import time

import pika

# El LLD enruta por `evento.<Tipo>`; el código usa la forma inglesa
# `event.<Tipo>` (correspondencia documentada en contracts/events/README).
EXCHANGE = "plataforma"


def publish_event(bus_url: str, event: dict) -> None:
    """Publica un evento con confirmación de publicación.

    Publisher confirms activado (LLD 02_eventos §5): la llamada retorna
    cuando el broker recibió el mensaje, no antes. El evento debe venir
    validado (sdn_common.events.validate_event).
    """
    routing_key = f"event.{event['type']}"
    parameters = pika.URLParameters(bus_url)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.confirm_delivery()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic",
                             durable=True)
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=routing_key,
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2),  # persistente
    )
    connection.close()


def consume_events(bus_url: str, queue: str, bindings: list[str],
                   handler, *, prefetch: int = 10) -> None:
    """Consume de una cola durable con ack manual, DLQ y reintentos.

    `bindings` es la lista de tipos de evento (se enlazan a sus claves
    `event.<Tipo>`). `handler(event)` devuelve True si procesó (ack) o
    False si no (nack → reintento). La idempotencia es por event_id con
    una ventana en memoria (prototipo; la ventana durable llega con
    bd_politicas). Los reintentos cuentan por event_id en memoria y al
    agotarse el mensaje pasa a `dlq.<queue>` — simplificación del
    retroceso 1 s → 60 s del LLD, documentada.

    Bloquea: ejecutar en un hilo o proceso dedicado del servicio.
    """
    MAX_RETRIES = 5
    parameters = pika.URLParameters(bus_url)
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except Exception:
            # El servicio puede arrancar antes que el bus (F-04): se
            # reintenta hasta conectar.
            time.sleep(5)
    channel = connection.channel()
    channel.basic_qos(prefetch_count=prefetch)
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic",
                             durable=True)
    channel.queue_declare(queue=f"dlq.{queue}", durable=True)
    channel.queue_bind(queue=f"dlq.{queue}", exchange=EXCHANGE,
                       routing_key=f"dlq.{queue}")
    channel.queue_declare(
        queue=queue, durable=True,
        arguments={"x-dead-letter-exchange": EXCHANGE,
                   "x-dead-letter-routing-key": f"dlq.{queue}"})
    for event_type in bindings:
        # "*" enlaza todo el catálogo (cola de auditoría, LLD §4).
        routing_key = "event.#" if event_type == "*" else \
            f"event.{event_type}"
        channel.queue_bind(queue=queue, exchange=EXCHANGE,
                           routing_key=routing_key)

    seen: set[str] = set()
    attempts: dict[str, int] = {}

    def reject(event_id: str, delivery_tag: int) -> None:
        count = attempts.get(event_id, 0) + 1
        if count >= MAX_RETRIES:
            attempts.pop(event_id, None)
            channel.basic_nack(delivery_tag, requeue=False)  # → DLQ
        else:
            attempts[event_id] = count
            channel.basic_nack(delivery_tag, requeue=True)

    def on_message(ch, method, properties, body):
        event = json.loads(body)
        event_id = event["event_id"]
        if event_id in seen:
            ch.basic_ack(method.delivery_tag)
            return
        try:
            if handler(event):
                seen.add(event_id)
                attempts.pop(event_id, None)
                ch.basic_ack(method.delivery_tag)
            else:
                reject(event_id, method.delivery_tag)
        except Exception:
            reject(event_id, method.delivery_tag)

    channel.basic_consume(queue=queue, on_message_callback=on_message)
    channel.start_consuming()
