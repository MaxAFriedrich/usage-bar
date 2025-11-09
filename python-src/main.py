#!/usr/bin/env python3
"""Main entry point for usage-bar monitor."""
import sys
import threading
import time

from config import Config
from input_listener import InputListener
from state_machine import TypingState, NotificationState
from socket_server import SocketServer


def counter_thread(listener, state, stop_event):
    """Thread that updates state based on event count."""
    try:
        while not stop_event.is_set():
            current_time = time.time()
            cutoff_time = current_time - 10.0
            
            listener.remove_old_timestamps(cutoff_time)
            count = listener.get_event_count()
            
            state.update(count)
            
            time.sleep(0.1)
    
    except Exception as e:
        print(f"Counter thread error: {e}")


def notification_thread(state, socket_server, stop_event):
    """Thread that determines and broadcasts notification states."""
    prev_state = None
    
    while not stop_event.is_set():
        notification_state = state.get_notification_state()
        
        if prev_state != notification_state:
            socket_server.broadcast(notification_state.value)
            print(f"State changed: {notification_state.name}")
            prev_state = notification_state
        
        time.sleep(0.5)


def main():
    """Main application entry point."""
    print("Usage Bar Monitor - Keyboard/Mouse Activity Monitor")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    
    # Initialize components
    listener = InputListener()
    state = TypingState(config)
    socket_server = SocketServer(config.socket_path)
    
    # Start input listener
    try:
        listener_thread_obj = listener.start()
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    
    # Start socket server
    socket_thread = socket_server.start()
    
    # Create stop event for threads
    stop_event = threading.Event()
    
    # Start counter thread
    counter_thread_obj = threading.Thread(
        target=counter_thread,
        args=(listener, state, stop_event),
        daemon=True
    )
    counter_thread_obj.start()
    
    # Start notification thread
    notification_thread_obj = threading.Thread(
        target=notification_thread,
        args=(state, socket_server, stop_event),
        daemon=True
    )
    notification_thread_obj.start()
    
    print("\nMonitoring started. Press Ctrl+C to exit.\n")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        stop_event.set()
        listener.stop()
        socket_server.stop()
        time.sleep(0.5)  # Give threads time to cleanup
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
