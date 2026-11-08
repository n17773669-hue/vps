"""
Đọc chat YouTube live (không cần API key) và gửi vào trang overlay.
Cài:  pip install pytchat websockets
Chạy: python chat_server.py
(ID live điền ngay trên trang overlay, ở nút ⚙ góc phải trên. Có thể truyền sẵn: python chat_server.py ID_LIVE)
"""
import asyncio, json, sys, threading, time
import pytchat
import websockets

HOST, PORT = "localhost", 8765
state = {"id": sys.argv[1] if len(sys.argv) > 1 else None}
clients = set()


async def handler(ws):
    clients.add(ws)
    try:
        async for raw in ws:
            try:
                v = json.loads(raw).get("video")
            except Exception:
                continue
            if v and v != state["id"]:
                state["id"] = v
                print("Đổi sang live:", v)
    finally:
        clients.discard(ws)


async def broadcast(msg):
    if clients:
        websockets.broadcast(clients, msg)


def read_chat(loop):
    while True:
        vid = state["id"]
        if not vid:
            time.sleep(1)
            continue
        try:
            chat = pytchat.create(video_id=vid)
            print("Đã kết nối chat của", vid)
            while chat.is_alive() and state["id"] == vid:
                for c in chat.get().sync_items():
                    data = json.dumps(
                        {"author": c.author.name, "text": c.message},
                        ensure_ascii=False,
                    )
                    print(c.author.name, ":", c.message)
                    asyncio.run_coroutine_threadsafe(broadcast(data), loop)
                time.sleep(1)
        except Exception as e:
            print("Lỗi đọc chat:", e)
        if state["id"] == vid:
            print("Thử kết nối lại sau 5 giây...")
            time.sleep(5)


async def main():
    loop = asyncio.get_running_loop()
    threading.Thread(target=read_chat, args=(loop,), daemon=True).start()
    async with websockets.serve(handler, HOST, PORT):
        print(f"WebSocket chạy tại ws://{HOST}:{PORT}")
        await asyncio.Future()


asyncio.run(main())
