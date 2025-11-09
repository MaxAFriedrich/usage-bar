# Usage Bar - Typing Activity Monitor with Visual Notifications

A keyboard and mouse activity monitoring system that helps prevent typing-related strain injuries by tracking your
activity and displaying visual notifications when you need to take breaks. This app does not require root (if you are in the `input` group).

## Overview

Usage Bar consists of two components:

1. **Python Monitor** - Monitors keyboard and mouse input events and manages the state machine (sources in `python-src/`, wrapper script `usage-bar-monitor`)
2. **C GUI** (`overspeed_monitor`) - Displays visual notifications on all monitors based on the current state

The two components communicate via a Unix socket (`/tmp/usage-bar.sock`).

## State Machine

The system uses a 6-state notification system to provide visual feedback about your typing activity:

### States

| State          | Value | Visual Display                                  | Meaning                                                          |
|----------------|-------|-------------------------------------------------|------------------------------------------------------------------|
| **UNKNOWN**    | -1    | Small black square (top-left)                   | Initial state on startup, waiting for monitor connection         |
| **BREAK_OVER** | 0     | Small green square (top-left)                   | Break period completed, ready to type                            |
| **BREAK**      | 1     | Small blue square (top-left)                    | Currently on break (no typing detected)                          |
| **TYPING**     | 2     | Small orange square (top-left)                  | Normal typing activity                                           |
| **OVERSPEED**  | 3     | Large red window with "OVERSPEED" text (center) | Typing too fast! Slow down, will also make the next break longer |
| **BREAK_DUE**  | 4     | Large orange window with "BREAK" text (center)  | Break time reached, should stop typing soon                      |

### State Colors

- **Black** (`#000000`) - Initial/Unknown state
- **Green** (`#007051`) - Break is over, safe to continue
- **Blue** (`#142f8c`) - On break
- **Orange** (`#8C4914`) - Normal typing or break needed
- **Red** (`#B70000`) - Overspeed warning
- **Orange** (`#FF6D00`) - Break due notification

### State Transitions

The monitor tracks:

- **Event count** - Number of keyboard/mouse events in the last 10 seconds
- **Break threshold** - Time before break is required (configurable in `config.yml`)
- **Break length** - Base duration of the break (configurable in `config.yml`)
- **Overspeed threshold** - Event count that triggers overspeed warning
- **Overspeed penalty** - Extra break time added when typing too fast

State flow:

1. **UNKNOWN** → Initial state on GUI startup
2. **TYPING** → When events detected and within normal threshold
3. **OVERSPEED** → When event count exceeds overspeed threshold
4. **BREAK_DUE** → When typing time exceeds break threshold
5. **BREAK** → When no events detected (user stopped typing)
6. **BREAK_OVER** → When break duration completed

### Configuration

The configuration file is searched in the following order:
1. `~/.config/usage-bar/config.yml` (user config)
2. `/etc/usage-bar/config.yml` (system config)
3. `./config.yml` (current directory, for development)

Edit `config.yml` to adjust thresholds:

```yaml
break_threshold: 50            # Seconds of typing before break needed
break_length: 10               # Base length of break (in seconds)
overspeed_threshold: 35        # Events/10s that trigger overspeed
overspeed_count_multiplier: 2  # Penalty multiplier per overspeed event
max_overspeed_penalty: 600     # Maximum penalty seconds
```

The `make install` command automatically copies the default config to `~/.config/usage-bar/config.yml` if it doesn't already exist.

## Building

### Prerequisites

Install system dependencies:

```bash
# Debian/Ubuntu
sudo apt-get install build-essential libx11-dev libxinerama-dev python3 python3-yaml

# Fedora/RHEL
sudo dnf install gcc libX11-devel libXinerama-devel python3 python3-pyyaml

# Arch Linux
sudo pacman -S base-devel libx11 libxinerama python python-yaml
```

### Compile

```bash
make
```

This will compile the C GUI component and create the `overspeed_monitor` binary.

To clean build artifacts:

```bash
make clean
```

Install both components and systemd user services:

```bash
make install
```

### Check Service Status

```bash
systemctl --user status usage-bar-monitor.service
systemctl --user status usage-bar-gui.service
```

### View Logs

```bash
# Monitor logs
journalctl --user -u usage-bar-monitor.service -f

# GUI logs
journalctl --user -u usage-bar-gui.service -f
```

### Uninstall

```bash
make uninstall
```

## Manual Development Testing

For development and testing, you can run the components manually without installing:

### Terminal 1 - Python Monitor

```bash
# Run using the wrapper script
./usage-bar-monitor

# Or run directly with Python
python3 python-src/main.py
```

**Note:** You may need to run with `sudo` if you don't have permission to access `/dev/input/event*` devices:

```bash
sudo ./usage-bar-monitor
```

### Terminal 2 - C GUI

```bash
# Build first
make

# Run the GUI
./overspeed_monitor
```

The GUI will automatically connect to the socket created by the Python monitor.

## Troubleshooting

### Permission Denied for /dev/input/

The monitor needs access to input device files. Solutions:

1. **Add user to input group** (recommended)
   ```bash
   sudo usermod -a -G input $USER
   # Log out and back in for changes to take effect
   ```

2. **Create udev rule** (most secure)
   Create `/etc/udev/rules.d/99-input.rules`:
   ```
   KERNEL=="event*", SUBSYSTEM=="input", MODE="0660", GROUP="input"
   ```
   Then: `sudo udevadm control --reload-rules && sudo udevadm trigger`

### GUI Not Displaying

- Check that DISPLAY environment variable is set: `echo $DISPLAY`
- Ensure X11 server is running
- Check GUI logs: `journalctl --user -u usage-bar-gui.service`

### Socket Connection Failed

- Ensure Python monitor is running first
- Check socket exists: `ls -l /tmp/usage-bar.sock`
- Check monitor logs: `journalctl --user -u usage-bar-monitor.service`
