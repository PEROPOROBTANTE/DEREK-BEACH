"""
Event Bus for Event-Driven Choreography
========================================

In-memory event bus implementation with support for:
- Asynchronous event publishing and subscription
- Event filtering by type and question_id
- Event history for traceability
- Subscriber management

For production, this can be replaced with Kafka, RabbitMQ, or similar.

Author: FARFAN Integration Team
Version: 1.0.0
Python: 3.11+
"""

import logging
import asyncio
import time
from typing import Dict, List, Callable, Optional, Any, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

from events.base_events import BaseEvent, EventType, EventStatus

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """
    Represents a subscription to events
    
    Attributes:
        subscriber_id: Unique identifier for subscriber
        event_types: Set of event types to receive
        callback: Function to call when event matches
        question_filter: Optional question_id filter
        active: Whether subscription is active
    """
    
    subscriber_id: str
    event_types: Set[EventType]
    callback: Callable[[BaseEvent], None]
    question_filter: Optional[str] = None
    active: bool = True


class EventBus:
    """
    In-memory event bus for choreography events
    
    Provides pub/sub mechanism for components to communicate via events.
    Maintains event history for traceability and debugging.
    
    Features:
    - Subscribe to specific event types
    - Filter events by question_id
    - Asynchronous event delivery
    - Event history with size limit
    - Thread-safe operations
    """
    
    def __init__(self, max_history_size: int = 10000):
        """
        Initialize event bus
        
        Args:
            max_history_size: Maximum number of events to keep in history
        """
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_history: deque = deque(maxlen=max_history_size)
        self.event_type_index: Dict[EventType, List[str]] = defaultdict(list)
        self.question_index: Dict[str, List[str]] = defaultdict(list)
        self.correlation_index: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._event_count = 0
        self._stats = {
            "events_published": 0,
            "events_delivered": 0,
            "active_subscriptions": 0,
        }
        
        logger.info("EventBus initialized")
    
    def subscribe(
        self,
        subscriber_id: str,
        event_types: List[EventType],
        callback: Callable[[BaseEvent], None],
        question_filter: Optional[str] = None
    ) -> str:
        """
        Subscribe to events
        
        Args:
            subscriber_id: Unique identifier for this subscriber
            event_types: List of event types to subscribe to
            callback: Function to call with matching events
            question_filter: Optional question_id to filter on
            
        Returns:
            Subscription ID
        """
        with self._lock:
            subscription = Subscription(
                subscriber_id=subscriber_id,
                event_types=set(event_types),
                callback=callback,
                question_filter=question_filter,
            )
            
            self.subscriptions[subscriber_id] = subscription
            
            # Index subscriptions by event type for faster lookup
            for event_type in event_types:
                if subscriber_id not in self.event_type_index[event_type]:
                    self.event_type_index[event_type].append(subscriber_id)
            
            self._stats["active_subscriptions"] = len(
                [s for s in self.subscriptions.values() if s.active]
            )
            
            logger.info(
                f"Subscribed {subscriber_id} to {len(event_types)} event types"
            )
            return subscriber_id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from events
        
        Args:
            subscriber_id: Subscriber to remove
            
        Returns:
            True if unsubscribed, False if not found
        """
        with self._lock:
            if subscriber_id not in self.subscriptions:
                return False
            
            subscription = self.subscriptions[subscriber_id]
            subscription.active = False
            
            # Remove from event type index
            for event_type in subscription.event_types:
                if subscriber_id in self.event_type_index[event_type]:
                    self.event_type_index[event_type].remove(subscriber_id)
            
            del self.subscriptions[subscriber_id]
            
            self._stats["active_subscriptions"] = len(
                [s for s in self.subscriptions.values() if s.active]
            )
            
            logger.info(f"Unsubscribed {subscriber_id}")
            return True
    
    def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to all matching subscribers
        
        Args:
            event: Event to publish
        """
        with self._lock:
            # Add to history
            self.event_history.append(event)
            self._event_count += 1
            self._stats["events_published"] += 1
            
            # Index event
            if event.question_id:
                self.question_index[event.question_id].append(event.event_id)
            self.correlation_index[event.correlation_id].append(event.event_id)
            
            # Find matching subscribers
            matching_subscribers = self._find_matching_subscribers(event)
            
            logger.debug(
                f"Publishing {event.event_type.value} "
                f"(event_id={event.event_id[:8]}...) "
                f"to {len(matching_subscribers)} subscribers"
            )
            
            # Deliver to subscribers asynchronously
            for subscriber_id in matching_subscribers:
                subscription = self.subscriptions.get(subscriber_id)
                if subscription and subscription.active:
                    self._deliver_event(subscription, event)
    
    def _find_matching_subscribers(self, event: BaseEvent) -> List[str]:
        """
        Find subscribers that should receive this event
        
        Args:
            event: Event to match
            
        Returns:
            List of matching subscriber IDs
        """
        matching = []
        
        # Get subscribers for this event type
        potential_subscribers = self.event_type_index.get(event.event_type, [])
        
        for subscriber_id in potential_subscribers:
            subscription = self.subscriptions.get(subscriber_id)
            if not subscription or not subscription.active:
                continue
            
            # Check event type match
            if event.event_type not in subscription.event_types:
                continue
            
            # Check question filter
            if subscription.question_filter:
                if event.question_id != subscription.question_filter:
                    continue
            
            matching.append(subscriber_id)
        
        return matching
    
    def _deliver_event(self, subscription: Subscription, event: BaseEvent) -> None:
        """
        Deliver event to subscriber asynchronously
        
        Args:
            subscription: Subscription to deliver to
            event: Event to deliver
        """
        def _safe_callback():
            try:
                subscription.callback(event)
                self._stats["events_delivered"] += 1
            except Exception as e:
                logger.error(
                    f"Error delivering event to {subscription.subscriber_id}: {e}",
                    exc_info=True
                )
        
        self._executor.submit(_safe_callback)
    
    def get_events_by_question(self, question_id: str) -> List[BaseEvent]:
        """
        Get all events for a specific question
        
        Args:
            question_id: Question ID to filter by
            
        Returns:
            List of events for this question
        """
        with self._lock:
            event_ids = self.question_index.get(question_id, [])
            return [
                event for event in self.event_history
                if event.event_id in event_ids
            ]
    
    def get_events_by_correlation(self, correlation_id: str) -> List[BaseEvent]:
        """
        Get all events in a correlation chain
        
        Args:
            correlation_id: Correlation ID to filter by
            
        Returns:
            List of correlated events
        """
        with self._lock:
            event_ids = self.correlation_index.get(correlation_id, [])
            return [
                event for event in self.event_history
                if event.event_id in event_ids
            ]
    
    def get_events_by_type(self, event_type: EventType) -> List[BaseEvent]:
        """
        Get all events of a specific type
        
        Args:
            event_type: Event type to filter by
            
        Returns:
            List of events of this type
        """
        with self._lock:
            return [
                event for event in self.event_history
                if event.event_type == event_type
            ]
    
    def get_all_events(self) -> List[BaseEvent]:
        """Get all events in history"""
        with self._lock:
            return list(self.event_history)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return {
                **self._stats,
                "total_events": self._event_count,
                "history_size": len(self.event_history),
                "subscriptions": len(self.subscriptions),
                "event_type_index_size": sum(
                    len(subs) for subs in self.event_type_index.values()
                ),
            }
    
    def clear_history(self) -> None:
        """Clear event history (for testing)"""
        with self._lock:
            self.event_history.clear()
            self.question_index.clear()
            self.correlation_index.clear()
            self._event_count = 0
            logger.info("Event history cleared")
    
    def shutdown(self) -> None:
        """Shutdown event bus and cleanup resources"""
        logger.info("Shutting down EventBus")
        self._executor.shutdown(wait=True)
        with self._lock:
            self.subscriptions.clear()
            self.event_type_index.clear()


# Global event bus instance (singleton pattern)
_event_bus_instance: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get global event bus instance
    
    Returns:
        Global EventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance


def reset_event_bus() -> None:
    """Reset global event bus (for testing)"""
    global _event_bus_instance
    if _event_bus_instance:
        _event_bus_instance.shutdown()
    _event_bus_instance = None
