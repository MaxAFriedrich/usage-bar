# Usage Bar - Typing Activity Monitor with Visual Notifications

A keyboard and mouse activity monitoring system that helps prevent typing-related strain injuries by tracking your
activity and displaying visual notifications when you need to take breaks.

## Overview

Usage Bar consists of two components:

1. **Python Monitor** (`input_monitor.py`) - Monitors keyboard and mouse input events and manages the state machine
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
- **Overspeed threshold** - Event count that triggers overspeed warning
- **Overspeed penalty** - Extra break time added when typing too fast

State flow:

1. **UNKNOWN** → Initial state on GUI startup
2. **TYPING** → When events detected and within normal threshold
3. **OVERSPEED** → When event count exceeds overspeed threshold
4. **BREAK_DUE** → When typing time exceeds break threshold
5. **BREAK** → When no events detected (user stopped typing)
6. **BREAK_OVER** → When break duration completed
4. **BREAK** → When no events detected (user stopped typing)
5. **BREAK_OVER** → When break duration completed

### Configuration

The configuration file is searched in the following order:
1. `~/.config/usage-bar/config.yml` (user config)
2. `/etc/usage-bar/config.yml` (system config)
3. `./config.yml` (current directory, for development)

Edit `config.yml` to adjust thresholds:

```yaml
break_threshold: 300           # Seconds of typing before break needed
overspeed_threshold: 15        # Events/10s that trigger overspeed
overspeed_count_multiplier: 2  # Penalty multiplier per overspeed event
max_overspeed_penalty: 600     # Maximum penalty seconds
```

The `make install` command automatically copies the default config to `~/.config/usage-bar/config.yml` if it doesn't already exist.

## Building

### Prerequisites

**System packages:**

```bash
# Debian/Ubuntu
sudo apt-get install build-essential libx11-dev libxinerama-dev

# Fedora/RHEL
sudo dnf install gcc libX11-devel libXinerama-devel

# Arch Linux
sudo pacman -S base-devel libx11 libxinerama
```

**Python dependencies:**

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install pyyaml
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

## Installation

### System-wide Installation

Install both components and systemd user services:

```bash
make install
```

This will:

- Install binaries to `/usr/local/bin/` (or `$PREFIX/bin`)
- Install systemd user service files to `~/.config/systemd/user/`
- Reload systemd user daemon

### Enable and Start Services

```bash
# Enable services to start on login
systemctl --user enable usage-bar-monitor.service
systemctl --user enable usage-bar-gui.service

# Start services now
systemctl --user start usage-bar-monitor.service
systemctl --user start usage-bar-gui.service

# Or enable and start in one command
systemctl --user enable --now usage-bar-monitor.service
systemctl --user enable --now usage-bar-gui.service
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

# Or run directly with Python (from project root)
cd python-src && python3 main.py
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

### Testing State Changes

You can manually test state transitions by:

1. **TYPING** - Start typing normally
2. **OVERSPEED** - Type very quickly to exceed threshold
3. **BREAK_DUE** - Wait for break threshold time while typing
4. **BREAK** - Stop all keyboard/mouse activity
5. **BREAK_OVER** - Wait for break duration to complete

Watch the terminal output from `input_monitor.py` to see state changes:

```
state changed: NotificationState.TYPING
state changed: NotificationState.OVERSPEED
state changed: NotificationState.BREAK_DUE
```

### Testing Socket Communication

You can also test the socket directly:

```bash
# In one terminal
./usage-bar-monitor

# In another terminal, connect to the socket
nc -U /tmp/usage-bar.sock

# You'll see state numbers printed as they change
# -1 = UNKNOWN, 0 = BREAK_OVER, 1 = BREAK, 2 = TYPING, 3 = OVERSPEED, 4 = BREAK_DUE
```

## Project Structure

```
usage-bar/
├── src/                       # C GUI source files
│   ├── common.h               # Shared constants and state definitions
│   ├── window.h/c             # X11 window management and display
│   ├── socket.h/c             # Unix socket communication
│   └── main.c                 # Main GUI entry point
├── python-src/                # Python monitor source files
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Main entry point
│   ├── config.py              # Configuration management
│   ├── input_listener.py      # Input device event monitoring
│   ├── state_machine.py       # State tracking and transitions
│   └── socket_server.py       # Unix socket server
├── systemd/
│   ├── usage-bar-monitor.service  # Python monitor service
│   └── usage-bar-gui.service      # C GUI service
├── usage-bar-monitor          # Python monitor wrapper script
├── Makefile                   # Build system
├── config.yml                 # Default configuration file
├── colors.md                  # Color definitions
└── README.md                  # This file
```
├── Makefile               # Build system
├── config.yml             # Configuration file
├── colors.md              # Color definitions
└── README.md              # This file
```

## Troubleshooting

### Permission Denied for /dev/input/

The monitor needs access to input device files. Solutions:

1. **Run with sudo** (simple but not recommended for production)
   ```bash
   sudo python3 input_monitor.py
   ```

2. **Add user to input group** (recommended)
   ```bash
   sudo usermod -a -G input $USER
   # Log out and back in for changes to take effect
   ```

3. **Create udev rule** (most secure)
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

### Multi-Monitor Setup

The GUI automatically detects and displays on all Xinerama screens. Small indicators appear in the top-left corner of
each monitor, while large notifications are centered.

