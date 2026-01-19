"""Event system for decoupled communication."""

from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from loguru import logger
import threading


class EventType(Enum):
    """Types of events in the system."""

    # Asset events
    ASSET_CREATED = auto()
    ASSET_UPDATED = auto()
    ASSET_DELETED = auto()

    # Scan events
    SCAN_STARTED = auto()
    SCAN_PROGRESS = auto()
    SCAN_COMPLETED = auto()
    SCAN_FAILED = auto()

    # Vulnerability events
    VULNERABILITY_FOUND = auto()
    VULNERABILITY_RESOLVED = auto()

    # Audit events
    AUDIT_STARTED = auto()
    AUDIT_COMPLETED = auto()
    AUDIT_FAILED = auto()

    # User events
    USER_LOGIN = auto()
    USER_LOGOUT = auto()
    USER_CREATED = auto()
    USER_UPDATED = auto()
    USER_LOCKED = auto()

    # System events
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()
    DATABASE_BACKUP = auto()


@dataclass
class Event:
    """Event object containing event data."""

    type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    user_id: int | None = None

    def __str__(self) -> str:
        return f"Event({self.type.name}, source={self.source}, time={self.timestamp})"


class EventBus:
    """
    Thread-safe event bus for publish/subscribe pattern.

    Singleton pattern ensures single instance across application.
    """

    _instance: "EventBus | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._subscribers: dict[EventType, list[Callable[[Event], None]]] = {}
                    instance._all_subscribers: list[Callable[[Event], None]] = []
                    instance._subscriber_lock = threading.Lock()
                    cls._instance = instance
        return cls._instance

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to a specific event type."""
        with self._subscriber_lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)
                logger.debug(f"Handler subscribed to {event_type.name}")

    def subscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""
        with self._subscriber_lock:
            if handler not in self._all_subscribers:
                self._all_subscribers.append(handler)
                logger.debug("Handler subscribed to all events")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from a specific event type."""
        with self._subscriber_lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                    logger.debug(f"Handler unsubscribed from {event_type.name}")
                except ValueError:
                    pass

    def unsubscribe_all(self, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from all events."""
        with self._subscriber_lock:
            try:
                self._all_subscribers.remove(handler)
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        logger.debug(f"Publishing event: {event}")

        handlers_to_call: list[Callable[[Event], None]] = []

        with self._subscriber_lock:
            handlers_to_call.extend(self._all_subscribers)
            if event.type in self._subscribers:
                handlers_to_call.extend(self._subscribers[event.type])

        for handler in handlers_to_call:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error for {event.type.name}: {e}")

    def publish_async(self, event: Event) -> threading.Thread:
        """Publish an event asynchronously."""
        thread = threading.Thread(target=self.publish, args=(event,), daemon=True)
        thread.start()
        return thread

    def clear(self) -> None:
        """Clear all subscribers (useful for testing)."""
        with self._subscriber_lock:
            self._subscribers.clear()
            self._all_subscribers.clear()


def get_event_bus() -> EventBus:
    """Get the event bus singleton."""
    return EventBus()
