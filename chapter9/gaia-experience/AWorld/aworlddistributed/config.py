import os
import logging
from pathlib import Path

from aworld.utils.common import get_local_ip

####################################
# Load .env file
####################################

try:
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv("./.env"))
except ImportError:
    print("dotenv not installed, skipping...")

# Define log levels dictionary
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
ROOT_DIR = Path(__file__).parent  # the path containing this file
AGENTS_DIR = os.getenv("AGENTS_DIR", "./aworldspace/agents")
ROOT_LOG = os.path.join(os.getenv("LOG_DIR_PATH", "logs") , get_local_ip())
WORKSPACE_TYPE = os.environ.get("WORKSPACE_TYPE", "local")
WORKSPACE_PATH = os.environ.get("WORKSPACE_PATH", "./data/workspaces")
