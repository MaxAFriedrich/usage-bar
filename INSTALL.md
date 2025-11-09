# Quick Installation Guide

## Prerequisites

Install system dependencies:

```bash
# Debian/Ubuntu
sudo apt-get install build-essential libx11-dev libxinerama-dev python3 python3-pip

# Fedora/RHEL
sudo dnf install gcc libX11-devel libXinerama-devel python3 python3-pip

# Arch Linux
sudo pacman -S base-devel libx11 libxinerama python python-pip
```

Install Python dependencies:

```bash
pip install pyyaml
# or with Poetry
poetry install
```

## Build

```bash
make
```

## Install as System Services

```bash
make install
systemctl --user enable --now usage-bar-monitor.service
systemctl --user enable --now usage-bar-gui.service
```

## Manual Testing (Development)

Terminal 1:
```bash
python3 input_monitor.py
# or: sudo python3 input_monitor.py  (if permission issues)
```

Terminal 2:
```bash
./overspeed_monitor
```

## Check Status

```bash
systemctl --user status usage-bar-monitor.service
systemctl --user status usage-bar-gui.service
```

## Uninstall

```bash
make uninstall
```

See [README.md](README.md) for full documentation.
