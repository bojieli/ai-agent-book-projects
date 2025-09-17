"""
Test Case Loader for User Memory Evaluation Framework
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import EVAL_FRAMEWORK_PATH

class TestCaseLoader:
    """Load test cases from user-memory-evaluation framework"""
    
    def __init__(self):
        self.eval_framework_path = EVAL_FRAMEWORK_PATH
        if not self.eval_framework_path.exists():
            raise ValueError(f"Evaluation framework not found at {self.eval_framework_path}")
    
    def get_all_test_cases(self) -> List[Dict[str, Any]]:
        """Get all available test cases"""
        script = """
import sys
import json
from pathlib import Path
import io

# Suppress rich console output
import rich.console
rich.console.Console = lambda *args, **kwargs: type('FakeConsole', (), {
    'print': lambda self, *a, **k: None,
    '__getattr__': lambda self, name: lambda *a, **k: None
})()

# Redirect output
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    from framework import UserMemoryEvaluationFramework
    
    framework = UserMemoryEvaluationFramework()
    test_cases = []
    
    for tc in framework.list_test_cases():
        test_cases.append({
            'test_id': tc.test_id,
            'category': tc.category,
            'title': tc.title,
            'description': tc.description,
            'num_conversations': len(tc.conversation_histories),
            'user_question': tc.user_question
        })
    
    # Restore stdout for JSON output
    sys.stdout = old_stdout
    print(json.dumps(test_cases))
    
except Exception as e:
    sys.stdout = old_stdout
    print(json.dumps([]))
"""
        
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=self.eval_framework_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error getting test cases: {result.stderr}")
            return []
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            print(f"Error parsing test cases JSON")
            return []
    
    def get_layer3_test_cases(self) -> List[Dict[str, Any]]:
        """Get only Layer 3 test cases (most complex)"""
        all_cases = self.get_all_test_cases()
        return [tc for tc in all_cases if tc['category'] == 'layer3']
    
    def get_test_case_conversations(self, test_id: str) -> List[Dict[str, Any]]:
        """Get detailed conversation histories for a specific test case"""
        script = f"""
import sys
import json
from pathlib import Path
import io

# Redirect stdout to suppress any print statements from framework
old_stdout = sys.stdout
sys.stdout = io.StringIO()

try:
    from framework import UserMemoryEvaluationFramework
    
    framework = UserMemoryEvaluationFramework()
    tc = framework.get_test_case("{test_id}")
    
    # Restore stdout for our JSON output
    sys.stdout = old_stdout
    
    if not tc:
        print(json.dumps([]))
    else:
        conversations = []
        for conv in tc.conversation_histories:
            conv_data = {{
                'conversation_id': conv.conversation_id,
                'timestamp': conv.timestamp,
                'messages': []
            }}
            
            for msg in conv.messages:
                msg_data = {{
                    'role': msg.role.value,
                    'content': msg.content
                }}
                # Add metadata if it exists
                if hasattr(msg, 'metadata'):
                    msg_data['metadata'] = msg.metadata
                conv_data['messages'].append(msg_data)
            
            conversations.append(conv_data)
        
        print(json.dumps(conversations))
        
except Exception as e:
    import traceback
    sys.stdout = old_stdout
    sys.stderr.write(traceback.format_exc())
    print(json.dumps([]))
"""
        
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=self.eval_framework_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error getting conversation histories: {result.stderr}")
            return []
        
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Error parsing conversation histories JSON: {e}")
            if result.stdout:
                print(f"stdout (first 500 chars): {result.stdout[:500]}")
            if result.stderr:
                print(f"stderr (first 500 chars): {result.stderr[:500]}")
            return []
    
    def format_conversation_text(self, conversation: Dict[str, Any]) -> str:
        """Format a conversation into readable text"""
        lines = []
        lines.append(f"Conversation ID: {conversation['conversation_id']}")
        lines.append(f"Timestamp: {conversation['timestamp']}")
        lines.append("-" * 50)
        
        for msg in conversation['messages']:
            role = msg['role'].upper()
            content = msg['content']
            lines.append(f"{role}: {content}")
            lines.append("")  # Empty line between messages
        
        return "\n".join(lines)
