"""Streamlit app runner and manager for integration with FastAPI"""
import subprocess
import threading
import time
import os
import socket
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StreamlitRunner:
    """Manages the Streamlit app as a subprocess"""
    
    def __init__(self, streamlit_script: str = "streamlit_dashboard.py", port: int = 8501):
        self.streamlit_script = streamlit_script
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        
    def is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            return result != 0
    
    def find_available_port(self, start_port: int = 8501, max_attempts: int = 10) -> int:
        """Find an available port starting from start_port"""
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port):
                return port
        raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")
    
    def start(self):
        """Start the Streamlit app in a separate thread"""
        if self.is_running:
            logger.warning("Streamlit app is already running")
            return
        
        # Find available port if the default is in use
        if not self.is_port_available(self.port):
            logger.info(f"Port {self.port} is in use, finding alternative...")
            self.port = self.find_available_port(self.port)
            logger.info(f"Using port {self.port} for Streamlit")
        
        self.thread = threading.Thread(target=self._run_streamlit, daemon=True)
        self.thread.start()
        
        # Wait for Streamlit to start
        max_wait = 10  # seconds
        start_time = time.time()
        while self.is_port_available(self.port) and (time.time() - start_time) < max_wait:
            time.sleep(0.5)
        
        if self.is_port_available(self.port):
            logger.error("Failed to start Streamlit app")
            self.is_running = False
        else:
            logger.info(f"Streamlit app started on port {self.port}")
            self.is_running = True
    
    def _run_streamlit(self):
        """Run the Streamlit app"""
        try:
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            streamlit_path = os.path.join(project_root, self.streamlit_script)
            
            # Streamlit command with configuration
            cmd = [
                "streamlit", "run",
                streamlit_path,
                "--server.port", str(self.port),
                "--server.address", "localhost",
                "--server.headless", "true",
                "--browser.serverAddress", "localhost",
                "--browser.gatherUsageStats", "false",
                "--server.enableCORS", "false",
                "--server.enableXsrfProtection", "false"
            ]
            
            # Set environment to ensure backend API is accessible
            env = os.environ.copy()
            env["STREAMLIT_SERVER_PORT"] = str(self.port)
            
            logger.info(f"Starting Streamlit with command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=project_root
            )
            
            # Log output
            for line in iter(self.process.stdout.readline, b''):
                if line:
                    logger.debug(f"Streamlit: {line.decode().strip()}")
            
            self.process.wait()
            
        except Exception as e:
            logger.error(f"Error running Streamlit: {e}")
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop the Streamlit app"""
        if self.process:
            logger.info("Stopping Streamlit app...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self.is_running = False
            logger.info("Streamlit app stopped")
    
    def get_url(self) -> str:
        """Get the URL of the running Streamlit app"""
        return f"http://localhost:{self.port}"


# Global instance
streamlit_runner = StreamlitRunner()