import re
from typing import Any, Dict, List, Literal, Optional, Union, Tuple
import logging as logger


def extract_pattern(content: str, pattern: str) -> Optional[str]:
    try:
        _pattern = fr"<{pattern}>(.*?)</{pattern}>"
        match = re.search(_pattern, content, re.DOTALL)
        if match:
            text = match.group(1)
            return text.strip()
        else:
            return None
    except Exception as e:
        logger.warning(f"Error extracting answer: {e}, current content: {content}")
        return None
       