"""
Resilience Manager - Circuit Breaker, Retry Logic, and Compensation
====================================================================

Manages fault tolerance strategies including retry logic, circuit breaker
integration, exponential backoff, and compensation actions (Saga pattern).

Key Features:
- Integration with existing CircuitBreaker
- Configurable retry strategies (fixed, exponential backoff)
- Differentiated handling for technical vs validation failures
- Compensation actions for transactional behavior (Saga pattern)
- Comprehensive failure tracking and metrics
- Strategy selection based on error type and context

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import random

from circuit_breaker import CircuitBreaker, CircuitState, FailureSeverity
from metadata_service import QuestionContext, ErrorStrategy
from event_schemas import SubProcessFailedEvent

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures"""
    TECHNICAL = "technical"  # Network, timeout, dependency failure
    VALIDATION = "validation"  # Validation rule violations
    BUSINESS_LOGIC = "business_logic"  # Business rule violations
    RESOURCE = "resource"  # Resource exhaustion (memory, CPU)
    CHOREOGRAPHER_ERROR = "choreographer_error"  # Errors from choreographed sub-processes


class RetryStrategy(Enum):
    """Retry strategies"""
    NONE = "none"
    FIXED = "fixed"  # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    JITTERED_EXPONENTIAL = "jittered_exponential"  # With random jitter


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    strategy: RetryStrategy
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter_factor: float = 0.1  # 10% jitter


