"""
Temporary HTTP server for serving images to OpenAI Vision API.

This allows us to send images as HTTP URLs instead of base64 encoding,
saving significant tokens.
"""
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket

from utils import print_with_color


class TempImageServer:
    """
    Simple HTTP server for serving local images via URLs.

    Usage:
        server = TempImageServer()
        server.start()
        url = server.get_url("/path/to/image.png")
        # Use url with OpenAI API
        server.stop()
    """

    def __init__(self, port=8765, directory=None):
        """
        Initialize temporary image server.

        Args:
            port: Port to serve on (default: 8765)
            directory: Directory to serve files from (default: auto-detect)
        """
        self.port = port

        # Use current working directory if not specified
        if directory is None:
            directory = os.getcwd()

        self.directory = os.path.abspath(directory)
        self.httpd = None
        self.thread = None
        self.running = False

    def _find_free_port(self):
        """Find a free port if the default is taken."""
        for port in range(self.port, self.port + 100):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        raise RuntimeError("Could not find a free port")

    def start(self):
        """Start the HTTP server in a background thread."""
        if self.running:
            return

        # Find a free port
        self.port = self._find_free_port()

        # Change to directory to serve
        original_dir = os.getcwd()
        os.chdir(self.directory)

        # Create server
        handler = SimpleHTTPRequestHandler

        # Suppress server logs
        handler.log_message = lambda *args: None

        try:
            self.httpd = HTTPServer(("localhost", self.port), handler)

            # Start server in background thread
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            self.running = True

            print_with_color(f"✓ Image server started: http://localhost:{self.port}", "green")

        finally:
            # Restore original directory
            os.chdir(original_dir)

    def stop(self):
        """Stop the HTTP server."""
        if not self.running:
            return

        if self.httpd:
            self.httpd.shutdown()
            self.httpd = None

        self.running = False
        print_with_color("✓ Image server stopped", "yellow")

    def get_url(self, file_path):
        """
        Get HTTP URL for a local file.

        Args:
            file_path: Absolute or relative file path

        Returns:
            HTTP URL string (e.g., "http://localhost:8765/screenshot.png")
        """
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)

        # Get relative path from serve directory
        try:
            rel_path = os.path.relpath(abs_path, self.directory)
        except ValueError:
            # File is on a different drive (Windows)
            # Copy file to temp directory
            import shutil
            filename = os.path.basename(abs_path)
            dest = os.path.join(self.directory, filename)
            shutil.copy(abs_path, dest)
            rel_path = filename

        # Convert to URL path (use forward slashes)
        url_path = rel_path.replace(os.sep, '/')

        return f"http://localhost:{self.port}/{url_path}"

    def __enter__(self):
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.stop()


# Global instance for easy access
_global_server = None


def get_global_server():
    """Get or create global image server instance."""
    global _global_server
    if _global_server is None:
        _global_server = TempImageServer()
        _global_server.start()
    return _global_server


def stop_global_server():
    """Stop global image server if running."""
    global _global_server
    if _global_server is not None:
        _global_server.stop()
        _global_server = None
