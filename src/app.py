import json
import os
from flask import Flask, request, jsonify
from confluent_kafka import Consumer, Producer
from csms_backend import retr_charger_list

# TESTTEST
app = Flask(__name__)
app.config['API_KEY'] = os.environ.get('API_KEY')

# Kafka 서버 및 topic 설정
bootstrap_servers = 'juha.iptime.org:29092'
topic = 'topic-to-charger'
# kafka topic 생성
# docker-compose exec kafka kafka-topics --create --topic topic-to-charger --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
# Producer 설정
conf = {'bootstrap.servers': bootstrap_servers}

producer = Producer(conf)
# 메시지 전송 함수
def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def require_api_key(view_function):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == app.config['API_KEY']:
            return view_function(*args, **kwargs)
        return jsonify({'error': 'Unauthorized'}), 401

    return decorated_function

@app.route('/api/get_charger_list', methods=['POST'])
@require_api_key
def get_charger_list():
    """get_charger_list."""
    try:
        # POST 요청에서 데이터 추출
        data = request.get_json()

        # 데이터가 존재하면 Redis에 저장
        if data:
            cs = str(data['crgr_stn_nm'])

            if cs:
                rows = retr_charger_list()

                return jsonify({'result': 'success', 'message': 'ocpp msg sent successfully', 'data':rows})
            else:
                return jsonify({'result': 'error', 'message': 'Key and value are required'})
        else:
            return jsonify({'result': 'error', 'message': 'No data provided'})

    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})

@app.route('/api/send_message', methods=['POST'])
@require_api_key
def store_data():
    try:
        # POST 요청에서 데이터 추출
        data = request.get_json()

        # 데이터가 존재하면 Redis에 저장
        if data:
            print(data)
            mid = str(data['mid'])
            data = data['data']

            if mid and data:
                producer.produce(topic, key=mid, value=json.dumps(data), callback=delivery_report)
                # 메시지 전송 완료 대기
                producer.flush()

                return jsonify({'result': 'success', 'message': 'ocpp msg sent successfully'})
            else:
                return jsonify({'result': 'error', 'message': 'Key and value are required'})
        else:
            return jsonify({'result': 'error', 'message': 'No data provided'})

    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})


@app.route('/api/gen_api_key', methods=['POST'])
def gen_api_key():
    try:
        import secrets
        api_key = secrets.token_hex(32)
        return jsonify({'result': api_key})
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

# append date 2024. 02. 06. (화) 11:06:10 KST\n
# append date 2024. 02. 06. (화) 11:06:45 KST\n
# append date 2024. 02. 06. (화) 11:08:52 KST\n
# append date 2024. 02. 06. (화) 12:32:10 KST\n
# append date 2024. 02. 06. (화) 12:46:27 KST\n
# append date 2024. 02. 06. (화) 12:56:23 KST\n
# append date 2024. 02. 06. (화) 13:02:38 KST\n
# append date 2024. 02. 06. (화) 13:08:40 KST\n
# append date 2024. 02. 06. (화) 13:18:24 KST\n
# append date 2024. 02. 06. (화) 13:26:49 KST\n
# append date 2024. 02. 06. (화) 13:33:30 KST\n
# append date 2024. 02. 06. (화) 13:44:59 KST\n
# append date 2024. 02. 06. (화) 13:52:05 KST\n
# append date 2024. 02. 06. (화) 14:05:33 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 14:21:33 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 14:53:49 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 16:20:28 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 16:58:47 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:06:26 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:17:07 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:20:32 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:34:48 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:44:21 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 17:50:53 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 20:59:09 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:07:01 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:11:56 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:17:00 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:27:37 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:30:38 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:46:03 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 21:52:37 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 22:04:53 KST\n
# deploy commit name : commit of 2024. 02. 06. (화) 22:20:01 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 10:26:27 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 10:32:39 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 10:41:45 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 10:45:13 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 10:50:19 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 11:05:02 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 12:15:34 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 12:18:51 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 12:19:47 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 13:00:59 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 17:34:46 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 17:38:20 KST\n
# deploy commit name : commit of 2024. 02. 07. (수) 17:41:36 KST\n
# deploy commit name : commit of 2024. 02. 14. (수) 14:41:52 KST\n
