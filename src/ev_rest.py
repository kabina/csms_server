"""ev_rest
"""
import json
import os
from flask import Flask, request, jsonify
from confluent_kafka import Producer
from csms_backend import retr_charger_list, retr_charger_log

app = Flask(__name__)
app.config['API_KEY'] = os.environ.get('API_KEY')

# Kafka 서버 및 topic 설정
BOOTSTRAP_SERVERS = 'juha.iptime.org:29092'
TOPIC = 'topic-to-charger'
# kafka topic 생성
# docker-compose exec kafka kafka-topics --create --topic topic-to-charger \
# --bootstrap-server kafka:9092 --replication-factor 1 --partitions 1
# Producer 설정
conf = {'bootstrap.servers': BOOTSTRAP_SERVERS}

producer = Producer(conf)
# 메시지 전송 함수
def delivery_report(err, msg):
    """delivery_report.

    :param err:
    :param msg:
    """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

def require_api_key(view_function):
    """require_api_key.

    :param view_function:
    """
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == app.config['API_KEY']:
            return view_function(*args, **kwargs)
        else:
            return jsonify({'error': 'Unauthorized'}), 401

    return decorated_function

@app.route('/api/get_charger_list', methods=['POST'], endpoint='/api/get_charger_list')
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
                rows = retr_charger_list(cs)
                return jsonify({'result': 'success', \
                       'message': 'ocpp msg sent successfully', 'data':rows})
            else:
                return jsonify({'result': 'error', \
                                'message': 'Key and value are required'})
        else:
            return jsonify({'result': 'error', 'message': 'No data provided'})

    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})

@app.route('/api/get_charger_log', methods=['POST'], endpoint='/api/get_charger_log')
@require_api_key
def get_charger_log():
    """get_charger_log."""
    try:
        # POST 요청에서 데이터 추출
        data = request.get_json()

        if data:
            cs = str(data['crgr_stn_nm'])

            if cs:
                rows = retr_charger_log()
                return jsonify({'result': 'success', \
                       'message': 'ocpp msg sent successfully', 'data':rows})
            else:
                return jsonify({'result': 'error', \
                       'message': 'Key and value are required'})
        else:
            return jsonify({'result': 'error', 'message': 'No data provided'})

    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})

@app.route('/api/send_message', methods=['POST'], endpoint='/api/send_message')
@require_api_key
def store_data():
    """store_data."""
    try:
        # POST 요청에서 데이터 추출
        data = request.get_json()

        # 데이터가 존재하면 Redis에 저장
        if data:
            print(data)
            mid = str(data['mid'])
            data = data['data']

            if mid and data:
                producer.produce(TOPIC, key=mid, value=json.dumps(data), callback=delivery_report)
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
    """gen_api_key."""
    try:
        import secrets
        api_key = secrets.token_hex(32)
        return jsonify({'result': api_key})
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)})

@app.after_request
def add_hsts_header(response):
    """add_hsts_header.

    :param response:
    """
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.after_request
def add_csp_header(response):
    """add_csp_header.

    :param response:
    """
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src https://*; child-src 'none';"
    return response

@app.after_request
def add_permissions_policy_header(response):
    """add_permissions_policy_header.

    :param response:
    """
    response.headers['Permissions-Policy'] = "geolocation=(self 'https://nheo.duckdns.org:5000')"
    return response

if __name__ == '__main__':
    app.run()
