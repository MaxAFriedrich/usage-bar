"""Unix socket server for communicating with GUI clients."""
import os
import socket
import threading


class SocketServer:
    """Manages Unix socket server for broadcasting notification states."""

    def __init__(self, socket_path):
        self.socket_path = socket_path
        self.clients = []
        self.clients_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.server_socket = None

    def start(self):
        """Start the socket server thread."""
        thread = threading.Thread(target=self._server_thread, daemon=True)
        thread.start()
        return thread

    def stop(self):
        """Stop the server and cleanup."""
        self.stop_event.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except Exception:
                pass

    def _server_thread(self):
        """Thread that manages the Unix socket server."""
        # Remove existing socket file if it exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)

        print(f"Socket server listening on {self.socket_path}")

        while not self.stop_event.is_set():
            try:
                client_socket, _ = self.server_socket.accept()
                with self.clients_lock:
                    self.clients.append(client_socket)
                print("Client connected to socket")
            except socket.timeout:
                continue
            except Exception as e:
                if not self.stop_event.is_set():
                    print(f"Socket server error: {e}")

        self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)

    def broadcast(self, state_value):
        """Send notification state to all connected socket clients."""
        with self.clients_lock:
            disconnected = []
            for client in self.clients:
                try:
                    client.sendall(f"{state_value}\n".encode())
                except Exception:
                    disconnected.append(client)

            for client in disconnected:
                self.clients.remove(client)
                try:
                    client.close()
                except Exception:
                    pass
