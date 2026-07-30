import re

def parse(line: str) -> dict | None:
    # 定义日志格式的正则表达式模式
    pattern = r'^\[(?P<timestamp>[^\]]+)\]\s*\((?P<level>[^)]+)\)\s*<tool=(?P<tool>[^>]+)>\s*\{latency_ms=(?P<latency_ms>\d+)\s+status=(?P<status>\w+)\}\s*::\s*(?P<message>.*)$'
    
    # 尝试匹配日志行
    match = re.match(pattern, line.strip())
    if not match:
        return None
    
    # 提取匹配的组
    groups = match.groupdict()
    
    # 检查所有必需字段是否存在且不为空
    required_keys = ['timestamp', 'level', 'tool', 'latency_ms', 'status', 'message']
    for key in required_keys:
        if key not in groups or not groups[key]:
            return None
    
    # 转换latency_ms为整数
    try:
        groups['latency_ms'] = int(groups['latency_ms'])
    except ValueError:
        return None
    
    return groups
