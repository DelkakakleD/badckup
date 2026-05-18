import asyncio
import struct

POLICY_FILE = '''<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
    <allow-access-from domain="*" to-ports="*"/>
</cross-domain-policy>
'''
POLICY_REQUEST = b"<policy-file-request/>\x00"

async def handle_client(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(1024), timeout=5)
        if POLICY_REQUEST in data or b"policy" in data.lower():
            writer.write(POLICY_FILE.encode() + b"\x00")
            await writer.drain()
    except (asyncio.TimeoutError, ConnectionError):
        pass
    finally:
        writer.close()

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 843)
    print("Crossdomain policy listener on port 843")
    async with server:
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
