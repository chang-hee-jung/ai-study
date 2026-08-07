# -*- coding: utf-8 -*-
"""한 턴을 돌리고, bg-review 데몬 스레드가 끝날 때까지 기다린 뒤 종료한다.

사용: python turn.py <session_id|-> "<질문>"

-q 단발 모드는 응답 직후 프로세스가 죽어 bg-review(daemon=True)가
중간에 잘린다. 여기서 atexit로 붙잡아 매 턴 리뷰가 완주하게 만든다.
"""
import atexit
import os
import sys
import threading
import time

HOME = os.path.join(os.environ["LOCALAPPDATA"], "hermes")
sys.path.insert(0, os.path.join(HOME, "hermes-agent"))
os.chdir(r"F:\ai-study")

SID = sys.argv[1]
QUERY = sys.argv[2]


def wait_for_bg():
    deadline = time.time() + 200
    seen = False
    while time.time() < deadline:
        alive = [t for t in threading.enumerate()
                 if t.name == "bg-review" and t.is_alive()]
        if alive:
            seen = True
            time.sleep(4)
            continue
        if seen:
            print("[turn] bg-review 완주", file=sys.stderr, flush=True)
            return
        time.sleep(2)
    print(f"[turn] bg-review {'미완' if seen else '미발생'}", file=sys.stderr, flush=True)


atexit.register(wait_for_bg)

argv = ["hermes", "chat", "--provider", "copilot", "-m", "gpt-4.1"]
if SID != "-":
    argv += ["--resume", SID]
argv += ["-q", QUERY]
sys.argv = argv

from hermes_cli.main import main as _m
try:
    _m()
except SystemExit:
    pass
