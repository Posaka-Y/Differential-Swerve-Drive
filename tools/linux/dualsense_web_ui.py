#!/usr/bin/env python3
"""Local, motor-disconnected DualSense preview Web UI."""

from __future__ import annotations

import argparse
import json
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dualsense_control import ControlConfig, DualSenseMapper, DualSenseReader


INDEX_HTML = r"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DualSense Control Preview</title>
  <style>
    :root { color-scheme: dark; --bg:#080c12; --panel:#111925; --line:#26354a;
      --text:#edf5ff; --muted:#8ca0b8; --cyan:#48d7ff; --green:#4cf3a2;
      --amber:#ffc857; --red:#ff5f6d; }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; color:var(--text); background:
      radial-gradient(circle at 20% 0%, #152840 0, transparent 32rem), var(--bg);
      font:15px/1.45 system-ui, sans-serif; }
    main { width:min(1100px, calc(100% - 28px)); margin:24px auto 50px; }
    header { display:flex; gap:18px; align-items:center; justify-content:space-between;
      margin-bottom:18px; }
    h1 { margin:0; font-size:clamp(22px, 3vw, 34px); letter-spacing:.02em; }
    .tag { padding:7px 11px; border:1px solid var(--amber); color:var(--amber);
      border-radius:999px; font-weight:750; white-space:nowrap; }
    .grid { display:grid; grid-template-columns:repeat(12, 1fr); gap:14px; }
    .card { grid-column:span 4; min-height:150px; padding:18px;
      border:1px solid var(--line); border-radius:16px; background:color-mix(in srgb, var(--panel) 92%, transparent);
      box-shadow:0 16px 45px #0006; }
    .wide { grid-column:span 8; } .full { grid-column:1 / -1; }
    h2 { margin:0 0 14px; color:var(--muted); font-size:12px; text-transform:uppercase;
      letter-spacing:.16em; }
    .status-row { display:flex; align-items:center; gap:10px; }
    .dot { width:12px; height:12px; border-radius:50%; background:var(--red);
      box-shadow:0 0 15px currentColor; }
    .dot.ok { color:var(--green); background:var(--green); }
    .big { font-size:26px; font-weight:800; }
    .muted { color:var(--muted); }
    .sticks { display:flex; gap:30px; align-items:center; justify-content:center; flex-wrap:wrap; }
    .stick-wrap { text-align:center; color:var(--muted); }
    .stick { position:relative; width:142px; aspect-ratio:1; margin:7px auto;
      border:1px solid var(--line); border-radius:50%; background:
      linear-gradient(transparent 49.5%, #33465d 50%, transparent 50.5%),
      linear-gradient(90deg, transparent 49.5%, #33465d 50%, transparent 50.5%), #0b111a; }
    .puck { position:absolute; width:22px; height:22px; left:60px; top:60px;
      border-radius:50%; background:var(--cyan); box-shadow:0 0 22px #48d7ffbb;
      transition:transform 45ms linear; }
    .bar-label { display:grid; grid-template-columns:82px 1fr 48px; align-items:center;
      gap:10px; margin:10px 0; }
    .bar { height:10px; overflow:hidden; border-radius:999px; background:#080d14; }
    .fill { height:100%; width:0; border-radius:inherit; background:linear-gradient(90deg,var(--cyan),var(--green)); }
    .command { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
    .metric { padding:12px; border:1px solid var(--line); border-radius:12px; background:#0a1018; }
    .metric strong { display:block; margin-top:3px; font-size:22px; font-variant-numeric:tabular-nums; }
    .pill { display:inline-flex; align-items:center; min-width:90px; justify-content:center;
      margin:3px 5px 3px 0; padding:8px 12px; border-radius:9px; border:1px solid var(--line);
      color:var(--muted); font-weight:800; }
    .pill.on { color:#07150f; border-color:var(--green); background:var(--green); }
    .warn { color:var(--amber); }
    code { color:#bad2ea; }
    @media(max-width:780px) { .card,.wide { grid-column:1 / -1; } header { align-items:flex-start; }
      .command { grid-template-columns:1fr; } }
  </style>
</head>
<body><main>
  <header><div><h1>DualSense Control Preview</h1><div class="muted">Differential Swerve Drive / mini PC input layer</div></div>
    <div class="tag">NO MOTOR OUTPUT</div></header>
  <div class="grid">
    <section class="card"><h2>Connection</h2><div class="status-row"><span id="dot" class="dot"></span>
      <span id="connection" class="big">SEARCHING</span></div><p id="device" class="muted">DualSenseを待っています</p></section>
    <section class="card wide"><h2>Safety gate</h2><span id="deadman" class="pill">R1 DEADMAN</span>
      <span id="options" class="pill">OPTIONS</span><span id="ps" class="pill">PS</span>
      <p id="gate" class="warn">R1を押している間だけ指令値を生成します。</p></section>
    <section class="card wide"><h2>Stick input</h2><div class="sticks">
      <div class="stick-wrap">LEFT / translation<div class="stick"><span id="leftPuck" class="puck"></span></div><code id="leftValue">0.00, 0.00</code></div>
      <div class="stick-wrap">RIGHT / yaw<div class="stick"><span id="rightPuck" class="puck"></span></div><code id="rightValue">0.00, 0.00</code></div>
    </div></section>
    <section class="card"><h2>Triggers</h2>
      <div class="bar-label"><span>L2</span><div class="bar"><div id="l2" class="fill"></div></div><code id="l2v">0%</code></div>
      <div class="bar-label"><span>R2 speed</span><div class="bar"><div id="r2" class="fill"></div></div><code id="r2v">0%</code></div>
      <p class="muted">速度倍率: <strong id="scale">25%</strong></p></section>
    <section class="card full"><h2>Body twist preview</h2><div class="command">
      <div class="metric"><span class="muted">+X forward</span><strong id="vx">0.000 m/s</strong></div>
      <div class="metric"><span class="muted">+Y left</span><strong id="vy">0.000 m/s</strong></div>
      <div class="metric"><span class="muted">+ω CCW</span><strong id="omega">0.000 rad/s</strong></div>
    </div><p class="muted">R2は25–100%の速度倍率。R1解放・Bluetooth切断時は3軸すべて即0になります。</p></section>
  </div>
</main>
<script>
const $ = id => document.getElementById(id);
const pct = x => `${Math.round(x * 100)}%`;
const pill = (id,on) => $(id).classList.toggle('on', !!on);
function puck(id,x,y){ $(id).style.transform=`translate(${x*52}px,${y*52}px)`; }
async function update(){
  try {
    const s=await fetch('/api/state',{cache:'no-store'}).then(r=>r.json());
    $('dot').classList.toggle('ok',s.connected);
    $('connection').textContent=s.connected ? `${s.transport} CONNECTED` : 'DISCONNECTED';
    $('device').textContent=s.connected ? `${s.device_name} · ${s.controller_id||s.device_path}` : 'DualSenseを待っています';
    pill('deadman',s.deadman); pill('options',s.options); pill('ps',s.ps);
    $('gate').textContent=s.command_active ? 'COMMAND ACTIVE（プレビューのみ）' : 'R1を押している間だけ指令値を生成します。';
    puck('leftPuck',s.left_x,s.left_y); puck('rightPuck',s.right_x,s.right_y);
    $('leftValue').textContent=`${s.left_x.toFixed(2)}, ${s.left_y.toFixed(2)}`;
    $('rightValue').textContent=`${s.right_x.toFixed(2)}, ${s.right_y.toFixed(2)}`;
    $('l2').style.width=pct(s.left_trigger); $('r2').style.width=pct(s.right_trigger);
    $('l2v').textContent=pct(s.left_trigger); $('r2v').textContent=pct(s.right_trigger); $('scale').textContent=pct(s.speed_scale);
    $('vx').textContent=`${s.vx_mps.toFixed(3)} m/s`; $('vy').textContent=`${s.vy_mps.toFixed(3)} m/s`;
    $('omega').textContent=`${s.omega_rad_s.toFixed(3)} rad/s`;
  } catch(e) { $('connection').textContent='UI ERROR'; }
  setTimeout(update,50);
}
update();
</script></body></html>"""


def make_handler(reader: DualSenseReader):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib API name
            if self.path == "/" or self.path.startswith("/?"):
                payload = INDEX_HTML.encode("utf-8")
                content_type = "text/html; charset=utf-8"
            elif self.path == "/api/state":
                payload = json.dumps(reader.snapshot().to_dict(), separators=(",", ":")).encode()
                content_type = "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *_args) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Local DualSense input preview Web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--preferred-id", default="4c:b9:9b:8a:c3:07")
    parser.add_argument("--max-v-mps", type=float, default=1.0)
    parser.add_argument("--max-omega-rad-s", type=float, default=3.0)
    args = parser.parse_args()

    config = ControlConfig(
        max_linear_speed_mps=max(0.0, args.max_v_mps),
        max_angular_speed_rad_s=max(0.0, args.max_omega_rad_s),
    )
    reader = DualSenseReader(DualSenseMapper(config), preferred_id=args.preferred_id)
    reader.start()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(reader))

    def stop_server(_signum, _frame) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)
    print(f"DualSense preview: http://{args.host}:{args.port}", flush=True)
    print("Preview only: no CAN, serial, or motor output is implemented.", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
        reader.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
