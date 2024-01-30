import asyncio
import websockets

async def handle_websocket(websocket, path):
    # 클라이언트가 연결될 때 실행되는 콜백 함수
    print(f"클라이언트가 연결되었습니다. 주소: {websocket.remote_address}")

    try:
        # 클라이언트와의 통신 루프
        while True:
            message = await websocket.recv()
            print(f"수신한 메시지: {message}")

            # 클라이언트에게 응답
            response = f"서버가 수신한 메시지: {message}"
            await websocket.send(response)
            print(f"응답 메시지 전송: {response}")

    except websockets.exceptions.ConnectionClosedError:
        print(f"클라이언트와의 연결이 닫혔습니다.")

# 웹소켓 서버 생성 및 실행
start_server = websockets.serve(handle_websocket, "localhost", 8000)

# 이벤트 루프 실행
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()