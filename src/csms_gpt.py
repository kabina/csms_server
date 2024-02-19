import asyncio
import ssl
import logging
import websockets
from kafka import KafkaConsumer, KafkaProducer
from ChargePoint import ChargePoint

# Kafka 설정
KAFKA_SERVER = 'juha.iptime.org:29092'
KAFKA_TOPIC_MESSAGES = 'topic-to-charger'
KAFKA_TOPIC_SOCKET_INFO = 'topic-socket-info'

# WebSocket 설정
WEBSOCKET_PORT = 8765
SUBPROTOCOL = 'ocpp1.6'

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# WebSocket 연결을 저장하는 딕셔너리
socket_pool = {}

async def consume_kafka_messages():
    consumer = KafkaConsumer(
        KAFKA_TOPIC_MESSAGES,
        bootstrap_servers=KAFKA_SERVER,
        group_id='websocket-consumer',
        enable_auto_commit=False,
        auto_offset_reset='earliest'
    )

    for message in consumer:
        key = message.key.decode('utf-8')
        payload = message.value.decode('utf-8')

        if key in socket_pool:
            websocket_connection = socket_pool[key]
            await websocket_connection.send(payload)
            logging.info(f"Sent Kafka message to {key}: {payload}")

        # 적절한 시점에 Kafka commit을 수행
        consumer.commit()

async def handle_websocket_connection(websocket, path):
    # WebSocket connection에서 path를 추출하여 key로 사용
    key = path.strip('/')
    print("Got websocket connection")

    # subprotocol이 일치하는지 확인
    requested_protocols = websocket.request_headers.get('Sec-WebSocket-Protocol')
    if SUBPROTOCOL not in (requested_protocols or '').split(','):
        logging.error(f"Invalid subprotocol requested: {requested_protocols}")
        return await websocket.close()

    # WebSocket 연결을 socket_pool에 저장
    socket_pool[key] = websocket
    logging.info(f"WebSocket connection established for {key}")

    charge_point_id = path.strip("/").split("/")[-1]
    print(charge_point_id)

    cp = ChargePoint(charge_point_id, websocket)

    """
    socket pool에 websocket 등록
    """
    socket_pool[charge_point_id] = websocket

    await cp.start()

    # Kafka에 WebSocket 연결 정보 전송
    producer = KafkaProducer(bootstrap_servers=KAFKA_SERVER)
    producer.send(KAFKA_TOPIC_SOCKET_INFO, key.encode('utf-8'), charge_point_id.encode('utf-8'))
    producer.flush()

    # ...

    try:
        # 연결이 유지되는 동안 대기
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosedOK:
        # WebSocket이 정상적으로 닫힌 경우
        logging.info(f"WebSocket connection closed for {key}")
    except websockets.exceptions.ConnectionClosedError:
        # WebSocket이 오류로 닫힌 경우
        logging.error(f"WebSocket connection error for {key}")
    finally:
        # WebSocket이 닫히면 socket_pool에서 제거
        del socket_pool[key]
        logging.info(f"Removed WebSocket connection for {key}")

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="certificate.pem", keyfile="private-key.pem")

    # Kafka consumer를 비동기로 실행
    kafka_consumer_task = asyncio.create_task(consume_kafka_messages())

    # WebSocket 서버를 비동기로 실행
    websocket_server_task = asyncio.create_task(websockets.serve(
        handle_websocket_connection, '127.0.0.1', WEBSOCKET_PORT, subprotocols=[SUBPROTOCOL], ssl=ssl_context
    ))

    # 두 개의 task를 함께 실행
    await asyncio.gather(kafka_consumer_task, websocket_server_task)

if __name__ == "__main__":
    asyncio.run(main())