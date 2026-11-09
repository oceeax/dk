#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baeb.py —— 只做一件事：
 API 读电量 → 每 15 秒写 battery1.csv（不碰 HTML、不发飞书）
<< 127.0.0.1:8766/api/battery 调试接口，返回实时电量 JSON
"""

import csv
import json
import subprocess
import threading
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path("/opt/bat/hz")
CSV_FILE = BASE_DIR / "battery1.csv"

POWER_SUPPLY_DIR = Path("/sys/class/power_supply")
SAMPLE_INTERVAL = 15
MAX_RECORDS = 30
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8766

STATUS_TEXT = {
    "charging": "充电中",
    "full": "已充满",
    "discharging": "未充电",
    "not charging": "未充电",
    "unknown": "未知",
}


def find_battery_dir():
    for p in sorted(POWER_SUPPLY_DIR.glob("BAT*")):
        if (p / "capacity").exists():
            return p
    return None


BATTERY_DIR = find_battery_dir()


def read_battery():
    """三级回退：/sys → termux-battery-status → dumpsys"""
    # 1. /sys/class/power_supply/BAT*/capacity
    if BATTERY_DIR is not None:
        try:
            percent = int((BATTERY_DIR / "capacity").read_text().strip())
            try:
                status_raw = (BATTERY_DIR / "status").read_text().strip()
            except OSError:
                status_raw = "Unknown"
            return percent, status_raw
        except Exception:
            pass

    # 2. termux-battery-status
    try:
        out = subprocess.check_output(["termux-battery-status"], text=True, timeout=3)
        data = json.loads(out)
        if "percentage" in data:
            return int(data["percentage"]), data.get("status", "Unknown")
    except Exception:
        pass

    # 3. dumpsys battery
    try:
        out = subprocess.check_output(["dumpsys", "battery"], text=True, timeout=3)
        level = None
        status_code = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("level:"):
                level = int(line.split(":")[1].strip())
            elif line.startswith("status:"):
                status_code = int(line.split(":")[1].strip())
        if level is not None:
            status_raw = "Charging" if status_code == 2 else ("Full" if status_code == 5 else "Discharging")
            return level, status_raw
    except Exception:
        pass

    raise RuntimeError("所有电池获取方式均失败（/sys、termux-api、dumpsys）")


def append_record(percent, status_raw):
    charge_status = STATUS_TEXT.get(status_raw.lower(), status_raw)
    now = datetime.now().astimezone()
    timestamp = now.strftime("%Y年%m月%d日 %H时%M分%S秒") + now.strftime(" %z")

    new_file = not CSV_FILE.exists() or CSV_FILE.stat().st_size == 0
    try:
        with CSV_FILE.open("a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["时间戳", "电量百分比", "充电状态"])
            writer.writerow([timestamp, percent, charge_status])
    except Exception as e:
        print(f"[写入CSV失败] {e}", flush=True)
        return

    try:
        with CSV_FILE.open("r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        if len(lines) > MAX_RECORDS + 1:
            lines = [lines[0]] + lines[-MAX_RECORDS:]
            with CSV_FILE.open("w", encoding="utf-8-sig") as f:
                f.writelines(lines)
    except Exception as e:
        print(f"[裁剪CSV失败] {e}", flush=True)

    print(f"[{timestamp}] 电量 {percent}% | {charge_status} -> {CSV_FILE}", flush=True)


def collector_loop():
    while True:
        try:
            percent, status_raw = read_battery()
            if 0 <= percent <= 100:
                append_record(percent, status_raw)
            else:
                print(f"[采集] 电量超出范围：{percent}", flush=True)
        except Exception as e:
            print(f"[采集失败] {e}", flush=True)
            traceback.print_exc()
        time.sleep(SAMPLE_INTERVAL)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """只提供 /api/battery 调试接口，不做 HTML、不接收 POST"""
        if urlparse(self.path).path == "/api/battery":
            try:
                percent, status_raw = read_battery()
                payload = {
                    "level": percent,
                    "charging": status_raw.lower() in ("charging", "full"),
                    "status": status_raw,
                    "status_text": STATUS_TEXT.get(status_raw.lower(), status_raw),
                    "timestamp": datetime.now().astimezone().isoformat(),
                }
                self._send(200, json.dumps(payload, ensure_ascii=False))
            except Exception as e:
                self._send(500, json.dumps({"error": str(e)}, ensure_ascii=False))
            return
        self.send_error(404)

    def log_message(self, fmt, *args):
        return  # 静默


if __name__ == "__main__":
    print("=" * 60)
    print("baeb.py —— 系统电量采集 → battery1.csv")
    print(f"CSV：   {CSV_FILE.resolve()}")
    print(f"间隔：   {SAMPLE_INTERVAL}s   保留：{MAX_RECORDS} 条")
    print(f"调试：   GET http://{LISTEN_HOST}:{LISTEN_PORT}/api/battery")
    if BATTERY_DIR is None:
        print("未找到 /sys/class/power_supply/BAT*，将尝试 Termux API / dumpsys")
    else:
        print(f"电池路径：{BATTERY_DIR}")
    print("=" * 60)

    t = threading.Thread(target=collector_loop, daemon=True)
    t.start()

    try:
        ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler).serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"[错误] 端口 {LISTEN_PORT} 已被占用，执行: fuser -k {LISTEN_PORT}/tcp")
        else:
            raise
