"""Input device listener for keyboard and mouse events."""
import os
import select
import struct
import threading
import time
from pathlib import Path


class InputListener:
    """Listens to input device events and tracks timestamps."""
    
    def __init__(self):
        self.timestamps = []
        self.timestamps_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.devices = []
    
    def find_input_devices(self):
        """Find all accessible input devices in /dev/input."""
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
    
    @staticmethod
    def parse_event(data, event_format):
        """Parse input event data."""
        if len(data) == struct.calcsize(event_format):
            return struct.unpack(event_format, data)
        return None
    
    @staticmethod
    def is_relevant_event(ev_type, ev_code, ev_value):
        """Check if event is a key/button press or scroll."""
        # Event types
        EV_KEY = 0x01
        
        if ev_type == EV_KEY and ev_value == 1:
            return True
        return False
    
    def add_timestamp(self):
        """Add current timestamp to the list."""
        with self.timestamps_lock:
            self.timestamps.append(time.time())
    
    def remove_old_timestamps(self, cutoff_time):
        """Remove timestamps older than cutoff_time."""
        with self.timestamps_lock:
            self.timestamps[:] = [ts for ts in self.timestamps if ts > cutoff_time]
    
    def get_event_count(self):
        """Get current count of events."""
        with self.timestamps_lock:
            return len(self.timestamps)
    
    def listener_thread(self):
        """Thread that listens for input events and adds timestamps."""
        event_format = "llHHi"
        event_size = struct.calcsize(event_format)
        
        try:
            while not self.stop_event.is_set():
                # Use select with timeout to check for stop event
                readable, _, _ = select.select(
                    [fd for fd, _ in self.devices], [], [], 0.1
                )
                
                for fd in readable:
                    try:
                        data = os.read(fd, event_size)
                        parsed = self.parse_event(data, event_format)
                        
                        if parsed:
                            _, _, ev_type, ev_code, ev_value = parsed
                            
                            if self.is_relevant_event(ev_type, ev_code, ev_value):
                                self.add_timestamp()
                    
                    except BlockingIOError:
                        pass
        
        except Exception as e:
            print(f"Listener thread error: {e}")
    
    def cleanup_devices(self):
        """Close all device file descriptors."""
        for fd, _ in self.devices:
            try:
                os.close(fd)
            except Exception:
                pass
    
    def start(self):
        """Initialize and start listening to input devices."""
        self.devices = self.find_input_devices()
        
        if not self.devices:
            raise RuntimeError("No input devices found. Try running with sudo.")
        
        print(f"Monitoring {len(self.devices)} devices.")
        
        thread = threading.Thread(target=self.listener_thread, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop listening and cleanup."""
        self.stop_event.set()
        self.cleanup_devices()
