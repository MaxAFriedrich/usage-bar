# Quick Installation Guide

## Prerequisites

Install system dependencies:

```bash
# Debian/Ubuntu
sudo apt-get install build-essential libx11-dev libxinerama-dev python3 python3-yaml

# Fedora/RHEL
sudo dnf install gcc libX11-devel libXinerama-devel python3 python3-pyyaml

# Arch Linux
sudo pacman -S base-devel libx11 libxinerama python python-yaml
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

This will:
- Install binaries to `/usr/local/bin/`
- Install Python modules to `/usr/local/share/usage-bar/python-src/`
- Copy default config to `~/.config/usage-bar/config.yml` (if not exists)
- Install systemd user services

## Manual Testing (Development)

Terminal 1:
```bash
./usage-bar-monitor
# or: sudo ./usage-bar-monitor  (if permission issues)
```

Terminal 2:
```bash
./overspeed_monitor
```

## Configuration

Edit `~/.config/usage-bar/config.yml` to customize settings:
- `break_threshold`: Time before break needed
- `overspeed_threshold`: Events that trigger overspeed
- `overspeed_count_multiplier`: Penalty per overspeed event
- `max_overspeed_penalty`: Maximum penalty time

## Check Status

```bash
systemctl --user status usage-bar-monitor.service
systemctl --user status usage-bar-gui.service

# View logs
journalctl --user -u usage-bar-monitor.service -f
```

## Uninstall

```bash
make uninstall
```

To also remove your config:
```bash
rm -rf ~/.config/usage-bar/
```

See [README.md](README.md) for full documentation.
