#!/usr/bin/env bash
set -u

run() {
  local title="$1"
  shift
  printf '\n## %s\n' "$title"
  "$@" 2>&1 || printf 'COMMAND_UNAVAILABLE_OR_FAILED\n'
}

run "OS" bash -lc 'uname -a; cat /etc/os-release'
run "CPU" bash -lc 'nproc; lscpu | sed -n "1,20p"'
run "MEMORY" free -h
run "DISK" df -h
run "BLOCK DEVICES" lsblk
run "LOAD" uptime
run "LISTENING PORTS" ss -lntup
run "RUNNING SERVICES" systemctl --type=service --state=running
run "NODE" node --version
run "NPM" npm --version
run "PYTHON" python3 --version
run "PIP" python3 -m pip --version
run "MYSQL CLIENT" mysql --version
run "NGINX" nginx -v
run "APACHE" apache2 -v
run "CADDY" caddy version
run "PM2" pm2 list
run "CRON" bash -lc 'for user in root "$USER"; do crontab -l -u "$user" 2>/dev/null || true; done'
run "SYSTEMD TIMERS" systemctl list-timers --all

