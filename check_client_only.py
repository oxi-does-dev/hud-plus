#!/usr/bin/env python3
"""Fails when HUD+'s sources could stop being a display-only, client-side mod.

HUD+ is compiled into the client, so its modules can reach everything the game
can: packets, the connection, the player's own actions. The server must keep
seeing a plain Horizon client, so this scans the mixin sources for the calls
that would change that. Run it before packaging:

    python3 check_client_only.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = sorted((ROOT / "mixins" / "hud_plus").glob("*.rs"))

# Sending: packets, the connection, the mod list a server asks for, sockets.
NETWORK = [
    r"\bServerbound\b",
    r"\bClientbound\b",
    r"\bCustomPayload\b",
    r"\bClientInformation\b",
    r"\bmod_net\b",
    r"\bmod_list\b",
    r"\bTcpStream\b",
    r"\bUdpSocket\b",
    r"\bSocketAddr\b",
    r"\bsend_packet\b",
    r"\bsend_[a-z_]+\b",
    r"\bPacket\b",
    r"\bconnect\s*\(",
    r"\.send\s*\(",
]

# Acting for the player: moves, attacks, uses, drops, selection.
PLAYER = [
    r"\.set_position\s*\(",
    r"\.set_pos\s*\(",
    r"\.teleport\s*\(",
    r"\.set_velocity\s*\(",
    r"\.attack\s*\(",
    r"\.use_item\s*\(",
    r"\.swing_hand\s*\(",
    r"\.drop_stack\s*\(",
    r"\.select_slot\s*\(",
]

# Running another program is the same as sending: the mod must not.
PROCESS = [r"\bstd::process\b", r"\bCommand::new\s*\("]

RULES = [(NETWORK, "network"), (PLAYER, "player action"), (PROCESS, "process")]


def code_only(text):
    """`text` without comments and string literals, so words in prose or log
    messages cannot trip a rule (nor hide it)."""
    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if text.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif text.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
        elif text[i] == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def main():
    if not SOURCES:
        sys.exit(f"no sources under {ROOT / 'mixins' / 'hud_plus'}")
    violations = []
    for path in SOURCES:
        code = code_only(path.read_text())
        for patterns, kind in RULES:
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    line = code.count("\n", 0, match.start()) + 1
                    violations.append(
                        {
                            "file": path.name,
                            "line": line,
                            "kind": kind,
                            "code": match.group(0),
                        }
                    )
    result = {
        "ok": not violations,
        "files": len(SOURCES),
        "rules": sum(len(p) for p, _ in RULES),
        "violations": violations,
    }
    print(json.dumps(result, indent=2))
    if violations:
        print(
            "\nHUD+ must stay display-only: the server has to see a plain "
            "Horizon client. Remove the call above, or prove in review that it "
            "never sends, moves, attacks or uses.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
