"""
csms_backend.py
"""
import os
import json
from datetime import datetime
import psycopg2
from psycopg2 import sql
from TransactionGenerator import TransactionGenerator
from ocpp.v16.enums import Action, RegistrationStatus, AuthorizationStatus

trans_generator = TransactionGenerator()

def get_crgr_no(trailing_url):
    """get_crgr_no.

    :param trailing_url:
    """
    return trailing_url.split('/')[-1]

def get_connection():
    """get_connection."""
    connection = psycopg2.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_SEVER')
    )
    return connection

def get_total_charged_value(crgr_no, trans_id):
    """get_total_charged_value.

    :param crgr_no:
    :param trans_id:
    """
    total_energy = 0
    connection = None
    try:
        # PostgreSQL에 연결
        connection = get_connection()
        total_energy = 0
        # 쿼리 작성
        query = sql.SQL("""
            SELECT ( meter_stop - meter_start ) as total_charged_value
            FROM crgr_trans
            WHERE crgr_no = %s
              AND trans_id = %s
        """)

        # 쿼리 실행
        with connection.cursor() as cursor:
            cursor.execute(query, (crgr_no, trans_id))
            result = cursor.fetchone()

        # 결과 처리
        if result and result[0] is not None:
            total_energy = result[0]

    except psycopg2.Error as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()
        return total_energy

def proc_message(crgr_no, message):
    """proc_message.

    :param crgr_no:
    :param message:
    """

    ocpp_message = json.loads(message)
    print(ocpp_message)
    if len(ocpp_message) > 3 :
        msg_id, msg_type, msg_body = ocpp_message[1:]
    else:
        msg_id, msg_body = ocpp_message[1:]
        msg_type = "Response"

    msg_body = json.dumps(msg_body)

    connection = get_connection()
    cursor = connection.cursor()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + \
        f".{datetime.now().microsecond}"
    insert_query = sql.SQL("""
       INSERT INTO crgr_msgs (crgr_no, msg_id, msg_type, \
       msg_body, regr_dttm, updt_dttm)
       VALUES (%s, %s, %s, %s, %s, %s)
       """)
    cursor.execute(insert_query, (crgr_no, msg_id, msg_type, msg_body, \
                                  current_datetime, current_datetime))

    connection.commit()
    cursor.close()
    connection.close()

def get_idtags_status(id_tag, trailing_url):
    """get_idtags_status.

    :param id_tag:
    :param trailing_url:
    """
    """
    사용자 RF Card상태 체크 후 결과값 리턴
    이용정지/해지 : Blocked
    타 충전기 충전 중 : concurrentTx
    기타 : Invalid
    TODO: 쿼리에 문제가 있음. 수정 필요.
    :return: accepted, blocked, expired, invalid, ConcurrentTx
    """

    total_energy = 0
    connection = None
    try:
        # PostgreSQL에 연결
        connection = get_connection()
        total_energy = 0
        # 쿼리 작성
        query = sql.SQL("""
            SELECT ii.card_no, ct.id_tag
            FROM idtag_info as ii
            LEFT JOIN crgr_trans as ct ON ii.card_no = ct.id_tag
            WHERE ii.card_no = %s
              AND ii.card_stats_cd = '01' and ii.isu_stats_cd > '01'
              AND ct.meter_start_dttm is not null and ct.meter_stop_dttm is null
              AND ct.meter_start_dttm >= NOW() - INTERVAL '24 hours'
              AND ct.crgr_no != %s
        """)

        # 쿼리 실행
        with connection.cursor() as cursor:
            cursor.execute(query, (id_tag, get_crgr_no(trailing_url)))
            result = cursor.fetchone()

        # 결과 처리
        if result is None:
            return AuthorizationStatus.accepted
        if result and result[0] is not None and result[1] is None:
            return AuthorizationStatus.accepted
        elif result and result[0] is not None and result[1] is not None:
            return AuthorizationStatus.concurrent_tx

    except psycopg2.Error as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()


    return AuthorizationStatus.invalid


def create_transaction(crgr_no, connector_id, id_tag, meter_start):
    """create_transaction.

    :param crgr_no:
    :param connector_id:
    :param id_tag:
    :param meter_start:
    """
    transaction_id = trans_generator.get_next_value()

    connection = get_connection()
    cursor = connection.cursor()
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f".{datetime.now().microsecond}"
    insert_query = sql.SQL("""
                    INSERT INTO crgr_trans (crgr_no, cntr_id, trans_id, id_tag, meter_start, meter_start_dttm, regr_dttm, updt_dttm)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """)
    cursor.execute(insert_query, (get_crgr_no(crgr_no), connector_id, transaction_id, id_tag, meter_start, current_datetime, current_datetime, current_datetime))

    connection.commit()
    cursor.close()
    connection.close()

    return transaction_id

