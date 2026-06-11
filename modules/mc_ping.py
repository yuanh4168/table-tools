"""
Minecraft 服务器状态查询（完整版）
支持：SRV解析、延迟测量、favicon图标、Mod信息、自动协议探测。
兼容原 run(host, port) 调用方式。
"""

import struct
import socket
import json
import time

try:
    import dns.resolver
    HAS_DNS = True
except ImportError:
    HAS_DNS = False


def _resolve_srv(host):
    """解析 SRV 记录，返回 (新host, 新port)"""
    if not HAS_DNS:
        return host, None
    try:
        answers = dns.resolver.resolve(f'_minecraft._tcp.{host}', 'SRV')
        if answers:
            srv = answers[0]
            new_host = str(srv.target).rstrip('.')
            new_port = srv.port
            return new_host, new_port
    except Exception:
        pass
    return host, None  # port=None 表示未改变


def _read_varint(sock):
    result = 0
    shift = 0
    while True:
        raw = sock.recv(1)
        if not raw:
            raise ConnectionError("连接中断")
        byte = raw[0]
        result |= (byte & 0x7F) << shift
        shift += 7
        if not (byte & 0x80):
            return result


def _pack_varint(value):
    # 负数转无符号32位
    if value < 0:
        value = (1 << 32) + value
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        out.append(byte)
        if not value:
            return bytes(out)


def _send_packet(sock, packet_id, data=b''):
    packet = bytearray()
    packet.extend(_pack_varint(len(data) + 1))
    packet.extend(_pack_varint(packet_id))
    packet.extend(data)
    sock.send(packet)


def _read_packet(sock):
    _ = _read_varint(sock)          # 包长度（忽略）
    packet_id = _read_varint(sock)
    data_len = _read_varint(sock)
    data = b''
    while len(data) < data_len:
        chunk = sock.recv(data_len - len(data))
        if not chunk:
            break
        data += chunk
    return packet_id, data


def query(host, port=25565, timeout=5):
    """
    查询 Minecraft 服务器状态（纯数据，无打印）。
    返回 dict 或 None（失败时）。
    """
    if port == 25565:
        new_host, new_port = _resolve_srv(host)
        if new_port is not None:
            host, port = new_host, new_port

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))

        # 握手
        hs = bytearray()
        hs.extend(_pack_varint(-1))
        hs.extend(_pack_varint(len(host)))
        hs.extend(host.encode('utf-8'))
        hs.extend(struct.pack('>H', port))
        hs.extend(_pack_varint(1))
        _send_packet(sock, 0x00, hs)

        # 请求状态
        _send_packet(sock, 0x00)

        # 接收
        pid, data = _read_packet(sock)
        if pid != 0x00:
            raise Exception("未收到状态响应包")
        info = json.loads(data.decode('utf-8', errors='replace'))

        # Ping 测延迟
        ping_t = time.time()
        _send_packet(sock, 0x01, struct.pack('>q', int(ping_t * 1000)))
        pid, _ = _read_packet(sock)
        if pid != 0x01:
            raise Exception("未收到 Pong 响应")
        latency = int((time.time() - ping_t) * 1000)
        sock.close()

        version = info.get("version", {}).get("name", "未知")
        protocol = info.get("version", {}).get("protocol", "未知")
        players = info.get("players", {})
        description = info.get("description", "")
        if isinstance(description, dict):
            description = description.get("text", str(description))
        favicon = info.get("favicon", "")
        if favicon and favicon.startswith("data:image/png;base64,"):
            favicon = favicon.split(",", 1)[1]
        modinfo = info.get("modinfo", {})

        return {
            "host": host,
            "port": port,
            "version": version,
            "protocol": protocol,
            "online": players.get("online", 0),
            "max": players.get("max", 0),
            "motd": description,
            "latency": latency,
            "favicon": favicon,
            "players": players.get("sample", []),
            "mod_info": modinfo,
        }
    except socket.timeout:
        return {"error": f"连接超时 ({timeout}s)"}
    except ConnectionRefusedError:
        return {"error": "连接被拒绝 — 服务器可能未运行"}
    except Exception as e:
        return {"error": f"查询失败: {e}"}
    finally:
        if sock:
            sock.close()


def run(host, port=25565, timeout=5):
    """查询 Minecraft 服务器状态并打印（与原接口兼容）"""
    result = query(host, port, timeout)
    if result is None:
        return None

    if result.get("error"):
        print(f"\n    查询 Minecraft 服务器: {host}:{port}\n")
        print(f"  {result['error']}\n")
        return None

    info = result
    print(f"\n    查询 Minecraft 服务器: {info['host']}:{info['port']}\n")
    print(f"  版本:     {info['version']} (协议 {info['protocol']})")
    print(f"  玩家:     {info['online']}/{info['max']} 在线")
    print(f"  MOTD:     {info['motd']}")
    print(f"  延迟:     {info['latency']} ms")
    if info['favicon']:
        print("  图标:     已获取 (Base64)")

    sample = info['players']
    if sample:
        print("\n  在线玩家:")
        for p in sample[:10]:
            print(f"    - {p.get('name', '未知')}")
        if len(sample) > 10:
            print(f"    ... 还有 {len(sample)-10} 人")

    modinfo = info['mod_info']
    if modinfo.get("type"):
        print(f"\n  Mod 类型: {modinfo.get('type')}")
        modlist = modinfo.get("modList", [])
        if modlist:
            print("  Mod 列表 (前5个):")
            for mod in modlist[:5]:
                mn = mod.get("modid", mod.get("name", "未知"))
                print(f"    - {mn}")
            if len(modlist) > 5:
                print(f"    ... 还有 {len(modlist)-5} 个")
    print()
    return info


# 如果你想要一个简单的直接测试入口
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        host = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 25565
        run(host, port)
    else:
        run("localhost", 25565)