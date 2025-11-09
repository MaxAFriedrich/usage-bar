import os
import select
import socket
import struct
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


config = load_config()
BREAK_THRESHOLD = config['break_threshold']
OVERSPEED_THRESHOLD = config['overspeed_threshold']
OVERSPEED_COUNT_MULTIPLIER = config['overspeed_count_multiplier']
MAX_OVERSPEED_PENALTY = config['max_overspeed_penalty']
SOCKET_PATH = "/tmp/usage-bar.sock"

# Shared data structure
timestamps = []
timestamps_lock = threading.Lock()
stop_event = threading.Event()


def find_input_devices():
    """Find all accessible input devices in /dev/input"""
    input_dir = Path("/dev/input")
    devices = []

    try:
        for device_path in sorted(input_dir.glob("event*")):
            try:
                fd = os.open(str(device_path), os.O_RDONLY | os.O_NONBLOCK)
                devices.append((fd, device_path))
                print(f"Monitoring: {device_path}")
            except PermissionError:
                pass
    except Exception as e:
        print(f"Error accessing /dev/input: {e}")

    return devices


def parse_event(data, event_format):
    """Parse input event data"""
    if len(data) == struct.calcsize(event_format):
        return struct.unpack(event_format, data)
    return None


def is_relevant_event(ev_type, ev_code, ev_value):
    """Check if event is a key/button press or scroll"""

    # Event types
    EV_KEY = 0x01

    if ev_type == EV_KEY and ev_value == 1:
        return True
    return False


def add_timestamp():
    """Add current timestamp to the list"""
    with timestamps_lock:
        timestamps.append(time.time())


def listener_thread(devices):
    """Thread that listens for input events and adds timestamps"""
    event_format = "llHHi"
    event_size = struct.calcsize(event_format)

    try:
        while not stop_event.is_set():
            # Use select with timeout to check for stop event
            readable, _, _ = select.select([fd for fd, _ in devices], [], [],
                                           0.1)

            for fd in readable:
                try:
                    data = os.read(fd, event_size)
                    parsed = parse_event(data, event_format)

                    if parsed:
                        _, _, ev_type, ev_code, ev_value = parsed

                        if is_relevant_event(ev_type, ev_code, ev_value):
                            add_timestamp()

                except BlockingIOError:
                    pass

    except Exception as e:
        print(f"Listener thread error: {e}")


def remove_old_timestamps(cutoff_time):
    """Remove timestamps older than cutoff_time"""
    with timestamps_lock:
        timestamps[:] = [ts for ts in timestamps if ts > cutoff_time]


def get_event_count():
    """Get current count of events"""
    with timestamps_lock:
        return len(timestamps)


@dataclass
class State:
    # last time the keystroke count was zero
    last_zero: float = -1
    # number of seconds to add to break threshold for too fast
    overspeed_penalty: float = 0
    # currently in overspeed state
    in_overspeed: bool = False
    # time the break will finish
    break_finish: float = -1

    def set(self, count) -> None:
        if count == 0:
            if self.last_zero == -1:
                # entered state
                self.last_zero = time.time()
                self.break_finish = (
                        time.time() +
                        BREAK_THRESHOLD +
                        self.overspeed_penalty
                )
                return
            if time.time() > self.break_finish:
                # break is over, so reset
                self.overspeed_penalty = 0
                self.in_overspeed = False
                self.break_finish = -1
            return

        # make sure we know we are typing
        self.last_zero = -1
        self.break_finish = -1

        if count > OVERSPEED_THRESHOLD:
            self.in_overspeed = True
            new_penalty = count * OVERSPEED_COUNT_MULTIPLIER
            if new_penalty > self.overspeed_penalty:
                # don't let it drop!
                self.overspeed_penalty = new_penalty

        else:
            self.in_overspeed = False

        if self.overspeed_penalty > MAX_OVERSPEED_PENALTY:
            self.overspeed_penalty = MAX_OVERSPEED_PENALTY


state = State()


def counter_thread():
    global state
    """Thread that removes old events and prints count every 0.5 seconds"""
    try:
        while not stop_event.is_set():
            current_time = time.time()
            cutoff_time = current_time - 10.0

            remove_old_timestamps(cutoff_time)
            count = get_event_count()

            state.set(count)

            time.sleep(0.1)

    except Exception as e:
        print(f"Counter thread error: {e}")


def cleanup_devices(devices):
    """Close all device file descriptors"""
    for fd, _ in devices:
        os.close(fd)


class NotificationState(int, Enum):
    BREAK_OVER = 0
    BREAK = 1
    TYPING = 2
    OVERSPEED = 3


notification_state = NotificationState.BREAK
socket_clients = []
socket_clients_lock = threading.Lock()


def socket_server_thread():
    """Thread that manages the Unix socket server"""
    # Remove existing socket file if it exists
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(SOCKET_PATH)
    server_socket.listen(5)
    server_socket.settimeout(1.0)

    print(f"Socket server listening on {SOCKET_PATH}")

    while not stop_event.is_set():
        try:
            client_socket, _ = server_socket.accept()
            with socket_clients_lock:
                socket_clients.append(client_socket)
            print("Client connected to socket")
        except socket.timeout:
            continue
        except Exception as e:
            if not stop_event.is_set():
                print(f"Socket server error: {e}")

    server_socket.close()
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)


def broadcast_notification_state(state_color):
    """Send notification state to all connected socket clients"""
    with socket_clients_lock:
        disconnected = []
        for client in socket_clients:
            try:
                client.sendall(f"{state_color}\n".encode())
            except Exception:
                disconnected.append(client)

        for client in disconnected:
            socket_clients.remove(client)
            try:
                client.close()
            except Exception:
                pass


def notification_agent_thread():
    global notification_state
    while not stop_event.is_set():
        prev_state = notification_state

        if state.in_overspeed:
            notification_state = NotificationState.OVERSPEED
        elif state.break_finish != -1:
            notification_state = NotificationState.BREAK
        elif state.last_zero != -1:
            notification_state = NotificationState.BREAK_OVER
        elif state.last_zero == -1:
            notification_state = NotificationState.TYPING

        if prev_state != notification_state:
            broadcast_notification_state(notification_state.value)
            print("state changed:", notification_state)

        time.sleep(0.5)


def main():
    devices = find_input_devices()

    if not devices:
        print("No input devices found. Try running with sudo.")
        return 1

    print(f"Monitoring {len(devices)} devices. Press Ctrl+C to exit.\n")

    # Start threads
    listener = threading.Thread(target=listener_thread, args=(devices,),
                                daemon=True)
    counter = threading.Thread(target=counter_thread, daemon=True)

    notification_agent = threading.Thread(target=notification_agent_thread,
                                          daemon=True)

    socket_server = threading.Thread(target=socket_server_thread,
                                     daemon=True)

    listener.start()
    counter.start()
    notification_agent.start()
    socket_server.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        cleanup_devices(devices)

    return 0


if __name__ == "__main__":
    exit(main())
