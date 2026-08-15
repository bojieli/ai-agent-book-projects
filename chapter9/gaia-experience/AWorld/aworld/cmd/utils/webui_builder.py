import subprocess
import logging
from pathlib import Path
import sys

logger = logging.getLogger(__name__)


def build_webui(force_rebuild: bool = False) -> str:
    webui_path = Path(__file__).parent.parent / "web" / "webui"
    static_path = webui_path / "dist"

    if (not static_path.exists()) or force_rebuild:
        logger.warning(f"Build WebUI at {webui_path}")

        try:
            subprocess.check_call(
                ["sh", "-c", "npm install && npm run build"],
                cwd=webui_path,
            )
            logger.info("WebUI build successfully")
        except:
            logger.error(f"Failed to build WebUI at {webui_path}")
            sys.exit(1)

    return static_path
