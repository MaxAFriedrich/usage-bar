#!/bin/python3

import subprocess
import sys
import time
import re

# parse arg in form of "2h" or "60m"
if len(sys.argv) != 2:
    print("Usage: pause.py <duration>")
    print("Example: pause.py 2h or pause.py 60m")
    sys.exit(1)

duration_str = sys.argv[1]
match = re.match(r'^(\d+)([hm])$', duration_str)
if not match:
    print("Invalid duration format. Use format like '2h' or '60m'")
    sys.exit(1)

value = int(match.group(1))
unit = match.group(2)

if unit == 'h':
    seconds = value * 3600
elif unit == 'm':
    seconds = value * 60

services = [
    "usage-bar-monitor.service",
    "usage-bar-gui.service"
]

for s in services:
    # does service for --user exist?
    result = subprocess.run(
        ["systemctl", "--user", "list-units", "--all", s],
        capture_output=True,
        text=True
    )
    # if yes, stop
    if s in result.stdout:
        print("Pausing", s)
        subprocess.call(["systemctl", "--user", "stop", s])

# wait arg seconds
print(f"Waiting for {duration_str} ({seconds} seconds)...")
time.sleep(seconds)

# start services back up
for s in services:
    result = subprocess.run(
        ["systemctl", "--user", "list-units", "--all", s],
        capture_output=True,
        text=True
    )
    if s in result.stdout:
        print("Starting", s)
        subprocess.call(["systemctl", "--user", "start", s])