def update_meter_value(crgr_no, connector_id, transaction_id, meter_value):
    """update_meter_value.

    :param crgr_no:
    :param connector_id:
    :param transaction_id:
    :param meter_value:
    """

    connection = get_connection()
    cursor = connection.cursor()
    meter = meter_value
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f".{datetime.now().microsecond}"
    """
    특정 충전기의 최근 transaction에 대해 Update
    """
    cursor.execute("""
                    UPDATE crgr_trans 
                    SET meter_stop = %s, updt_dttm = %s
                    WHERE crgr_no = %s and cntr_id = %s and trans_id = %s
                     and regr_dttm = (  select max(regr_dttm) 
                                        from crgr_trans 
                                        where crgr_no = %s and cntr_id = %s
                                        )
                """, (meter, current_datetime, get_crgr_no(crgr_no), \
                      connector_id, transaction_id,
                      get_crgr_no(crgr_no), connector_id))

    connection.commit()
    cursor.close()
    connection.close()

    return transaction_id

def stop_transaction(crgr_no, transaction_id, meter_stop):
    """stop_transaction.

    :param crgr_no:
    :param transaction_id:
    :param meter_stop:
    """

    connection = get_connection()
    cursor = connection.cursor()

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + \
        f".{datetime.now().microsecond}"
    """
    특정 충전기의 StopTransaction에 따른 meter_stop, meter_stop_dttm Update
    """
    cursor.execute("""
                    UPDATE crgr_trans 
                    SET meter_stop = %s, updt_dttm = %s, meter_stop_dttm = %s
                    WHERE crgr_no = %s and trans_id = %s
                     and regr_dttm = (  select max(regr_dttm) 
                                        from crgr_trans 
                                        where crgr_no = %s and
                                        trans_id = %s
                                        )
                """, (meter_stop, current_datetime, current_datetime, \
                      get_crgr_no(crgr_no), transaction_id,
                      get_crgr_no(crgr_no), transaction_id))

    connection.commit()
    cursor.close()
    connection.close()

    return transaction_id

def update_charger_status(crgr_no, connector_id, status, error_code):
    """update_charger_status.

    :param crgr_no:
    :param connector_id:
    :param status:
    :param error_code:
    """

    connection = get_connection()
    cursor = connection.cursor()

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + f".{datetime.now().microsecond}"
    """
    특정 충전기의 StopTransaction에 따른 meter_stop, meter_stop_dttm Update
    """
    cursor.execute("""
                    UPDATE crgr_info
                    SET crgr_stats = %s, 
                        err_cd = %s, 
                        updt_dttm = %s
                    WHERE crgr_no = %s 
                        and cntr_id = %s
                """, (status, error_code, current_datetime, get_crgr_no(crgr_no), connector_id))

    connection.commit()
    cursor.close()
    connection.close()


def check_connection(model, serial, auth_key) :
    """check_connection.

    :param model:
    :param serial:
    :param auth_key:
    """
    """
    websocket connection 발생 시 적절한 충전기로 부터의 Connection인지 확인

    :return: 403 if not valid
    """

    print(model)
    print(serial)
    print(auth_key)
    total_energy = 0
    connection = None
    try:
        # PostgreSQL에 연결
        connection = get_connection()
        total_energy = 0
        # 쿼리 작성
        query = sql.SQL("""
            SELECT CRGR_MST_NO 
            FROM CRGR_MST_INFO AS CM
            WHERE CM.CRGR_MDL_ID = %s 
                AND CM.CRGR_SERIAL_NO = %s 
                AND CM.AUTH_KEY = %s
        """)

        # 쿼리 실행
        with connection.cursor() as cursor:
            cursor.execute(query, (model, serial, auth_key))
            result = cursor.fetchone()

        # 결과 처리
        if result is None:
            return None
        else:
            return result[0]

    except psycopg2.Error as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()

def retr_charger_list(crgr_stn_nm) :
    """
    websocket connection 발생 시 적절한 충전기로 부터의 Connection인지 확인

    :return: 403 if not valid
    """

    total_energy = 0
    connection = None
    try:
        # PostgreSQL에 연결
        connection = get_connection()
        charger_list = []
        # 쿼리 작성
        query = sql.SQL("""
            SELECT crgr_mst_no 
            FROM CRGR_MST_INFO AS CM
        """)

        # 쿼리 실행
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            charger_list = [{'crgr_mst_no': result[0]} for result in results]

            return charger_list

    except psycopg2.Error as e:
        print(f"Error: {e}")
    finally:
        if connection:
            connection.close()

def retr_charger_log() :
    """
    websocket connection 발생 시 적절한 충전기로 부터의 Connection인지 확인

    :return: 403 if not valid
    """

    total_energy = 0
    connection = None
    try:
        # PostgreSQL에 연결
        connection = get_connection()
        total_energy = 0
        # 쿼리 작성
        query = sql.SQL("""
            SELECT msg_id, crgr_no, msg_type, msg_body, msg_resp 
            FROM crgr_msgs AS CM
        """)

        # 쿼리 실행
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        # 결과 처리
        msgs = [{'msg_id': result[0],
                'crgr_no': result[1],
                'msg_type': result[2],
                'msg_body': result[3],
                'msg_resp': result[4]} for result in results]

        return msgs

    except psycopg2.Error as e:
        print(f"Error: {e}")

    finally:
        if connection:
            connection.close()
