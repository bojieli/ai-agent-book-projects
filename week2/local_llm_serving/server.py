"""
vLLM Server Launcher for Qwen3 with Tool Calling Support
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path
from config import VLLM_SERVER_CONFIG, VLLM_HOST, VLLM_PORT
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VLLMServer:
    """Manager for vLLM server process"""
    
    def __init__(self, config: dict = None):
        """Initialize server manager with configuration"""
        self.config = config or VLLM_SERVER_CONFIG
        self.process = None
        self.server_url = f"http://{self.config['host']}:{self.config['port']}"
    
    def _build_command(self) -> list:
        """Build vLLM server command with arguments"""
        cmd = [
            sys.executable, "-m", "vllm.entrypoints.openai.api_server",
            "--model", self.config["model"],
            "--port", str(self.config["port"]),
            "--host", self.config["host"],
        ]
        
        # Add tool-specific arguments
        if self.config.get("enable_auto_tool_choice"):
            cmd.append("--enable-auto-tool-choice")
        
        if self.config.get("tool_call_parser"):
            cmd.extend(["--tool-call-parser", self.config["tool_call_parser"]])
        
        if self.config.get("chat_template"):
            cmd.extend(["--chat-template", self.config["chat_template"]])
        
        # Add performance arguments
        if self.config.get("max_model_len"):
            cmd.extend(["--max-model-len", str(self.config["max_model_len"])])
        
        if self.config.get("gpu_memory_utilization"):
            cmd.extend(["--gpu-memory-utilization", str(self.config["gpu_memory_utilization"])])
        
        if self.config.get("dtype"):
            cmd.extend(["--dtype", self.config["dtype"]])
        
        if self.config.get("enforce_eager"):
            cmd.append("--enforce-eager")
        
        # Add tensor parallel size if multiple GPUs
        if self.config.get("tensor_parallel_size"):
            cmd.extend(["--tensor-parallel-size", str(self.config["tensor_parallel_size"])])
        
        return cmd
    
    def start(self, wait_for_ready: bool = True, timeout: int = 120):
        """
        Start the vLLM server
        
        Args:
            wait_for_ready: Wait for server to be ready
            timeout: Maximum time to wait for server startup
        """
        if self.is_running():
            logger.info("vLLM server is already running")
            return
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Build command
        cmd = self._build_command()
        logger.info(f"Starting vLLM server with command: {' '.join(cmd)}")
        
        # Start server process
        log_file = log_dir / "vllm_server.log"
        with open(log_file, "w") as f:
            self.process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                env=os.environ.copy()
            )
        
        logger.info(f"vLLM server process started with PID: {self.process.pid}")
        logger.info(f"Server logs are being written to: {log_file}")
        
        if wait_for_ready:
            self._wait_for_ready(timeout)
    
    def _wait_for_ready(self, timeout: int = 120):
        """Wait for server to be ready"""
        start_time = time.time()
        health_url = f"{self.server_url}/health"
        
        logger.info(f"Waiting for vLLM server to be ready at {health_url}...")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=1)
                if response.status_code == 200:
                    logger.info("vLLM server is ready!")
                    
                    # Test model availability
                    models_url = f"{self.server_url}/v1/models"
                    models_response = requests.get(models_url)
                    if models_response.status_code == 200:
                        models = models_response.json()
                        logger.info(f"Available models: {models}")
                    return
            except requests.exceptions.RequestException:
                pass
            
            # Check if process is still running
            if self.process and self.process.poll() is not None:
                raise RuntimeError(f"vLLM server process died with code: {self.process.returncode}")
            
            time.sleep(2)
        
        raise TimeoutError(f"vLLM server did not start within {timeout} seconds")
    
    def stop(self):
        """Stop the vLLM server"""
        if self.process:
            logger.info("Stopping vLLM server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not stop gracefully, forcing kill...")
                self.process.kill()
                self.process.wait()
            
            self.process = None
            logger.info("vLLM server stopped")
    
    def is_running(self) -> bool:
        """Check if server is running"""
        if not self.process:
            return False
        
        # Check if process is still alive
        if self.process.poll() is not None:
            return False
        
        # Try to connect to health endpoint
        try:
            response = requests.get(f"{self.server_url}/health", timeout=1)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def restart(self):
        """Restart the server"""
        logger.info("Restarting vLLM server...")
        self.stop()
        time.sleep(2)
        self.start()


def download_model_from_modelscope():
    """
    Download Qwen3-0.6B model from ModelScope
    This is optional - vLLM can download from HuggingFace automatically
    """
    try:
        from modelscope import snapshot_download
        
        model_dir = snapshot_download(
            'Qwen/Qwen3-0.6B',
            cache_dir='./models'
        )
        logger.info(f"Model downloaded to: {model_dir}")
        return model_dir
    except ImportError:
        logger.warning("ModelScope not installed. Install with: pip install modelscope")
        logger.info("vLLM will download from HuggingFace instead")
        return None


def main():
    """Main function to start vLLM server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Start vLLM server with Qwen3 model")
    parser.add_argument("--download", action="store_true", 
                       help="Download model from ModelScope first")
    parser.add_argument("--model", type=str, default=None,
                       help="Model name or path (overrides config)")
    parser.add_argument("--port", type=int, default=None,
                       help="Server port (overrides config)")
    parser.add_argument("--host", type=str, default=None,
                       help="Server host (overrides config)")
    
    args = parser.parse_args()
    
    # Download model if requested
    if args.download:
        model_path = download_model_from_modelscope()
        if model_path:
            VLLM_SERVER_CONFIG["model"] = model_path
    
    # Override config with command line arguments
    if args.model:
        VLLM_SERVER_CONFIG["model"] = args.model
    if args.port:
        VLLM_SERVER_CONFIG["port"] = args.port
    if args.host:
        VLLM_SERVER_CONFIG["host"] = args.host
    
    # Create and start server
    server = VLLMServer(VLLM_SERVER_CONFIG)
    
    try:
        server.start(wait_for_ready=True)
        logger.info(f"vLLM server is running at {server.server_url}")
        logger.info("Press Ctrl+C to stop the server")
        
        # Keep the server running
        while True:
            time.sleep(1)
            if not server.is_running():
                logger.error("Server stopped unexpectedly!")
                break
                
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