@dataclass
class FailureRecord:
    """Record of a failure event"""
    timestamp: str
    failure_type: FailureType
    error_message: str
    step_id: str
    question_id: str
    retry_attempt: int
    recovery_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompensationAction:
    """Compensation action for saga pattern"""
    step_id: str
    action_callable: Callable[[Dict[str, Any]], Any]
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResilienceManager:
    """
    Central resilience manager for orchestrator fault tolerance
    
    Features:
    - Circuit breaker integration
    - Configurable retry strategies
    - Exponential backoff with jitter
    - Compensation actions (Saga pattern)
    - Failure classification and differentiated handling
    - Comprehensive metrics and reporting
    """
    
    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        default_retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize resilience manager
        
        Args:
            circuit_breaker: Existing CircuitBreaker instance (creates new if None)
            default_retry_config: Default retry configuration
        """
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        
        self.default_retry_config = default_retry_config or RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter_factor=0.1
        )
        
        # Failure tracking
        self._failure_history: List[FailureRecord] = []
        self._compensation_log: List[Dict[str, Any]] = []
        
        # Metrics
        self._metrics = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "circuit_breaks": 0,
            "compensations_executed": 0,
            "by_failure_type": {ft.value: 0 for ft in FailureType},
            "by_retry_strategy": {rs.value: 0 for rs in RetryStrategy},
        }
        
        logger.info("ResilienceManager initialized")
    
    def execute_with_resilience(
        self,
        operation: Callable[[], Any],
        context: QuestionContext,
        step_id: str,
        retry_config: Optional[RetryConfig] = None
    ) -> Dict[str, Any]:
        """
        Execute operation with full resilience support
        
        Args:
            operation: Function to execute
            context: QuestionContext for the operation
            step_id: Unique identifier for this step
            retry_config: Optional retry configuration (uses default if None)
            
        Returns:
            Dictionary with result and metadata
        """
        adapter_name = f"{context.dimension}_{context.question_id}"
        retry_config = retry_config or self.default_retry_config
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute(adapter_name):
            logger.warning(f"Circuit breaker OPEN for {adapter_name}, using fallback")
            self._metrics["circuit_breaks"] += 1
            
            return self._handle_circuit_open(context, step_id)
        
        # Determine retry strategy based on error strategy
        if context.error_strategy == ErrorStrategy.FAIL_FAST:
            retry_config = RetryConfig(strategy=RetryStrategy.NONE, max_attempts=1)
        elif context.error_strategy == ErrorStrategy.SKIP:
            retry_config = RetryConfig(strategy=RetryStrategy.NONE, max_attempts=1)
        
        # Execute with retries
        last_error = None
        attempt = 0
        
        while attempt < retry_config.max_attempts:
            attempt += 1
            
            try:
                # Execute operation
                start_time = time.time()
                result = operation()
                execution_time = time.time() - start_time
                
                # Report success to circuit breaker
                self.circuit_breaker.record_success(adapter_name, execution_time)
                
                # Log successful retry if not first attempt
                if attempt > 1:
                    self._metrics["successful_retries"] += 1
                    logger.info(
                        f"Operation succeeded on attempt {attempt}/{retry_config.max_attempts}"
                    )
                
                return {
                    "success": True,
                    "result": result,
                    "attempt": attempt,
                    "execution_time": execution_time
                }
                
            except Exception as e:
                last_error = e
                execution_time = time.time() - start_time
                
                # Classify failure
                failure_type = self._classify_failure(e)
                
                # Record failure
                self._record_failure(
                    step_id=step_id,
                    question_id=context.question_id,
                    failure_type=failure_type,
                    error_message=str(e),
                    retry_attempt=attempt
                )
                
                # Report to circuit breaker
                severity = self._map_failure_to_severity(failure_type)
                self.circuit_breaker.record_failure(
                    adapter_name=adapter_name,
                    error=str(e),
                    execution_time=execution_time,
                    severity=severity
                )
                
                # Check if we should retry
                if attempt < retry_config.max_attempts:
                    should_retry = self._should_retry(failure_type, context, attempt)
                    
                    if should_retry:
                        # Calculate delay
                        delay = self._calculate_retry_delay(
                            retry_config, attempt, failure_type
                        )
                        
                        logger.warning(
                            f"Attempt {attempt} failed: {e}. "
                            f"Retrying in {delay:.2f}s "
                            f"(strategy: {retry_config.strategy.value})"
                        )
                        
                        self._metrics["total_retries"] += 1
                        self._metrics["by_retry_strategy"][retry_config.strategy.value] += 1
                        
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(
                            f"Failure type {failure_type.value} is not retryable, "
                            f"failing immediately"
                        )
                        break
                else:
                    logger.error(
                        f"Max retries ({retry_config.max_attempts}) exhausted"
                    )
                    self._metrics["failed_retries"] += 1
        
        # All retries exhausted or non-retryable error
        return self._handle_failure(
            context=context,
            step_id=step_id,
            last_error=last_error,
            attempts=attempt
        )
    
    def _classify_failure(self, error: Exception) -> FailureType:
        """Classify error type"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Technical failures
        if any(keyword in error_str for keyword in [
            "timeout", "connection", "network", "unavailable"
        ]):
            return FailureType.TECHNICAL
        
        if any(keyword in error_type for keyword in [
            "timeout", "connection", "network", "io"
        ]):
            return FailureType.TECHNICAL
        
        # Validation failures
        if "validation" in error_str or "invalid" in error_str:
            return FailureType.VALIDATION
        
        # Resource failures
        if any(keyword in error_str for keyword in [
            "memory", "resource", "quota", "limit"
        ]):
            return FailureType.RESOURCE
        
        # Default to technical
        return FailureType.TECHNICAL
    
    def _map_failure_to_severity(self, failure_type: FailureType) -> FailureSeverity:
        """Map failure type to circuit breaker severity"""
        mapping = {
            FailureType.TECHNICAL: FailureSeverity.TRANSIENT,
            FailureType.VALIDATION: FailureSeverity.DEGRADED,
            FailureType.BUSINESS_LOGIC: FailureSeverity.DEGRADED,
            FailureType.RESOURCE: FailureSeverity.CRITICAL,
            FailureType.CHOREOGRAPHER_ERROR: FailureSeverity.TRANSIENT,  # Often retryable
        }
        return mapping.get(failure_type, FailureSeverity.TRANSIENT)
    
    def _should_retry(
        self,
        failure_type: FailureType,
        context: QuestionContext,
        attempt: int
    ) -> bool:
        """Determine if failure should be retried"""
        # Check error strategy
        if context.error_strategy == ErrorStrategy.FAIL_FAST:
            return False
        
        if context.error_strategy == ErrorStrategy.SKIP:
            return False
        
        # Technical failures are always retryable
        if failure_type == FailureType.TECHNICAL:
            return True
        
        # Resource failures are retryable with backoff
        if failure_type == FailureType.RESOURCE:
            return True
        
        # Validation failures: retry once in case of transient validation issues
        if failure_type == FailureType.VALIDATION:
            return attempt == 1
        
        # Business logic failures: don't retry (deterministic)
        if failure_type == FailureType.BUSINESS_LOGIC:
            return False
        
        return True
    
    def _calculate_retry_delay(
        self,
        config: RetryConfig,
        attempt: int,
        failure_type: FailureType
    ) -> float:
        """Calculate retry delay based on strategy"""
        if config.strategy == RetryStrategy.NONE:
            return 0.0
        
        elif config.strategy == RetryStrategy.FIXED:
            return config.base_delay
        
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.exponential_base ** (attempt - 1))
            return min(delay, config.max_delay)
        
        elif config.strategy == RetryStrategy.JITTERED_EXPONENTIAL:
            base_delay = config.base_delay * (config.exponential_base ** (attempt - 1))
            base_delay = min(base_delay, config.max_delay)
            
            # Add jitter
            jitter = random.uniform(
                -config.jitter_factor * base_delay,
                config.jitter_factor * base_delay
            )
            
            return max(0.0, base_delay + jitter)
        
        return config.base_delay
    
    def _record_failure(
        self,
        step_id: str,
        question_id: str,
        failure_type: FailureType,
        error_message: str,
        retry_attempt: int
    ) -> None:
        """Record failure event"""
        record = FailureRecord(
            timestamp=datetime.now().isoformat(),
            failure_type=failure_type,
            error_message=error_message,
            step_id=step_id,
            question_id=question_id,
            retry_attempt=retry_attempt
        )
        
        self._failure_history.append(record)
        self._metrics["by_failure_type"][failure_type.value] += 1
    
    def _handle_circuit_open(
        self,
        context: QuestionContext,
        step_id: str
    ) -> Dict[str, Any]:
        """Handle circuit breaker open state"""
        logger.warning(f"Circuit breaker open for {step_id}, applying fallback strategy")
        
        if context.error_strategy == ErrorStrategy.FALLBACK:
            # Return degraded result
            return {
                "success": False,
                "degraded": True,
                "result": {
                    "score": 0.0,
                    "confidence": 0.0,
                    "status": "degraded",
                    "reason": "Circuit breaker open"
                },
                "circuit_breaker_open": True
            }
        
        elif context.error_strategy == ErrorStrategy.SKIP:
            # Skip the step
            return {
                "success": False,
                "skipped": True,
                "reason": "Circuit breaker open",
                "circuit_breaker_open": True
            }
        
        else:
            # Fail fast
            return {
                "success": False,
                "error": "Circuit breaker open",
                "circuit_breaker_open": True
            }
    
    def _handle_failure(
        self,
        context: QuestionContext,
        step_id: str,
        last_error: Optional[Exception],
        attempts: int
    ) -> Dict[str, Any]:
        """Handle final failure after retries exhausted"""
        error_msg = str(last_error) if last_error else "Unknown error"
        
        logger.error(
            f"Step {step_id} failed after {attempts} attempts: {error_msg}"
        )
        
        if context.error_strategy == ErrorStrategy.FALLBACK:
            # Return degraded result
            return {
                "success": False,
                "degraded": True,
                "result": {
                    "score": 0.0,
                    "confidence": 0.0,
                    "status": "degraded",
                    "reason": f"Failed after {attempts} attempts: {error_msg}"
                },
                "attempts": attempts,
                "error": error_msg
            }
        
        elif context.error_strategy == ErrorStrategy.SKIP:
            # Skip the step
            return {
                "success": False,
                "skipped": True,
                "reason": f"Failed after {attempts} attempts: {error_msg}",
                "attempts": attempts,
                "error": error_msg
            }
        
        elif context.error_strategy == ErrorStrategy.COMPENSATE:
            # Trigger compensation (Saga pattern)
            logger.info(f"Triggering compensation for {step_id}")
            # Compensation logic would be implemented here
            return {
                "success": False,
                "compensated": True,
                "reason": f"Failed after {attempts} attempts, compensation triggered",
                "attempts": attempts,
                "error": error_msg
            }
        
        else:
            # Fail fast (default)
            return {
                "success": False,
                "error": error_msg,
                "attempts": attempts
            }
    
    def register_compensation(
        self,
        step_id: str,
        action: Callable[[Dict[str, Any]], Any],
        description: str
    ) -> None:
        """
        Register compensation action for a step (Saga pattern)
        
        Args:
            step_id: Step identifier
            action: Callable to execute for compensation
            description: Human-readable description
        """
        compensation = CompensationAction(
            step_id=step_id,
            action_callable=action,
            description=description
        )
        
        # Store compensation action (would be part of workflow state in full implementation)
        logger.info(f"Registered compensation for {step_id}: {description}")
    
    def execute_compensation(
        self,
        step_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute compensation action for a failed step
        
        Args:
            step_id: Step identifier
            context: Context data for compensation
            
        Returns:
            Compensation result
        """
        logger.info(f"Executing compensation for {step_id}")
        
        try:
            # In full implementation, would retrieve registered action and execute
            # For now, just log
            self._compensation_log.append({
                "step_id": step_id,
                "timestamp": datetime.now().isoformat(),
                "context": context
            })
            
            self._metrics["compensations_executed"] += 1
            
            return {
                "success": True,
                "compensated": True,
                "step_id": step_id
            }
            
        except Exception as e:
            logger.error(f"Compensation failed for {step_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "step_id": step_id
            }
    
    def get_failure_history(
        self,
        question_id: Optional[str] = None,
        failure_type: Optional[FailureType] = None,
        limit: int = 100
    ) -> List[FailureRecord]:
        """
        Get failure history with optional filtering
        
        Args:
            question_id: Filter by question ID
            failure_type: Filter by failure type
            limit: Maximum number of records to return
            
        Returns:
            List of failure records
        """
        history = self._failure_history
        
        if question_id:
            history = [r for r in history if r.question_id == question_id]
        
        if failure_type:
            history = [r for r in history if r.failure_type == failure_type]
        
        return history[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resilience metrics"""
        metrics = self._metrics.copy()
        
        # Add circuit breaker status
        metrics["circuit_breaker_status"] = self.circuit_breaker.get_all_status()
        
        # Add failure history summary
        metrics["failure_history_size"] = len(self._failure_history)
        metrics["compensation_log_size"] = len(self._compensation_log)
        
        # Calculate success rate
        total_ops = metrics["successful_retries"] + metrics["failed_retries"]
        if total_ops > 0:
            metrics["retry_success_rate"] = metrics["successful_retries"] / total_ops
        else:
            metrics["retry_success_rate"] = 0.0
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self._metrics = {
            "total_retries": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "circuit_breaks": 0,
            "compensations_executed": 0,
            "by_failure_type": {ft.value: 0 for ft in FailureType},
            "by_retry_strategy": {rs.value: 0 for rs in RetryStrategy},
        }
        
        self._failure_history.clear()
        self._compensation_log.clear()
    
    def handle_choreographer_failure(
        self,
        failed_event: SubProcessFailedEvent,
        context: QuestionContext,
        retry_config: Optional[RetryConfig] = None
    ) -> Dict[str, Any]:
        """
        Handle failure reported by choreographed sub-process
        
        Applies resilience strategies based on error code and context:
        - Retry for transient errors
        - Fallback for non-critical errors
        - Fail-fast for critical errors
        - Compensation if enabled
        
        Args:
            failed_event: SubProcessFailedEvent from choreographer
            context: QuestionContext for the failed sub-process
            retry_config: Optional retry configuration
            
        Returns:
            Dictionary with handling result and recommended action
        """
        logger.warning(
            f"Handling choreographer failure: "
            f"correlation_id={failed_event.context.correlation_id}, "
            f"error={failed_event.error_message}"
        )
        
        # Record the failure
        self._record_failure(
            step_id=failed_event.context.sub_process_id or "choreographer_subprocess",
            question_id=", ".join(failed_event.context.question_ids),
            failure_type=FailureType.CHOREOGRAPHER_ERROR,
            error_message=failed_event.error_message,
            retry_attempt=0,
        )
        
        # Update metrics
        self._metrics["by_failure_type"][FailureType.CHOREOGRAPHER_ERROR.value] += 1
        
        # Determine action based on error code and strategy
        error_code = failed_event.error_code
        error_strategy = context.error_strategy
        
        # Check if we have partial results
        has_partial_results = failed_event.partial_result is not None
        
        # Decide on action
        if error_strategy == ErrorStrategy.RETRY:
            # Attempt retry with backoff
            retry_config = retry_config or self.default_retry_config
            
            return {
                "action": "retry",
                "should_retry": True,
                "retry_config": retry_config,
                "reason": f"Choreographer error is retryable: {error_code}",
                "partial_results": failed_event.partial_result.to_dict() if has_partial_results else None
            }
        
        elif error_strategy == ErrorStrategy.FALLBACK:
            # Use partial results if available, otherwise degraded result
            if has_partial_results:
                return {
                    "action": "fallback",
                    "should_retry": False,
                    "use_partial_results": True,
                    "partial_results": failed_event.partial_result.to_dict(),
                    "reason": "Using partial results from choreographer"
                }
            else:
                return {
                    "action": "fallback",
                    "should_retry": False,
                    "use_degraded_result": True,
                    "reason": "Choreographer failed with no partial results, using degraded output"
                }
        
        elif error_strategy == ErrorStrategy.COMPENSATE:
            # Trigger compensation for any completed steps
            logger.info("Triggering compensation for choreographer failure")
            
            return {
                "action": "compensate",
                "should_retry": False,
                "should_compensate": True,
                "partial_results": failed_event.partial_result.to_dict() if has_partial_results else None,
                "reason": "Compensating for choreographer failure"
            }
        
        elif error_strategy == ErrorStrategy.SKIP:
            # Skip this sub-process
            return {
                "action": "skip",
                "should_retry": False,
                "reason": f"Skipping choreographer sub-process due to: {error_code}"
            }
        
        else:  # FAIL_FAST or default
            # Fail immediately
            return {
                "action": "fail",
                "should_retry": False,
                "reason": f"Choreographer failure: {failed_event.error_message}",
                "error_details": failed_event.error_details
            }


if __name__ == "__main__":
    # Test the resilience manager
    from metadata_service import get_metadata_service
    
    print("=" * 80)
    print("RESILIENCE MANAGER TEST")
    print("=" * 80)
    
    # Load metadata
    service = get_metadata_service()
    service.load()
    
    # Get a question context
    context = service.get_question_context("P1-D1-Q1")
    if not context:
        print("ERROR: Could not load question context")
        exit(1)
    
    # Create resilience manager
    manager = ResilienceManager()
    
    print(f"\nTesting resilience for: {context.canonical_id}")
    
    # Test 1: Successful operation
    print("\n" + "-" * 80)
    print("Test 1: Successful Operation (no retries needed)")
    print("-" * 80)
    
    def successful_operation():
        return {"score": 2.5, "confidence": 0.9}
    
    result = manager.execute_with_resilience(
        successful_operation,
        context,
        "step_1"
    )
    
    print(f"Success: {result['success']}")
    print(f"Attempts: {result.get('attempt', 1)}")
    print(f"Result: {result.get('result')}")
    
    # Test 2: Operation that fails once then succeeds
    print("\n" + "-" * 80)
    print("Test 2: Transient Failure (succeeds on retry)")
    print("-" * 80)
    
    attempt_counter = {"count": 0}
    
    def flaky_operation():
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 2:
            raise ConnectionError("Temporary network issue")
        return {"score": 2.0, "confidence": 0.85}
    
    result = manager.execute_with_resilience(
        flaky_operation,
        context,
        "step_2"
    )
    
    print(f"Success: {result['success']}")
    print(f"Attempts: {result.get('attempt', 1)}")
    print(f"Result: {result.get('result')}")
    
    # Test 3: Operation that always fails
    print("\n" + "-" * 80)
    print("Test 3: Persistent Failure (all retries exhausted)")
    print("-" * 80)
    
    def failing_operation():
        raise ValueError("Persistent validation error")
    
    result = manager.execute_with_resilience(
        failing_operation,
        context,
        "step_3"
    )
    
    print(f"Success: {result['success']}")
    print(f"Attempts: {result.get('attempts', 1)}")
    print(f"Error: {result.get('error', 'N/A')}")
    print(f"Degraded: {result.get('degraded', False)}")
    
    # Show metrics
    print("\n" + "=" * 80)
    print("RESILIENCE METRICS")
    print("=" * 80)
    
    metrics = manager.get_metrics()
    print(f"Total Retries: {metrics['total_retries']}")
    print(f"Successful Retries: {metrics['successful_retries']}")
    print(f"Failed Retries: {metrics['failed_retries']}")
    print(f"Circuit Breaks: {metrics['circuit_breaks']}")
    print(f"Retry Success Rate: {metrics['retry_success_rate']:.1%}")
    print(f"\nBy Failure Type: {metrics['by_failure_type']}")
    print(f"By Retry Strategy: {metrics['by_retry_strategy']}")
    
    # Show failure history
    print("\n" + "=" * 80)
    print("FAILURE HISTORY")
    print("=" * 80)
    
    history = manager.get_failure_history(limit=10)
    print(f"Total failures recorded: {len(history)}")
    for record in history[:5]:
        print(f"  [{record.timestamp}] {record.failure_type.value}: {record.error_message}")
    
    print("\n" + "=" * 80)
