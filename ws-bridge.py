import asyncio
import json
import os
import struct
import sys
import websockets
import aiohttp

POLICY_FILE = '''<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/schema/dtd/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" to-ports="*"/>
</cross-domain-policy>
'''

LOGIN_PORT = 5150
GAME_PORT = 90
BRIDGE_PORT = 9091

WS_BRIDGE_TOKEN = os.environ.get("WS_BRIDGE_TOKEN", "")

async def relay(ws, tcp_reader, tcp_writer, label):
    try:
        while True:
            msg = await ws.recv()
            if isinstance(msg, bytes):
                tcp_writer.write(msg)
                await tcp_writer.drain()
            else:
                tcp_writer.write(msg.encode())
                await tcp_writer.drain()
    except (websockets.exceptions.ConnectionClosed, ConnectionError):
        pass
    except Exception as e:
        print(f"[{label}] relay error: {e}")
    finally:
        if not tcp_writer.is_closing():
            tcp_writer.close()

async def relay_tcp_to_ws(ws, tcp_reader, label):
    try:
        while True:
            data = await tcp_reader.read(4096)
            if not data:
                break
            await ws.send(data)
    except (websockets.exceptions.ConnectionClosed, ConnectionError):
        pass
    except Exception as e:
        print(f"[{label}] tcp->ws error: {e}")

async def handle_connection(ws):
    path = ws.request.path
    auth_header = ws.request.headers.get("authentication", "")

    # M21: validate WS bridge token if configured
    if WS_BRIDGE_TOKEN:
        if auth_header != WS_BRIDGE_TOKEN:
            print(f"[{path}] auth rejected: token mismatch")
            await ws.close(4001, "authentication failed")
            return
        print(f"[{path}] auth accepted")

    port = LOGIN_PORT if "login" in path else GAME_PORT if "game" in path else None
    label = path

    if port is None:
        print(f"[{label}] unknown path, closing")
        await ws.close(4000, "unknown path")
        return

    try:
        tcp_reader, tcp_writer = await asyncio.open_connection("127.0.0.1", port)
    except ConnectionRefusedError:
        print(f"[{label}] TCP connection refused to 127.0.0.1:{port}")
        await ws.close(4000, "backend unavailable")
        return

    print(f"[{label}] connected to 127.0.0.1:{port}")

    ws_to_tcp = asyncio.create_task(relay(ws, tcp_reader, tcp_writer, label))
    tcp_to_ws = asyncio.create_task(relay_tcp_to_ws(ws, tcp_reader, label))
    done, _ = await asyncio.wait(
        [ws_to_tcp, tcp_to_ws],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in done:
        task.result()
    for task in {ws_to_tcp, tcp_to_ws} - done:
        task.cancel()

    if not tcp_writer.is_closing():
        tcp_writer.close()

    print(f"[{label}] disconnected")

POLICY_REQUEST = b"<policy-file-request/>\x00"

async def handle_crossdomain(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=5)
        if POLICY_REQUEST in data:
            writer.write(POLICY_FILE.encode() + b"\x00")
            await writer.drain()
            print("[policy] served crossdomain.xml")
    except (asyncio.TimeoutError, ConnectionError):
        pass
    finally:
        writer.close()

async def main():
    if WS_BRIDGE_TOKEN:
        print(f"WS bridge auth enabled (token configured)")
    else:
        print(f"WARNING: WS bridge auth disabled (set WS_BRIDGE_TOKEN env var)")
    print(f"WS bridge listening on 0.0.0.0:{BRIDGE_PORT}")
    print(f"  /realtime/login -> 127.0.0.1:{LOGIN_PORT}")
    print(f"  /realtime/game  -> 127.0.0.1:{GAME_PORT}")
    crossdomain = await asyncio.start_server(handle_crossdomain, "0.0.0.0", 843)
    async with websockets.serve(handle_connection, "0.0.0.0", BRIDGE_PORT), crossdomain:
        print(f"  Crossdomain policy on port 843")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
