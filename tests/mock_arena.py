#!/usr/bin/env python3
"""本機模擬伺服器：用公開對戰的真實決策點，模仿官方 owner-hosted 的 API，測執行器用。

模仿的端點：POST /tcg/join、GET /tcg/pending-actions、POST /tcg/action、GET /tcg/battle/{id}
刻意安排的情境：
  - 每次加入都要帶牌組（沒帶 → 422，跟真伺服器一樣）；牌組鎖定後帶不同牌組 → 409 payload_locked
  - 每隔幾次詢問就回「輪到對手」（pending 空、activeMatches 有東西）
  - 故障注入：第 4 次詢問回 500、第 5 個動作請求直接斷線（測重試與冪等重送）
  - 單數場在「我們這一步」結束（action 回 Settled）；雙數場在「對手那一步」結束（我們收不到結束回應）
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

MATCH_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "matches"
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
DECISIONS_PER_MATCH = 25  # 每場只取前 25 個決策點，測試跑得快


def load_script():
    """從一場公開對戰取出「贏家」那一方的決策點序列。"""
    path = (sorted(MATCH_DIR.glob("*.json")) or sorted(FIXTURE_DIR.glob("*.json")))[0]
    match = json.loads(path.read_text())
    winner = match["battle"]["result"]["winnerAgentId"]
    script = []
    for dp in match["decisions"]["decisionPoints"]:
        player = dp["perPlayer"].get(winner) or {}
        if player.get("legalActions"):
            script.append({"obs": player["obs"], "legalActions": player["legalActions"]})
    return script[:DECISIONS_PER_MATCH]


class MockArena:
    def __init__(self):
        self.script = load_script()
        self.lock = threading.Lock()
        self.deck = None
        self.match_no = 0
        self.current = None        # {"id", "i", "polls", "status"}
        self.status = {}           # matchId → Active/Settled
        self.joins = 0
        self.actions = []

    def join(self, body):
        self.joins += 1
        if self.joins == 2 and not getattr(self, "busy_sent", False):
            self.busy_sent = True
            return 409, {"error": "arena_transaction_busy", "message": "Database transaction is busy; retry"}
        payload = body.get("joinPayload")
        # 跟真伺服器一樣（2026-10-17 實測）：每次加入都要帶 60 張牌組；牌組鎖定後帶不同的 → 409
        if not isinstance(payload, list) or len(payload) != 60:
            return 422, {"error": "invalid_join_payload", "message": "joinPayload must be a deck of 60"}
        if self.deck is None:
            self.deck = payload
        elif payload != self.deck:
            return 409, {"error": "payload_locked"}
        if self.current and self.status[self.current["id"]] == "Active":
            return 200, {"status": "matched", "matchId": self.current["id"]}
        self.match_no += 1
        match_id = f"mock-match-{self.match_no}"
        self.current = {"id": match_id, "i": 0, "polls": 0}
        self.status[match_id] = "Active"
        return 200, {"status": "matched", "matchId": match_id}

    def pending(self):
        self.polls = getattr(self, "polls", 0) + 1
        if self.polls == 4:  # 注入：詢問時回一次 500
            return None
        cur = self.current
        if not cur or self.status[cur["id"]] != "Active":
            return {"pending": [], "activeMatches": []}
        cur["polls"] += 1
        if cur["polls"] % 3 == 0:  # 模擬「輪到對手」
            return {"pending": [], "activeMatches": [{"matchId": cur["id"]}]}
        if cur["i"] >= len(self.script):  # 雙數場：我們的最後一步之後，對手那一步結束了比賽
            self.status[cur["id"]] = "Settled"
            return {"pending": [], "activeMatches": []}
        dp = self.script[cur["i"]]
        return {"pending": [{"matchId": cur["id"], "seq": cur["i"], "deadline": int(time.time() * 1000) + 30000,
                             "obs": dp["obs"], "legalActions": dp["legalActions"]}],
                "activeMatches": [{"matchId": cur["id"]}]}

    def action(self, body):
        cur = self.current
        if not cur or body.get("matchId") != cur["id"] or body.get("seq") != cur["i"]:
            return 409, {"error": "decision point closed"}
        if body.get("action") not in self.script[cur["i"]]["legalActions"]:
            return 422, {"error": "illegal action"}
        self.actions.append(body)
        cur["i"] += 1
        last = cur["i"] >= len(self.script)
        if last and self.match_no % 2 == 1:  # 單數場：在我們這一步結束
            self.status[cur["id"]] = "Settled"
            return 200, {"idempotent": False, "matchStatus": "Settled"}
        return 200, {"idempotent": False, "matchStatus": "Active"}


def make_handler(arena):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, data):
            raw = json.dumps(data).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            path = urlparse(self.path).path
            with arena.lock:
                if path.endswith("/tcg/pending-actions"):
                    data = arena.pending()
                    return self.reply(500, {"error": "internal"}) if data is None else self.reply(200, data)
                if "/tcg/battle/" in path:
                    match_id = path.rsplit("/", 1)[-1]
                    return self.reply(200, {"matchId": match_id, "status": arena.status.get(match_id, "Unknown")})
            self.reply(404, {"error": "not found"})

        def do_POST(self):
            if not self.headers.get("x-arena-api-key"):
                return self.reply(401, {"error": "Missing x-arena-api-key header"})
            path = urlparse(self.path).path
            body = self.body()
            with arena.lock:
                if path.endswith("/tcg/join"):
                    return self.reply(*arena.join(body))
                if path.endswith("/tcg/action"):
                    arena.action_requests = getattr(arena, "action_requests", 0) + 1
                    if arena.action_requests == 5:  # 注入：第 5 個動作請求直接斷線、不回應（模擬網路中斷）
                        self.close_connection = True
                        return
                    return self.reply(*arena.action(body))
            self.reply(404, {"error": "not found"})

    return Handler


def start(port=0):
    arena = MockArena()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(arena))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return arena, server
