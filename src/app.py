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

# deploy commit name : commit of 2024. 02. 21. (수) 13:51:30 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 13:52:09 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:00:39 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:15:16 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:23:40 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:27:36 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:34:49 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:42:14 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 14:54:52 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 15:41:13 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 15:48:46 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 15:51:20 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 15:59:03 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 16:36:27 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 16:43:45 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 16:58:45 KST\n
# deploy commit name : commit of 2024. 02. 21. (수) 17:01:19 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 09:59:32 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 10:01:20 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 10:14:48 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 13:14:57 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 13:29:00 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 13:58:57 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 14:43:00 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 14:51:05 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 14:57:50 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 15:04:47 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 15:11:49 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 15:17:56 KST\n
# deploy commit name : commit of 2024. 02. 22. (목) 15:58:52 KST\n
