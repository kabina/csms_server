import asyncio
import ssl
import logging
import websockets
import json
import os
from ChargePoint import ChargePoint
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from csms_backend import check_connection

WEBSOCKET_PORT = os.environ.get('SOCK_PORT')
SUBPROTOCOL = 'ocpp1.6'

logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP_SERVERS = 'juha.iptime.org:29092'
KAFKA_TOPIC_SOCKET_INFO = 'topic-socket-info'
KAFKA_TOPIC_MESSAGES = 'topic-to-charger'

class WebSocketManager:
    def __init__(self):
        self.connections = {}

    def add_connection(self, key, websocket):
        print(f"Adding WebSocket connection for {key}")
        self.connections[key] = websocket

    def get_connection(self, key):
        return self.connections.get(key)

    def remove_connection(self, key):
        del self.connections[key]

async def consume_kafka(ws_manager):
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC_MESSAGES,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    await consumer.start()

    try:
        async for message in consumer:
            key = message.key.decode('utf-8')
            value = message.value
            websocket = ws_manager.get_connection(key)
            if websocket:
                # WebSocket connection이 존재하면 해당 객체를 사용하여 작업 수행
                # 예: 메시지 전송, 연결 닫기 등
                logging.info(f"Sending message: {key}:{value}")
                await websocket.send(json.dumps(value))
            else:
                # WebSocket connection이 존재하지 않으면 처리 로직 추가
                pass
    finally:
        await consumer.stop()

async def handle_websocket_connection(websocket, path, ws_manager, producer):
    charger_model, charger_serial = path.strip("/").split("/")[-2:]
    authorizatiop_key = websocket.request_headers.get('Authorization')
    logging.info(f"Got WebSocket connection for {charger_serial}")

    requested_protocols = websocket.request_headers.get('Sec-WebSocket-Protocol')
    if SUBPROTOCOL not in (requested_protocols or '').split(','):
        logging.error(f"Invalid subprotocol requested: {requested_protocols}")
        return await websocket.close()
    # Connection 정보 체크
    mid = check_connection(charger_model, charger_serial, authorizatiop_key)
    if not mid:
        logging.error(f"Invalid Connetion Information from {path}")
        return await websocket.close(1008, "Connection refused")

    # WebSocket connection 정보 추출
    websocket_info = {
        'key': mid,
        'uri': websocket.request_headers['Host'] + path,
        # 추가 정보도 필요하다면 여기에 추가
    }
    charge_point_serial = path.strip("/").split("/")[-1]
    # WebSocket connection 관리자에 추가
    ws_manager.add_connection(mid, websocket)

    cp = ChargePoint(mid, websocket)
    try :
        await cp.start()
    except websockets.exceptions.ConnectionClosedOK as e:
        logging.info(f"WebSocket connection closed for {mid}")

    # Kafka에 WebSocket connection 정보 전송
    await producer.send_and_wait(KAFKA_TOPIC_SOCKET_INFO, key=mid, value=websocket_info)



    try:
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"WebSocket connection closed for {mid}")
    except websockets.exceptions.ConnectionClosedError:
        logging.error(f"WebSocket connection error for {mid}")
    finally:
        # WebSocket connection이 종료되면 관리자에서 제거
        ws_manager.remove_connection(mid)

async def main():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="certificate.pem", keyfile="private-key.pem")

    # WebSocket connection 관리자 생성
    ws_manager = WebSocketManager()

    # Kafka 소비자 및 프로듀서 생성
    consumer_task = asyncio.create_task(consume_kafka(ws_manager))
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    # WebSocket 서버 실행
    server_task = websockets.serve(
        lambda ws, path: handle_websocket_connection(ws, path, ws_manager, producer),
        "0.0.0.0", WEBSOCKET_PORT, subprotocols=[SUBPROTOCOL], ssl=ssl_context
    )

    # 두 작업을 병렬로 실행
    await asyncio.gather(server_task, consumer_task)

if __name__ == "__main__":
    asyncio.run(main())
