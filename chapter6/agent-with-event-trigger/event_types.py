"""
Event types for the event-triggered agent system
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class EventType(Enum):
    """Types of events that can trigger agent actions"""
    # External input events
    WEB_MESSAGE = "web_message"
    IM_MESSAGE = "im_message"
    EMAIL_REPLY = "email_reply"
    GITHUB_PR_UPDATE = "github_pr_update"
    TIMER_TRIGGER = "timer_trigger"
    FILE_CHANGE = "file_change"

    # System reminder events
    USER_TIMEOUT = "user_timeout"
    PROCESS_TIMEOUT = "process_timeout"
    SYSTEM_ALERT = "system_alert"


@dataclass
class Event:
    """Represents an event that triggers agent action"""
    event_type: EventType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: Optional[str] = None
    
    def to_user_message(self) -> str:
        """Convert event to user message format for the agent"""
        if self.event_type == EventType.WEB_MESSAGE:
            return f"[Web Interface] {self.content}"
        
        elif self.event_type == EventType.IM_MESSAGE:
            sender = self.metadata.get('sender', 'Unknown')
            return f"[IM from {sender}] {self.content}"
        
        elif self.event_type == EventType.EMAIL_REPLY:
            from_email = self.metadata.get('from', 'Unknown')
            subject = self.metadata.get('subject', 'No Subject')
            return f"[Email Reply from {from_email}]\nSubject: {subject}\n{self.content}"
        
        elif self.event_type == EventType.GITHUB_PR_UPDATE:
            pr_number = self.metadata.get('pr_number', 'Unknown')
            action = self.metadata.get('action', 'updated')
            return f"[GitHub PR #{pr_number} {action}] {self.content}"
        
        elif self.event_type == EventType.TIMER_TRIGGER:
            timer_id = self.metadata.get('timer_id', 'Unknown')
            return f"[Timer {timer_id} triggered] {self.content}"

        elif self.event_type == EventType.FILE_CHANGE:
            path = self.metadata.get('path', 'Unknown')
            change = self.metadata.get('change', 'modified')
            return f"[File {change}: {path}] {self.content}"

        elif self.event_type == EventType.USER_TIMEOUT:
            duration = self.metadata.get('duration', 'unknown')
            return f"[System Reminder] User has not responded for {duration}. {self.content}"
        
        elif self.event_type == EventType.PROCESS_TIMEOUT:
            process_id = self.metadata.get('process_id', 'Unknown')
            duration = self.metadata.get('duration', 'unknown')
            return f"[System Alert] Background process {process_id} has been running for {duration}. {self.content}"
        
        elif self.event_type == EventType.SYSTEM_ALERT:
            alert_type = self.metadata.get('alert_type', 'general')
            return f"[System Alert: {alert_type}] {self.content}"
        
        else:
            return f"[{self.event_type.value}] {self.content}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        return {
            'event_type': self.event_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'event_id': self.event_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_type=EventType(data['event_type']),
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            event_id=data.get('event_id')
        )
