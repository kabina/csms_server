"""csms_server for ocpp1.6 and 2.0.1
"""
import asyncio
import ssl
import logging
import json
import os
import websockets
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from ChargePoint16 import ChargePoint as cp16
from ChargePoint201 import ChargePoint as cp201
from csms_backend import check_connection

WEBSOCKET_PORT = os.environ.get('SOCK_PORT')
WEBSOCKET_SERVER = os.environ.get('SOCK_SERVER')
SUBPROTOCOL = ['ocpp1.6', 'ocpp2.0.1']

logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP_SERVERS = 'juha.iptime.org:29092'
KAFKA_TOPIC_SOCKET_INFO = 'topic-socket-info'
KAFKA_TOPIC_MESSAGES = 'topic-to-charger'

class WebSocketManager:
    """WebSocketManager."""

    def __init__(self):
        """__init__."""
        self.connections = {}

    def add_connection(self, key, websocket):
        """add_connection.

        :param key:
        :param websocket:
        """
        print(f"Adding WebSocket connection for {key}")
        self.connections[key] = websocket

    def get_connection(self, key):
        """get_connection.

        :param key:
        """
        """get_connection.

        :param key:
        """
        return self.connections.get(key)

    def remove_connection(self, key):
        """remove_connection.

        :param key:
        """
        del self.connections[key]

async def consume_kafka(ws_manager):
    """consume_kafka.

    :param ws_manager:
    """
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
    """handle_websocket_connection.

    :param websocket:
    :param path:
    :param ws_manager:
    :param producer:
    """
    proto = {"ocpp16":cp16, "ocpp201":cp201}
    uri_protocol, charger_model, charger_serial = path.strip("/").split("/")[-3:]
    authorizatiop_key = websocket.request_headers.get('Authorization')
    logging.info("Got WebSocket connection for %s", charger_serial)

    requested_protocols = websocket.request_headers.get('Sec-WebSocket-Protocol')
    if requested_protocols not in SUBPROTOCOL:
        logging.error("Invalid subprotocol requested: %s", requested_protocols)
        return await websocket.close()
    # Connection 정보 체크
    mid = check_connection(charger_model, charger_serial, authorizatiop_key)
    if not mid:
        logging.error("Invalid Connetion Information from %s", path)
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

    #cp = ChargePoint(mid, websocket)
    cp = proto[uri_protocol](mid, websocket)
    try :
        await cp.start()
        except websockets.exceptions.ConnectionClosedOK as e:
        logging.info("WebSocket connection closed for %s", mid)

    # Kafka에 WebSocket connection 정보 전송
    await producer.send_and_wait(KAFKA_TOPIC_SOCKET_INFO, key=mid, value=websocket_info)



    try:
        await websocket.wait_closed()
    except websockets.exceptions.ConnectionClosedOK:
        logging.info("WebSocket connection closed for %s", mid)
    except websockets.exceptions.ConnectionClosedError:
        logging.error(f"WebSocket connection error for {mid}")
    finally:
        # WebSocket connection이 종료되면 관리자에서 제거
        ws_manager.remove_connection(mid)

async def main():
    """main."""
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
        WEBSOCKET_SERVER, WEBSOCKET_PORT, subprotocols=SUBPROTOCOL, ssl=ssl_context
    )

    # 두 작업을 병렬로 실행
    await asyncio.gather(server_task, consumer_task)


if __name__ == "__main__":
    asyncio.run(main())
