import asyncio
import websockets

async def connect_websocket():
    uri = "ws://localhost:8000/TEST/TEST1"  # 웹소켓 서버의 주소 및 포트
    async with websockets.connect(uri) as websocket:
        # 연결이 성공하면 이 부분에서 웹소켓을 사용하여 통신 가능
        print("WebSocket 연결 성공")

# 비동기 이벤트 루프 생성
loop = asyncio.get_event_loop()
# 웹소켓 연결 실행
loop.run_until_complete(connect_websocket())
# 이벤트 루프 실행
loop.run_forever()