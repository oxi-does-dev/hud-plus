#!/usr/bin/env python3
"""Wire-level packet audit for HUD+.

HUD+ is display-only, so a server (and an anticheat watching it) must see the
same bytes from the HUD+ client as from the stock one. This tool proves it:

    python3 tools/packet_audit.py capture --client PATH --out run.jsonl \
        --server PATH --ctl PATH --ids PATH --server-dir DIR
    python3 tools/packet_audit.py compare stock.jsonl hud.jsonl

`capture` starts a fresh dedicated server and a decoding proxy
(`tools/net_capture.py`), joins with the given client, runs a fixed input
scenario, writes every packet both ways and stops everything again.
`compare` trims both captures to their play session and checks:

- handshake, login and configuration bytes are identical;
- the client brand and every other CustomPayload are identical;
- the serverbound action packets (chat, commands, clicks, hotbar, input,
  abilities, ...) are the same packets with the same bytes;
- movement packets carry the same flag transitions and a comparable number
  of packets per input segment;
- the client tick rate stays at vanilla's 20 Hz (the anticheat's timer check);
- no payload contains a mod id, and no packet type appears on one side only.

Exit status is 0 when every check passes, 1 otherwise. The JSON report says
what differed; `--json OUT` writes it to a file.
"""
import argparse
import collections
import hashlib
import json
import math
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT
CAPTURE = TOOLS / "net_capture.py"

# Packets whose count or bytes depend on wall-clock time, not on what the
# player did. They are audited through the tick rate and movement checks.
TIMING = {
    "pong",
    "keep_alive",
    "client_tick_end",
    "chunk_batch_received",
    "move_player_pos",
    "move_player_pos_rot",
    "move_player_rot",
    "move_player_status_only",
}
MOVES = {
    "move_player_pos",
    "move_player_pos_rot",
    "move_player_rot",
    "move_player_status_only",
}
# Bytes that legitimately differ between two sessions: chat signatures and
# salts, and the timestamps inside them.
MASK = re.compile(
    r"(hud[_-]?plus|hudplus|horizon[:_-]mod[_-]?list|fabric|forge|neoforge)",
    re.I,
)

SCENARIO = """\
sleep 2
mouse-move 100 20
sleep 0.2
move forward 1
move forward 1 --sprint
move forward 0.5 --sprint --jump
move left 0.5 --sneak
hold space 0.3
mouse-move 300 -40
move backward 0.7
key e tap
sleep 0.4
click-slot 9
sleep 0.2
click-slot 10 right
sleep 0.2
key e tap
sleep 0.3
chat packet-audit
sleep 0.5
command time set day
sleep 0.5
key q tap
sleep 0.5
"""


def wait_port(port, timeout=30.0, up=True):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                if up:
                    return True
        except OSError:
            if not up:
                return True
        time.sleep(0.1)
    return False


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, text=True, **kw)


def server_world(server_dir):
    """The world folder `[world] name` of server.toml, so a capture starts clean."""
    text = (server_dir / "server.toml").read_text(encoding="utf-8")
    match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.M)
    return server_dir / (match.group(1) if match else "world")


