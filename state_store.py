"""
State Store - Immutable Workflow State Management
==================================================

Manages workflow instance state with immutability, atomicity, and persistence.
Supports version tracking and state transitions for deterministic execution.

Key Features:
- Immutable state representation using frozen dataclasses
- Atomic state updates with optimistic locking
- State history tracking for audit and debugging
- Thread-safe operations
- Persistence to disk (JSON) for recovery
- Query interface for workflow status

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow instance status"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass(frozen=True)
class StepResult:
    """Immutable step execution result"""
    step_id: str
    question_id: str
    status: StepStatus
    output: Dict[str, Any]
    validation_passed: bool
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass(frozen=True)
class WorkflowState:
    """
    Immutable workflow instance state
    
    This represents a complete snapshot of workflow execution state at a point in time.
    All updates create a new WorkflowState instance rather than modifying in place.
    """
    workflow_id: str
    version: int  # Incremented on each state update
    status: WorkflowStatus
    current_step: Optional[str]
    completed_steps: Set[str]
    failed_steps: Set[str]
    skipped_steps: Set[str]
    step_results: Dict[str, StepResult]
    error_count: int
    retry_count: int
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "workflow_id": self.workflow_id,
            "version": self.version,
            "status": self.status.value,
            "current_step": self.current_step,
            "completed_steps": list(self.completed_steps),
            "failed_steps": list(self.failed_steps),
            "skipped_steps": list(self.skipped_steps),
            "step_results": {k: v.to_dict() for k, v in self.step_results.items()},
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """Create from dictionary (for deserialization)"""
        # Convert string enums back to enum objects
        status = WorkflowStatus(data["status"])
        
        # Convert step results
        step_results = {}
        for step_id, result_data in data.get("step_results", {}).items():
            # Handle both StepResult objects and dicts
            if isinstance(result_data, StepResult):
                step_results[step_id] = result_data
            else:
                result_data = result_data.copy() if isinstance(result_data, dict) else {}
                result_data['status'] = StepStatus(result_data['status'])
                step_results[step_id] = StepResult(**result_data)
        
        return cls(
            workflow_id=data["workflow_id"],
            version=data["version"],
            status=status,
            current_step=data.get("current_step"),
            completed_steps=set(data.get("completed_steps", [])),
            failed_steps=set(data.get("failed_steps", [])),
            skipped_steps=set(data.get("skipped_steps", [])),
            step_results=step_results,
            error_count=data.get("error_count", 0),
            retry_count=data.get("retry_count", 0),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            metadata=data.get("metadata", {})
        )
    
    def __hash__(self):
        # Make hashable for caching
        return hash((self.workflow_id, self.version))


class StateStore:
    """
    Thread-safe, persistent state store for workflow instances
    
    Features:
    - Immutable state with versioning
    - Atomic updates with optimistic locking
    - State history for audit trail
    - Persistence to disk for recovery
    - Thread-safe operations
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize state store
        
        Args:
            storage_dir: Directory for persistent storage (default: ./workflow_states)
        """
        self.storage_dir = storage_dir or Path("./workflow_states")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._states: Dict[str, WorkflowState] = {}  # Current states by workflow_id
        self._history: Dict[str, List[WorkflowState]] = {}  # State history
        self._lock = threading.Lock()
        
        logger.info(f"StateStore initialized with storage: {self.storage_dir}")
    
    def create_workflow(
        self,
        workflow_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WorkflowState:
        """
        Create a new workflow instance
        
        Args:
            workflow_id: Unique workflow identifier
            metadata: Optional metadata for the workflow
            
        Returns:
            Initial WorkflowState
            
        Raises:
            ValueError: If workflow_id already exists
        """
        with self._lock:
            if workflow_id in self._states:
                raise ValueError(f"Workflow {workflow_id} already exists")
            
            now = datetime.now().isoformat()
            
            initial_state = WorkflowState(
                workflow_id=workflow_id,
                version=1,
                status=WorkflowStatus.CREATED,
                current_step=None,
                completed_steps=set(),
                failed_steps=set(),
                skipped_steps=set(),
                step_results={},
                error_count=0,
                retry_count=0,
                created_at=now,
                updated_at=now,
                metadata=metadata or {}
            )
            
            self._states[workflow_id] = initial_state
            self._history[workflow_id] = [initial_state]
            
            # Persist to disk
            self._persist_state(initial_state)
            
            logger.info(f"Created workflow: {workflow_id}")
            
            return initial_state
    
    def update_state(
        self,
        workflow_id: str,
        updates: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> WorkflowState:
        """
        Update workflow state atomically
        
        Args:
            workflow_id: Workflow identifier
            updates: Dictionary of fields to update
            expected_version: Expected current version for optimistic locking
            
        Returns:
            New WorkflowState with updates applied
            
        Raises:
            ValueError: If workflow doesn't exist or version mismatch
        """
        with self._lock:
            if workflow_id not in self._states:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            current_state = self._states[workflow_id]
            
            # Optimistic locking check
            if expected_version is not None and current_state.version != expected_version:
                raise ValueError(
                    f"Version mismatch: expected {expected_version}, "
                    f"current {current_state.version}"
                )
            
            # Create new state with updates
            state_dict = current_state.to_dict()
            state_dict["version"] = current_state.version + 1
            state_dict["updated_at"] = datetime.now().isoformat()
            
            # Apply updates
            for key, value in updates.items():
                if key in ["completed_steps", "failed_steps", "skipped_steps"]:
                    # Convert to set
                    if isinstance(value, (list, set)):
                        state_dict[key] = list(value)
                    else:
                        state_dict[key] = list(current_state.__dict__[key] | {value})
                elif key == "step_results":
                    # Merge step results
                    state_dict["step_results"].update(value)
                else:
                    state_dict[key] = value
            
            # Create new immutable state
            new_state = WorkflowState.from_dict(state_dict)
            
            # Update in memory
            self._states[workflow_id] = new_state
            self._history[workflow_id].append(new_state)
            
            # Persist to disk
            self._persist_state(new_state)
            
            logger.debug(
                f"Updated workflow {workflow_id}: v{current_state.version} → v{new_state.version}"
            )
            
            return new_state
    
    def mark_step_completed(
        self,
        workflow_id: str,
        step_id: str,
        result: StepResult
    ) -> WorkflowState:
        """Mark a step as completed with its result"""
        return self.update_state(
            workflow_id,
            {
                "completed_steps": step_id,
                "step_results": {step_id: result},
                "current_step": None
            }
        )
    
    def mark_step_failed(
        self,
        workflow_id: str,
        step_id: str,
        result: StepResult
    ) -> WorkflowState:
        """Mark a step as failed"""
        current = self.get_state(workflow_id)
        return self.update_state(
            workflow_id,
            {
                "failed_steps": step_id,
                "step_results": {step_id: result},
                "error_count": current.error_count + 1,
                "current_step": None
            }
        )
    
    def mark_step_skipped(
        self,
        workflow_id: str,
        step_id: str,
        reason: str
    ) -> WorkflowState:
        """Mark a step as skipped"""
        result = StepResult(
            step_id=step_id,
            question_id=step_id,
            status=StepStatus.SKIPPED,
            output={},
            validation_passed=False,
            error_message=reason
        )
        
        return self.update_state(
            workflow_id,
            {
                "skipped_steps": step_id,
                "step_results": {step_id: result},
                "current_step": None
            }
        )
    
    def mark_step_running(
        self,
        workflow_id: str,
        step_id: str
    ) -> WorkflowState:
        """Mark a step as currently running"""
        return self.update_state(
            workflow_id,
            {
                "current_step": step_id,
                "status": WorkflowStatus.RUNNING
            }
        )
    
    def increment_retry(
        self,
        workflow_id: str,
        step_id: str
    ) -> WorkflowState:
        """Increment retry count for a step"""
        current = self.get_state(workflow_id)
        step_result = current.step_results.get(step_id)
        
        if step_result:
            # Create new result with incremented retry count
            result_dict = step_result.to_dict()
            result_dict['retry_count'] = step_result.retry_count + 1
            result_dict['status'] = StepStatus.RETRYING.value
            new_result = StepResult(**{**result_dict, 'status': StepStatus.RETRYING})
            
            return self.update_state(
                workflow_id,
                {
                    "step_results": {step_id: new_result},
                    "retry_count": current.retry_count + 1
                }
            )
        
        return current
    
    def mark_workflow_completed(self, workflow_id: str) -> WorkflowState:
        """Mark entire workflow as completed"""
        return self.update_state(
            workflow_id,
            {
                "status": WorkflowStatus.COMPLETED,
                "current_step": None
            }
        )
    
    def mark_workflow_failed(
        self,
        workflow_id: str,
        reason: str
    ) -> WorkflowState:
        """Mark entire workflow as failed"""
        current = self.get_state(workflow_id)
        metadata = current.metadata.copy()
        metadata["failure_reason"] = reason
        
        return self.update_state(
            workflow_id,
            {
                "status": WorkflowStatus.FAILED,
                "current_step": None,
                "metadata": metadata
            }
        )
    
    def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get current state of a workflow"""
        with self._lock:
            return self._states.get(workflow_id)
    
    def get_history(self, workflow_id: str) -> List[WorkflowState]:
        """Get state history for a workflow"""
        with self._lock:
            return self._history.get(workflow_id, []).copy()
    
    def get_step_result(
        self,
        workflow_id: str,
        step_id: str
    ) -> Optional[StepResult]:
        """Get result for a specific step"""
        state = self.get_state(workflow_id)
        if state:
            return state.step_results.get(step_id)
        return None
    
    def list_workflows(
        self,
        status: Optional[WorkflowStatus] = None
    ) -> List[str]:
        """List all workflow IDs, optionally filtered by status"""
        with self._lock:
            if status is None:
                return list(self._states.keys())
            
            return [
                wid for wid, state in self._states.items()
                if state.status == status
            ]
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow and its history"""
        with self._lock:
            if workflow_id not in self._states:
                return False
            
            # Remove from memory
            del self._states[workflow_id]
            if workflow_id in self._history:
                del self._history[workflow_id]
            
            # Remove from disk
            state_file = self.storage_dir / f"{workflow_id}.json"
            if state_file.exists():
                state_file.unlink()
            
            logger.info(f"Deleted workflow: {workflow_id}")
            return True
    
    def _persist_state(self, state: WorkflowState) -> None:
        """Persist state to disk"""
        try:
            state_file = self.storage_dir / f"{state.workflow_id}.json"
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Persisted state for workflow: {state.workflow_id}")
            
        except Exception as e:
            logger.error(f"Failed to persist state: {e}", exc_info=True)
    
    def load_from_disk(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load workflow state from disk"""
        try:
            state_file = self.storage_dir / f"{workflow_id}.json"
            
            if not state_file.exists():
                logger.warning(f"State file not found: {state_file}")
                return None
            
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = WorkflowState.from_dict(data)
            
            with self._lock:
                self._states[workflow_id] = state
                self._history[workflow_id] = [state]
            
            logger.info(f"Loaded workflow from disk: {workflow_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to load state from disk: {e}", exc_info=True)
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get state store statistics"""
        with self._lock:
            total = len(self._states)
            by_status = {}
            
            for state in self._states.values():
                status_name = state.status.value
                by_status[status_name] = by_status.get(status_name, 0) + 1
            
            total_history = sum(len(h) for h in self._history.values())
            
            return {
                "total_workflows": total,
                "by_status": by_status,
                "total_history_entries": total_history,
                "storage_dir": str(self.storage_dir)
            }


if __name__ == "__main__":
    # Test the state store
    print("=" * 80)
    print("STATE STORE TEST")
    print("=" * 80)
    
    # Create state store
    store = StateStore(storage_dir=Path("/tmp/test_workflow_states"))
    
    # Create a workflow
    print("\nCreating workflow...")
    workflow_id = f"test_workflow_{int(time.time())}"
    state = store.create_workflow(
        workflow_id,
        metadata={"plan_name": "Test Plan", "questions": 5}
    )
    
    print(f"✓ Created: {workflow_id}")
    print(f"  Status: {state.status.value}")
    print(f"  Version: {state.version}")
    print(f"  Created: {state.created_at}")
    
    # Start workflow
    print("\nStarting workflow...")
    state = store.update_state(workflow_id, {"status": WorkflowStatus.RUNNING})
    print(f"✓ Status: {state.status.value}")
    print(f"  Version: {state.version}")
    
    # Execute some steps
    print("\nExecuting steps...")
    for i in range(1, 4):
        step_id = f"step_{i}"
        
        # Mark step running
        state = store.mark_step_running(workflow_id, step_id)
        print(f"  Running step {i}...")
        
        # Complete step
        result = StepResult(
            step_id=step_id,
            question_id=f"P1-D1-Q{i}",
            status=StepStatus.COMPLETED,
            output={"score": 2.5, "confidence": 0.9},
            validation_passed=True,
            execution_time=1.5
        )
        
        state = store.mark_step_completed(workflow_id, step_id, result)
        print(f"  ✓ Completed step {i}")
    
    # Complete workflow
    print("\nCompleting workflow...")
    state = store.mark_workflow_completed(workflow_id)
    print(f"✓ Status: {state.status.value}")
    print(f"  Completed steps: {len(state.completed_steps)}")
    print(f"  Failed steps: {len(state.failed_steps)}")
    print(f"  Total versions: {state.version}")
    
    # Show history
    print("\nState history:")
    history = store.get_history(workflow_id)
    for h_state in history:
        print(f"  v{h_state.version}: {h_state.status.value} @ {h_state.updated_at}")
    
    # Show stats
    print("\n" + "=" * 80)
    print("STATE STORE STATISTICS")
    print("=" * 80)
    
    stats = store.get_stats()
    print(f"Total workflows: {stats['total_workflows']}")
    print(f"By status: {stats['by_status']}")
    print(f"Total history entries: {stats['total_history_entries']}")
    print(f"Storage directory: {stats['storage_dir']}")
    
    print("\n" + "=" * 80)
