#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
battery_web.py
1) GET  /          → 返回 battery.html（手机浏览器打开）
2) POST /battery   → 写 battery2.csv
3) 后台线程每 20s  → 读 battery1.csv + battery2.csv → 发飞书
"""

import csv
import datetime
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE_DIR   = Path("/opt/bat/hz")
HTML_FILE  = BASE_DIR / "battery.html"
CSV_FILE   = BASE_DIR / "battery2.csv"     # 本脚本生成
BATTERY1   = BASE_DIR / "battery1.csv"     # baeb.py 生成，只读
STATE_FILE = BASE_DIR / "state.json"

FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/b8dc958f-2d42-4341-b90c-54abaa81b07b"
MAX_RECORDS = 30
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8765
SEND_INTERVAL = 10

def format_duration(seconds):
    if seconds <= 0:
        return "0微秒"
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    micros = int((seconds % 1) * 1000000)
    parts = []
    if days > 0: parts.append(f"{days}天")
    if hours > 0: parts.append(f"{hours}小时")
    if minutes > 0: parts.append(f"{minutes}分")
    if secs > 0 or len(parts) == 0: parts.append(f"{secs}秒")
    parts.append(f"{micros}微秒")
    return "".join(parts)


def get_last_battery_info(file_path):
    if not os.path.exists(file_path):
        return "未找到电量日志文件"
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            if not lines:
                return "日志文件为空"
            return lines[-1].strip()
    except Exception as e:
        return f"读取失败({e})"


def load_state():
    default_state = {
        "counter": 1,                # 序号
        "last_duration": 0.0,        # 上次飞书请求的耗时
        "error_count": 0,            # 累计异常次数
        "start_time": 0.0,           # 启动时间
        "total_downtime": 0.0,       # 累计故障时间（已结算的）
        "first_fail_ts": 0.0,        # 本次开始失败的时间戳
        "last_offline_duration": 0.0 # 上次断网（飞书失败）总时长
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k in default_state:
                    if k not in data:
                        data[k] = default_state[k]
                return data
        except Exception as e:
            print(f"⚠️ 状态文件读取失败，将重置: {e}", flush=True)
            return default_state
    return default_state


def save_state(state):
    try:
        tmp = str(STATE_FILE) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f"❌ [严重] 状态文件保存失败，请检查目录权限: {e}", flush=True)


def append_record(percent, is_charging):
    """POST /battery 写入 battery2.csv"""
    status = "充电中" if is_charging else "未充电"
    now = datetime.datetime.now().astimezone()
    ts = now.strftime("%Y年%m月%d日 %H时%M分%S秒") + now.strftime(" %z")

    new_file = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0
    try:
        with CSV_FILE.open("a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["时间戳", "电量百分比", "充电状态"])
            writer.writerow([ts, percent, status])
    except Exception as e:
        print(f"[写入失败] {CSV_FILE.name}: {e}", flush=True)
        return

    try:
        with CSV_FILE.open("r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        if len(lines) > MAX_RECORDS + 1:
            lines = [lines[0]] + lines[-MAX_RECORDS:]
            with CSV_FILE.open("w", encoding="utf-8-sig") as f:
                f.writelines(lines)
    except Exception as e:
        print(f"[裁剪失败] {CSV_FILE.name}: {e}", flush=True)

    print(f"[{ts}] 电量 {percent}% | {status} -> battery2.csv", flush=True)


def send_feishu():
    now_dt = datetime.datetime.now()
    now_str = now_dt.strftime('%Y年%m月%d日 %H:%M:%S')
    now_ts = time.time()
    
    # 每次强制读取最新状态
    state = load_state()
    
    # 初始化启动时间
    if state["start_time"] == 0.0:
        state["start_time"] = now_ts
        state["total_downtime"] = 0.0
        save_state(state)

    # ===== 核心修复：基于总时间做减法 =====
    # 总时长 = 当前时间 - 启动时间
    total_elapsed = now_ts - state["start_time"]
    
    # 如果当前正处于断网中，把正在断网的时长也加上用于展示
    current_fail_duration = 0.0
    if state["first_fail_ts"] > 0:
        current_fail_duration = now_ts - state["first_fail_ts"]
        
    # 展示用的累计断网时长 = 历史已结算断网 + 当前正在断网
    display_downtime = state["total_downtime"] + current_fail_duration
    
    # 展示用的累计运行时长 = 总时长 - 累计断网时长
    # 这样能保证：累计运行 + 累计断网 === 当前时间 - 启动时间，一分一秒都不差
    display_uptime = total_elapsed - display_downtime

    uptime_str = format_duration(display_uptime)
    downtime_str = format_duration(display_downtime)
    start_str = datetime.datetime.fromtimestamp(state["start_time"]).strftime('%Y年%m月%d日 %H:%M:%S')

    # 处理“上次断网”和“当前断网”的展示
    offline_msg = ""
    if state["first_fail_ts"] > 0:
        offline_msg = f"\n⚠️ 当前飞书断网: {format_duration(current_fail_duration)}"
    elif state["last_offline_duration"] > 0:
        offline_msg = f"\n⚠️ 上次断网: {format_duration(state['last_offline_duration'])}"

    error_msg = f"\n📊 累计异常: {state['error_count']} 次"
    
    duration_msg = ""
    if state["last_duration"] > 0:
        duration_msg = f"\n⚡ 上次联网耗时: {int(state['last_duration'] * 1000000)} 微秒"

    b1 = get_last_battery_info(BATTERY1)
    b2 = get_last_battery_info(CSV_FILE)

    text = (
        f"📱 手机服务器状态\n"
        f"当前时间: {now_str}\n"
        f"启动时间: {start_str}\n"
        f"⏱️ 累计运行: {uptime_str}\n"
        f"☕ 累计断网: {downtime_str}\n"
        f"🔋 电池①(系统): {b1}\n"
        f"🔋 电池②(网页): {b2}\n"
        f"序号: {state['counter']}\n"
        f"状态: 运行正常{offline_msg}{error_msg}{duration_msg}"
    )
    payload = {"msg_type": "text", "content": {"text": text}}

    # 发送请求
    req_start = time.time()
    try:
        r = requests.post(FEISHU_WEBHOOK, json=payload, timeout=2)
        r.raise_for_status()
        req_end = time.time()
        
        # ===== 发送成功 =====
        state["last_duration"] = req_end - req_start
        state["counter"] += 1
        
        # 如果之前处于断网状态，现在恢复了，把这段时长实打实地“结算”到总断网时间里
        if state["first_fail_ts"] > 0:
            offline_duration = req_end - state["first_fail_ts"]
            state["last_offline_duration"] = offline_duration
            state["total_downtime"] += offline_duration 
            state["first_fail_ts"] = 0.0
            
        save_state(state)
        print(f"[{now_str}] 飞书成功 | 序号:{state['counter']-1} | 累计异常:{state['error_count']}", flush=True)
        
    except Exception as e:
        # ===== 发送失败 =====
        state["error_count"] += 1
        if state["first_fail_ts"] == 0.0:
            # 如果这是第一次失败，记录开始失败的时间
            state["first_fail_ts"] = now_ts 
            
        save_state(state)
        print(f"[{now_str}] 飞书失败: {e} | 累计异常:{state['error_count']}", flush=True)


def feishu_loop():
    print(f"飞书上报线程启动，每 {SEND_INTERVAL}s 一次...")
    while True:
        send_feishu()
        time.sleep(SEND_INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html", "/battery.html"):
            if HTML_FILE.exists():
                self._send(200, HTML_FILE.read_bytes(), "text/html; charset=utf-8")
            else:
                self._send(404, f"battery.html not found: {HTML_FILE}")
        else:
            self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != "/battery":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8").strip()
            data = json.loads(raw)
            percent = int(data.get("level"))
            if not 0 <= percent <= 100:
                raise ValueError("电量必须在 0~100 之间")
            is_charging = bool(data.get("charging"))
            append_record(percent, is_charging)
            self._send(200, "OK")
        except json.JSONDecodeError:
            self._send(400, "JSON 格式错误")
        except Exception as e:
            self._send(400, str(e))

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.log_date_time_string(), fmt % args), flush=True)


if __name__ == "__main__":
    print("=" * 60)
    print("battery_web.py —— HTML + battery2.csv + 飞书")
    print(f"页面：  GET  http://{LISTEN_HOST}:{LISTEN_PORT}/")
    print(f"上报：  POST http://{LISTEN_HOST}:{LISTEN_PORT}/battery")
    print(f"HTML：  {HTML_FILE}")
    print(f"写：    {CSV_FILE}  (最多 {MAX_RECORDS} 条)")
    print(f"读：    {BATTERY1}")
    print(f"飞书：  每 {SEND_INTERVAL}s 一次")
    print("=" * 60)

    t = threading.Thread(target=feishu_loop, daemon=True)
    t.start()

    try:
        ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"[错误] 端口 {LISTEN_PORT} 已被占用，执行: fuser -k {LISTEN_PORT}/tcp")
        else:
            raise




