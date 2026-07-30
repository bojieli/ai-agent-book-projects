import re

def parse(line: str) -> dict | None:
    # 定义匹配日志格式的正则表达式
    pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\|([A-Z]+)\|([\w.]+)\|step=(\d+)\|(.*)$'
    match = re.match(pattern, line.strip())
    
    if not match:
        return None
    
    # 提取各个字段
    timestamp = match.group(1)
    level = match.group(2)
    module = match.group(3)
    step = match.group(4)
    message = match.group(5)
    
    # 确保所有必需字段都不为空
    if not all([timestamp, level, module, step, message]):
        return None
    
    return {
        'timestamp': timestamp,
        'level': level,
        'module': module,
        'step': step,
        'message': message
    }
