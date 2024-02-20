import json
import os
from flask import Flask, request, jsonify
from confluent_kafka import Consumer, Producer
from csms_backend import retr_charger_list

app = Flask(__name__)
app.config['API_KEY'] = os.environ.get('API_KEY')


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
        else:
            return jsonify({'error': 'Unauthorized'}), 401

    return decorated_function

@app.route('/api/get_charger_list', methods=['POST'])
@require_api_key
def get_charger_list():
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
    app.run(debug=False, host='127.0.0.1', port=5000)

# deploy commit name : commit of 2024. 02. 19. (월) 10:54:05 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 11:53:13 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 12:21:21 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 12:39:32 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 12:53:08 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 13:11:50 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 13:26:08 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 14:33:20 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 14:57:04 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 15:21:58 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 15:43:35 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 15:46:09 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 15:50:41 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 15:59:18 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 17:04:33 KST\n
# deploy commit name : commit of 2024. 02. 19. (월) 17:07:02 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 09:12:08 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 09:22:49 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 09:30:58 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 09:42:07 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 09:42:16 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 10:16:09 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 10:16:17 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 10:34:23 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 10:49:18 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 10:55:20 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 11:03:14 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 11:47:18 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 11:53:32 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 12:01:23 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 12:37:02 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 12:38:10 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 12:39:15 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 12:49:14 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:00:49 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:20:12 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:21:46 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:22:45 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:33:04 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:44:46 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 13:57:45 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 14:11:31 KST\n
# deploy commit name : commit of 2024. 02. 20. (화) 14:19:21 KST\n
