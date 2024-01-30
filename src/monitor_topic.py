from confluent_kafka import Consumer, KafkaException

# Kafka 서버 설정
conf = {
    'bootstrap.servers': 'juha.iptime.org:29092',
    'group.id': '1',
    'auto.offset.reset': 'earliest',  # 가장 이른 오프셋부터 읽기
}

# 토픽 설정
topic = ['topic-to-charger']

# Consumer 인스턴스 생성
consumer = Consumer(conf)

# 특정 토픽으로 구독
consumer.subscribe(topic)
try:
    while True:
        # 메시지 수신 (타임아웃 1초)
        msg = consumer.poll(1000)

        if msg is None:
            continue
        if msg.error():
                print(msg.error())
                break

        # 메시지 출력
        print('Received message:{}: {}'.format(msg.key().decode('utf-8'),
                                               msg.value().decode('utf-8')))

except KeyboardInterrupt:
    pass

finally:
    # Consumer 종료
    consumer.close()