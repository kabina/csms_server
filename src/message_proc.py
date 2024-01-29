import asyncio
import logging
from confluent_kafka import Consumer, KafkaError

# Kafka 서버 및 topic 설정
bootstrap_servers = 'juha.iptime.org:29092'
topic = 'topic-to-charger'
group_id = '1'

# Consumer 설정
conf = {
    'bootstrap.servers': bootstrap_servers,
    'group.id': group_id,
    'enable.auto.commit': False,
    'auto.offset.reset': 'earliest'  # 가장 처음부터 메시지 소비
}

socket_pool = {}

logging.basicConfig(level=logging.INFO)

async def check_topic_periodically(consumer):
    commit_interval = 100  # 메시지 처리 후 매 100개마다 커밋
    message_count = 0

    while True:
        try:
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
            if key in socket_pool:
                socket_pool[key].send(msg_decoded)
                print(f"Sent message: {key}:{msg_decoded}")
            else:
                print(f"ChargePoint {key} not found")

            # 메시지 처리 후 commit
            message_count += 1

            if message_count >= commit_interval:
                # 일정 갯수만큼 메시지를 처리하면 커밋
                consumer.commit()
                message_count = 0

        except Exception as e:
            print(f'Error during message processing: {e}')

async def main():
    # Consumer 생성
    consumer = Consumer(conf)
    # Topic 구독
    consumer.subscribe([topic])

    logging.info("Message Processor Started listening to new message...")

    # message_task = asyncio.create_task(check_topic_periodically(consumer))
    # await message_task

    await check_topic_periodically(consumer)

if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())