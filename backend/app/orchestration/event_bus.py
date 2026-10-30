"""Event Bus for Agent Communication"""
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple
from uuid import uuid4

class Event:
    def __init__(self, event_type: str, data: Dict[str, Any], source: str = "system"):
        self.event_id = str(uuid4())
        self.event_type = event_type
        self.data = data
        self.source = source
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }

class EventBus:
    """Central event bus for agent communication"""
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history_size = 1000

    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    async def publish(self, event_type: str, data: Dict[str, Any], source: str = "system") -> Tuple[Event, List[Any]]:
        event = Event(event_type, data, source)
        # Recorded before callbacks run: callbacks may recursively publish further
        # events (e.g. negotiation/arbitration chains), so appending only after they
        # complete would record nested events ahead of the event that triggered them.
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)
        results: List[Any] = []
        if event_type in self.subscribers:
            payload = {"type": event.event_type, **event.data}
            for callback in self.subscribers[event_type]:
                try:
                    results.append(await callback(payload))
                except Exception:
                    logging.getLogger(__name__).exception("Event handler failed for %s", event_type)
                    raise
        return event, results

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.event_history[-limit:]]