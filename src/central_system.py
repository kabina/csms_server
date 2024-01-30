import asyncio
import logging
import ssl
from redis import StrictRedis
from ChargePoint import ChargePoint
from confluent_kafka import Consumer, KafkaError
import multiprocessing
from multiprocessing import freeze_support

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)

socket_pool = {}
# Kafka 서버 및 topic 설정
bootstrap_servers = 'juha.iptime.org:29092'
topic = 'topic-to-charger'
group_id = '1'

# Consumer 설정
conf = {
    'bootstrap.servers': bootstrap_servers,
    'group.id' : group_id,
    'enable.auto.commit': False,
    'auto.offset.reset': 'earliest'  # 가장 처음부터 메시지 소비
}
# Consumer 생성
consumer = Consumer(conf)
# Topic 구독
consumer.subscribe([topic])


logging.basicConfig(level=logging.INFO)


async def on_connect(websocket, path):
    """For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logging.error("Client hasn't requested any Subprotocol. Closing Connection")
        return await websocket.close()
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning(
            "Protocols Mismatched | Expected Subprotocols: %s,"
            " but client supports  %s | Closing connection",
            websocket.available_subprotocols,
            requested_protocols,
        )
        return await websocket.close()

    charge_point_id = path.strip("/").split("/")[-1]
    print(charge_point_id)
    cp = ChargePoint(charge_point_id, websocket)

    """
    socket pool에 websocket 등록
    """
    socket_pool[charge_point_id] = websocket

    await cp.start()


async def check_topic_periodically(socket_pool, consumer):
    while True:
        # 메시지 소비
        print("Before polling")
        msg = consumer.poll(timeout=1000)  # 1초마다 폴링
        print("Before message received")
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition event, not an error
                continue
            else:
                print(f'Error: {msg.error()}')
                break
        key, msg_decoded = (msg.key().decode('utf-8') if msg.key() else None,
                            msg.value().decode('utf-8') if msg.value() else None
                            )

        # 메시지 출력
        print(f"Received message: {key}:{msg.value().decode('utf-8')}")
        if key in socket_pool :
            socket_pool[key].send(msg_decoded)
            print(f"Sent message: {key}:{msg_decoded}")
        else:
            print(f"ChargePoint {key} not found")

        consumer.commit()


async def main():

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="certificate.pem", keyfile="private-key.pem")
    subprotocol = ["ocpp1.6"]
    server = await websockets.serve(
        on_connect,
        "localhost",
        443,  # HTTPS 기본 포트
        subprotocols=subprotocol,
        ssl=ssl_context
    )

    logging.info("Server Started listening to new connections...")

    # message_task = asyncio.create_task(check_topic_periodically(consumer))

    # tasks = [message_task, server.wait_closed()]
    # await asyncio.gather(*tasks)


    await server.wait_closed()
    # await message_task

if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v

    asyncio.run(main())

    socket_pool = multiprocessing.Manager().dict()

    child = multiprocessing.Process(target=check_topic_periodically, args=(socket_pool, consumer, ))
    child.start()
    child.join()