#!/bin/bash

DIR="/opt/bat/hz"
PID_DIR="/tmp/bat_monitor_pids"
mkdir -p "\$PID_DIR"

echo "===== 启动目录守护：\$DIR ====="

while true; do
    for file in "\$DIR"/*.py "\$DIR"/*.sh; do
        [ -f "\$file" ] || continue
        name=\$(basename "\$file")
        pidfile="\$PID_DIR/\$name.pid"
        running=0

        if [ -f "\$pidfile" ]; then
            pid=\$(cat "\$pidfile")
            if kill -0 "\$pid" 2>/dev/null; then
                running=1
            else
                rm -f "\$pidfile"
            fi
        fi

        if [ \$running -eq 0 ]; then
            echo "[!] \$name 未运行，正在拉起"
            if [[ "\$name" == *.py ]]; then
                nohup python3 "\$file" > "\$DIR/\$name.log" 2>&1 &
            elif [[ "\$name" == *.sh ]]; then
                nohup bash "\$file" > "\$DIR/\$name.log" 2>&1 &
            fi
            newpid=\$!
            echo "\$newpid" > "\$pidfile"
            echo "[+] \$name PID: \$newpid"
        fi
    done
    sleep 10
done