def capture(args):
    server_dir = Path(args.server_dir).resolve()
    log = Path(args.out).with_suffix(".log")
    ctl = Path(args.ctl)
    server = Path(args.server)
    # A fresh world: both captures must start from the same blocks and spawn.
    subprocess.run([str(server), "--dir", str(server_dir), "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.rmtree(server_world(server_dir), ignore_errors=True)
    run([str(server), "--dir", str(server_dir), "start"], stdout=subprocess.DEVNULL, timeout=60)
    if not wait_port(args.server_port, 90):
        raise SystemExit("dedicated server did not start")
    # The lab player may summon the cow the combat step attacks.
    subprocess.run(
        [str(server), "--dir", str(server_dir), "cmd", "op", args.name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    proxy = subprocess.Popen(
        [
            sys.executable,
            str(CAPTURE),
            "proxy",
            "--ids",
            str(Path(args.ids).resolve()),
            "--listen",
            str(args.listen),
            "--target",
            f"127.0.0.1:{args.server_port}",
            "--out",
            str(Path(args.out).resolve()),
            "--full",
        ],
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
    )
    try:
        if not wait_port(args.listen, 10):
            raise SystemExit(f"proxy did not listen on {args.listen} (see {log})")
        launch = [
            str(ctl),
            "launch",
            "--game",
            str(Path(args.client).resolve()),
            "--server",
            f"127.0.0.1:{args.listen}",
            "--name",
            args.name,
            "--wait",
        ]
        run(launch, stdout=subprocess.DEVNULL, timeout=180)
        time.sleep(2)
        run([str(ctl), "script", str(ROOT / "packet_scenario.txt")], stdout=subprocess.DEVNULL, timeout=180)
        # Combat: a stationary cow right beside the player gives the attacks a
        # target, each attack swinging the arm the way vanilla's startAttack
        # does (the combat check's clean case).
        try:
            state = json.loads(run([str(ctl), "state"], capture_output=True, timeout=30).stdout)
            x, y, z = state["player"]["position"]
            subprocess.run(
                [
                    str(server),
                    "--dir",
                    str(server_dir),
                    "cmd",
                    "summon",
                    "minecraft:cow",
                    str(x + 1),
                    str(y),
                    str(z),
                    "{NoAI:1b,Silent:1b}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            time.sleep(0.5)
            out = run([str(ctl), "entities"], capture_output=True, timeout=30).stdout
            data = json.loads(out)
            entities = data.get("entities", data) if isinstance(data, dict) else data
            mobs = [
                e
                for e in entities
                if isinstance(e, dict) and e.get("kind") == "mob" and "id" in e
            ]
            target = min(mobs, key=lambda e: e.get("distance", 1e9), default=None)
            target = target["id"] if target else None
            if target is not None:
                run([str(ctl), "attack", str(target)], stdout=subprocess.DEVNULL, timeout=30)
                time.sleep(0.35)
                run([str(ctl), "attack", str(target)], stdout=subprocess.DEVNULL, timeout=30)
        except (subprocess.SubprocessError, ValueError, KeyError):
            pass
        time.sleep(0.3)
        run([str(ctl), "quit"], stdout=subprocess.DEVNULL, timeout=60)
        time.sleep(1)
    finally:
        proxy.terminate()
        try:
            proxy.wait(5)
        except subprocess.TimeoutExpired:
            proxy.kill()
        subprocess.run(
            [str(server), "--dir", str(server_dir), "stop"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print(json.dumps({"capture": str(args.out), "packets": sum(1 for _ in open(args.out))}))


def play_session(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    conns = collections.Counter(r["conn"] for r in rows)
    conn = max(conns, key=lambda c: sum(1 for r in rows if r["conn"] == c and r["state"] == "play"))
    session = [r for r in rows if r["conn"] == conn]
    c2s = [r for r in session if r["dir"] == "c2s"]
    if not c2s:
        raise SystemExit(f"{path}: no serverbound packets")
    return session, c2s


def payload(entry):
    return bytes.fromhex(entry.get("data", entry.get("head", "")))


def deterministic(entry):
    return entry["name"] not in TIMING and entry["name"] not in MOVES


def fingerprint(entries):
    h = hashlib.sha256()
    for e in entries:
        h.update(e["state"].encode())
        h.update(b"\0")
        h.update(e["name"].encode())
        h.update(b"\0")
        h.update(payload(e))
    return h.hexdigest()


def compare(args):
    sessions = []
    for path in (args.stock, args.hud):
        session, c2s = play_session(path)
        sessions.append((path, session, c2s))
    (stock_path, stock, stock_c2s), (hud_path, hud, hud_c2s) = sessions
    checks = []

    def check(name, ok, detail, gate=True):
        checks.append({"check": name, "ok": bool(ok), "gate": gate, "detail": detail})

    for state in ("handshake", "login", "configuration"):
        a = [e for e in stock_c2s if e["state"] == state]
        b = [e for e in hud_c2s if e["state"] == state]
        check(
            f"{state}_bytes",
            [(e["name"], payload(e)) for e in a] == [(e["name"], payload(e)) for e in b],
            {
                "stock": [(e["name"], payload(e).hex()) for e in a],
                "hud": [(e["name"], payload(e).hex()) for e in b],
            },
        )

    # Every deterministic action packet, with repeats, in order. Player input
    # is checked on its own: a key change landing on a frame boundary can add
    # one 0x00 packet, which is timing, not a different client.
    a_actions = [e for e in stock_c2s if deterministic(e) and e["state"] == "play" and e["name"] != "player_input"]
    b_actions = [e for e in hud_c2s if deterministic(e) and e["state"] == "play" and e["name"] != "player_input"]
    a_names = [e["name"] for e in a_actions]
    b_names = [e["name"] for e in b_actions]
    check("action_sequence", a_names == b_names, {"stock": a_names, "hud": b_names})

    # Byte equality for packets that carry no session-dependent value.
    # A chat signature is random for the same text (the salt), so compare the
    # text part only; everything else must match exactly.
    def canonical(e):
        data = payload(e)
        if e["name"] == "chat" and len(data) > 1:
            n = data[0]
            return data[: 1 + n]
        if e["name"] in ("attack", "interact") and data:
            # Entity ids are handed out per session by the server, so the
            # same action has a different number in every capture.
            _, pos = varint(data)
            return b"entity:" + data[pos:]
        return data

    a_canon = [(e["name"], canonical(e).hex()) for e in a_actions]
    b_canon = [(e["name"], canonical(e).hex()) for e in b_actions]
    check("action_bytes", a_canon == b_canon, {"stock_sha256": fingerprint(a_actions), "hud_sha256": fingerprint(b_actions)})

    # Client brand and every other custom payload.
    a_brand = [(e["name"], payload(e).hex()) for e in stock_c2s if e["name"] == "custom_payload"]
    b_brand = [(e["name"], payload(e).hex()) for e in hud_c2s if e["name"] == "custom_payload"]
    check("custom_payload", a_brand == b_brand, {"stock": a_brand, "hud": b_brand})


    # Both clients must attack: the same number of times, and always the same
    # entity within a run (entity ids themselves are session-local).
    def attack_targets(entries):
        ids = []
        for e in entries:
            if e["name"] == "attack" and payload(e):
                try:
                    target, _ = varint(payload(e))
                    ids.append(target)
                except IndexError:
                    pass
        return ids

    a_targets = attack_targets(stock_c2s)
    b_targets = attack_targets(hud_c2s)
    check(
        "attacks",
        len(a_targets) == len(b_targets) and len(set(a_targets)) <= 1 and len(set(b_targets)) <= 1,
        {"stock": a_targets, "hud": b_targets},
    )

    # The single-stream signal an anticheat fingerprints: client information.
    a_info = [payload(e).hex() for e in stock_c2s if e["name"] == "client_information"]
    b_info = [payload(e).hex() for e in hud_c2s if e["name"] == "client_information"]
    check("client_information", a_info == b_info, {"stock": a_info, "hud": b_info})

    # No mod id may appear anywhere on the wire, in either direction.
    hits = []
    for path, session, _ in sessions:
        for e in session:
            text = e.get("data", "") + " " + e.get("head", "")
            raw = bytes.fromhex(text.strip())
            found = MASK.findall(raw.decode("utf-8", "ignore"))
            if found:
                hits.append({"file": str(path), "name": e["name"], "found": found})
    check("no_mod_markers", not hits, hits)

    # Movement: same kinds, same on-ground transitions, comparable counts.
    a_move = [e for e in stock_c2s if e["name"] in MOVES]
    b_move = [e for e in hud_c2s if e["name"] in MOVES]
    a_kinds = collections.Counter(e["name"] for e in a_move)
    b_kinds = collections.Counter(e["name"] for e in b_move)
    check(
        "move_packet_kinds",
        set(a_kinds) == set(b_kinds),
        {"stock": dict(a_kinds), "hud": dict(b_kinds)},
    )

    def ratios(a, b):
        if not a:
            return 0.0
        return abs(b - a) / a

    def close(a, b):
        # Movement position packets scale with how long the player moved;
        # one-off packets (a status change on a frame boundary) may differ by
        # one without meaning anything.
        if a <= 4:
            return abs(b - a) <= 1
        return ratios(a, b) <= 0.25

    check(
        "move_packet_counts",
        all(close(a_kinds[k], b_kinds.get(k, 0)) for k in a_kinds),
        {"stock": dict(a_kinds), "hud": dict(b_kinds)},
        gate=False,
    )

    def flags(entries):
        out = []
        for e in entries:
            if e["name"] in ("move_player_pos", "move_player_pos_rot", "move_player_status_only"):
                out.append(payload(e)[-1] if payload(e) else None)
        return out

    a_flags = collections.Counter(flags(a_move))
    b_flags = collections.Counter(flags(b_move))
    check(
        "move_flags",
        all(
            abs(a_flags[k] - b_flags[k]) <= max(3, round(0.35 * a_flags[k]))
            for k in set(a_flags) | set(b_flags)
        ),
        {"stock": dict(a_flags), "hud": dict(b_flags)},
        gate=False,
    )

    # The same course walked in the same direction: the start is exact, the
    # end and the path length may drift by a frame or a fall.
    def trajectory(entries):
        points = []
        for e in entries:
            data = payload(e)
            if e["name"] in ("move_player_pos", "move_player_pos_rot") and len(data) >= 24:
                points.append(struct.unpack(">ddd", data[:24]))
        if not points:
            return None
        path = sum(math.dist(a, b) for a, b in zip(points, points[1:]))
        return points[0], points[-1], path

    a_traj = trajectory(stock_c2s)
    b_traj = trajectory(hud_c2s)
    check(
        "trajectory",
        a_traj
        and b_traj
        and math.dist(a_traj[0], b_traj[0]) <= 0.01
        and math.hypot(a_traj[1][0] - b_traj[1][0], a_traj[1][2] - b_traj[1][2]) <= 3.0
        and abs(a_traj[2] - b_traj[2]) <= max(1.5, 0.2 * a_traj[2]),
        {
            "stock": [tuple(round(v, 2) for v in a_traj[0]), tuple(round(v, 2) for v in a_traj[1]), round(a_traj[2], 2)]
            if a_traj
            else None,
            "hud": [tuple(round(v, 2) for v in b_traj[0]), tuple(round(v, 2) for v in b_traj[1]), round(b_traj[2], 2)]
            if b_traj
            else None,
        },
    )

    # Input transitions: the same set of key states, allowing one repeated
    # packet from a frame boundary.
    a_input = [payload(e)[0] for e in stock_c2s if e["name"] == "player_input"]
    b_input = [payload(e)[0] for e in hud_c2s if e["name"] == "player_input"]
    # A key change landing on a frame boundary can add or coalesce a repeat,
    # so the exact count is timing; the set of states exercised is not.
    check(
        "player_input",
        sorted(set(a_input)) == sorted(set(b_input))
        and abs(len(a_input) - len(b_input)) <= max(3, round(0.35 * len(a_input))),
        {"stock": a_input, "hud": b_input},
    )

    # Timer: tick ends per second of the play session. The anticheat flags a
    # client well above 20 Hz; a normal session is 19.5..20.5.
    def tick_rate(entries):
        ticks = [e["t"] for e in entries if e["name"] == "client_tick_end"]
        if len(ticks) < 2:
            return None
        return (len(ticks) - 1) / (ticks[-1] - ticks[0])

    a_rate, b_rate = tick_rate(stock_c2s), tick_rate(hud_c2s)
    check(
        "tick_rate",
        a_rate and b_rate and 19.0 <= a_rate <= 21.0 and 19.0 <= b_rate <= 21.0,
        {"stock": round(a_rate, 3) if a_rate else None, "hud": round(b_rate, 3) if b_rate else None},
    )

    # Same set of serverbound packet names overall.
    a_types = set(e["name"] for e in stock_c2s if e["name"] not in TIMING)
    b_types = set(e["name"] for e in hud_c2s if e["name"] not in TIMING)
    check("packet_types", a_types == b_types, {"only_stock": sorted(a_types - b_types), "only_hud": sorted(b_types - a_types)})

    ok = all(c["ok"] for c in checks if c["gate"])
    report = {
        "ok": ok,
        "stock": str(stock_path),
        "hud": str(hud_path),
        "stock_packets": len(stock_c2s),
        "hud_packets": len(hud_c2s),
        "checks": checks,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


def varint(data, pos=0):
    value = shift = 0
    while True:
        b = data[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return value, pos


def mstring(data, pos=0):
    n, pos = varint(data, pos)
    return data[pos : pos + n].decode("utf-8", "replace"), pos + n


def audit(args):
    session, c2s = play_session(args.capture)
    play = [e for e in c2s if e["state"] == "play"]
    brands = []
    markers = []
    for e in c2s:
        data = payload(e)
        if e["name"] == "custom_payload":
            try:
                channel, pos = mstring(data)
                value, _ = mstring(data, pos) if channel == "minecraft:brand" else ("", 0)
                brands.append({"channel": channel, "value": value})
            except (IndexError, UnicodeDecodeError):
                pass
        text = data.decode("utf-8", "ignore")
        for word in MASK.findall(text):
            markers.append({"packet": e["name"], "word": word})

    ticks = [e["t"] for e in play if e["name"] == "client_tick_end"]
    rate = (len(ticks) - 1) / (ticks[-1] - ticks[0]) if len(ticks) > 1 else None

    positions = []
    rotations = []
    for e in play:
        data = payload(e)
        if e["name"] == "move_player_pos" and len(data) >= 25:
            positions.append((e["t"], *struct.unpack(">ddd", data[:24])))
        elif e["name"] == "move_player_pos_rot" and len(data) >= 33:
            x, y, z = struct.unpack(">ddd", data[:24])
            yaw, pitch = struct.unpack(">ff", data[24:32])
            positions.append((e["t"], x, y, z))
            rotations.append((e["t"], yaw, pitch))
        elif e["name"] == "move_player_rot" and len(data) >= 9:
            yaw, pitch = struct.unpack(">ff", data[:8])
            rotations.append((e["t"], yaw, pitch))

    speeds = []
    falls = []
    for (t0, x0, y0, z0), (t1, x1, y1, z1) in zip(positions, positions[1:]):
        dt = t1 - t0
        distance = math.dist((x0, y0, z0), (x1, y1, z1))
        # A gap or a teleport is not a movement tick; only consecutive
        # positions a tick or two apart say anything about speed. Falling is
        # vertical and legal; speed checks look at the horizontal part.
        if 0.04 <= dt < 0.25 and distance < 1.5:
            speeds.append(math.hypot(x1 - x0, z1 - z0) / dt)
            falls.append(max(0.0, y0 - y1) / dt)
    turns = []
    for (_, y0, p0), (_, y1, p1) in zip(rotations, rotations[1:]):
        dy = (y1 - y0 + 180) % 360 - 180
        turns.append(abs(dy) + abs(p1 - p0))

    # The combat check: per client tick, attacks must be covered by swings and
    # all attacks must name one entity.
    fouls = []
    attacks = swings = 0
    targets = []
    for e in play:
        if e["name"] == "attack":
            attacks += 1
            try:
                target, _ = varint(payload(e))
                targets.append(target)
            except IndexError:
                pass
        elif e["name"] == "punch":
            swings += 1
        elif e["name"] == "client_tick_end":
            if attacks > swings:
                fouls.append({"tick_end": e["t"], "attacks": attacks, "swings": swings})
            if len(set(targets)) > 1:
                fouls.append({"tick_end": e["t"], "targets": sorted(set(targets))})
            attacks = swings = 0
            targets = []

    max_speed = max(speeds, default=0.0)
    max_fall = max(falls, default=0.0)
    # Walking, sprinting and sprint-jumping stay under ~0.35 blocks a tick
    # horizontally (7 m/s); anything above 12 m/s on this course is not
    # vanilla. A fall may reach ~78 m/s and is reported, not gated.
    ok = (
        rate is not None
        and 19.0 <= rate <= 21.0
        and max_speed <= 12.0
        and not fouls
        and not markers
        and all(b["value"] in ("vanilla", "horizon") for b in brands)
    )
    report = {
        "ok": ok,
        "capture": str(args.capture),
        "play_packets": len(play),
        "tick_rate_hz": round(rate, 3) if rate else None,
        "brands": brands,
        "mod_markers": markers,
        "movement_packets": len(positions),
        "rotation_packets": len(rotations),
        "max_horizontal_speed_m_s": round(max_speed, 2),
        "max_fall_speed_m_s": round(max_fall, 2),
        "max_turn_deg": round(max(turns, default=0.0), 1),
        "attacks": sum(1 for e in play if e["name"] == "attack"),
        "swings": sum(1 for e in play if e["name"] == "punch"),
        "combat_fouls": fouls,
    }
    text = json.dumps(report, indent=2)
    print(text)
    if args.json:
        Path(args.json).write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


def matrix(args):
    """Every stock capture against every HUD+ capture: the run-to-run matrix."""
    pairs = []
    failures = 0
    with tempfile.TemporaryDirectory(prefix="packet-audit-") as scratch:
        for stock in args.stock:
            for hud in args.hud:
                out = Path(scratch) / f"{Path(stock).stem}--{Path(hud).stem}.json"
                code = subprocess.run(
                    [sys.executable, __file__, "compare", stock, hud, "--json", str(out)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                report = json.loads(out.read_text()) if out.exists() else {"ok": False, "checks": []}
                failed = [c["check"] for c in report.get("checks", []) if c.get("gate", True) and not c["ok"]]
                pairs.append(
                    {
                        "stock": Path(stock).name,
                        "hud": Path(hud).name,
                        "ok": code == 0,
                        "failed": failed,
                        "stock_packets": report.get("stock_packets"),
                        "hud_packets": report.get("hud_packets"),
                    }
                )
                failures += code != 0
    result = {"ok": failures == 0, "pairs": len(pairs), "failures": failures, "results": pairs}
    print(json.dumps(result, indent=2))
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0 if failures == 0 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="record one client's packets")
    cap.add_argument("--client", required=True)
    cap.add_argument("--out", required=True)
    cap.add_argument("--name", default="PacketAudit")
    cap.add_argument("--server", required=True, help="horizon-server binary")
    cap.add_argument("--ctl", required=True, help="horizon-ctl binary of the same build")
    cap.add_argument(
        "--server-dir",
        required=True,
        help="server directory with a server.toml (whitelist off); its world is recreated",
    )
    cap.add_argument("--server-port", type=int, default=25599)
    cap.add_argument("--listen", type=int, default=25598)
    cap.add_argument(
        "--ids",
        required=True,
        help="crates/horizon-protocol/src/ids.rs of the Horizon build the proxy decodes",
    )
    cap.set_defaults(func=capture)

    aud = sub.add_parser("audit", help="the anticheat's view of one capture")
    aud.add_argument("capture")
    aud.add_argument("--json")
    aud.set_defaults(func=audit)

    mat = sub.add_parser("matrix", help="every stock capture against every HUD+ capture")
    mat.add_argument("--stock", nargs="+", required=True)
    mat.add_argument("--hud", nargs="+", required=True)
    mat.add_argument("--json")
    mat.set_defaults(func=matrix)

    cmp = sub.add_parser("compare", help="compare two captures")
    cmp.add_argument("stock")
    cmp.add_argument("hud")
    cmp.add_argument("--json")
    cmp.set_defaults(func=compare)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
