"""
Module Controller - Standardized Component Invocation Interface
================================================================

Provides standardized interface for invoking orchestrated components with
QuestionContext injection, result normalization, and adapter management.

Key Features:
- Standardized invocation pattern with context injection
- Result normalization from ModuleResult to orchestrator format
- Adapter availability checking
- Performance tracking
- Versioned API contract enforcement
- Integration with ResilienceManager for fault tolerance

Author: FARFAN 3.0 - Industrial Orchestrator
Version: 1.0.0
Python: 3.10+
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from metadata_service import QuestionContext
from validation_engine import ValidationEngine, ValidationResult
from resilience_manager import ResilienceManager

logger = logging.getLogger(__name__)


class InvocationStatus(Enum):
    """Status of component invocation"""
    SUCCESS = "success"
    FAILURE = "failure"
    DEGRADED = "degraded"
    SKIPPED = "skipped"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class InvocationResult:
    """
    Standardized result from component invocation
    
    This normalizes ModuleResult and adds orchestrator-specific metadata
    """
    status: InvocationStatus
    module_name: str
    method_name: str
    output: Dict[str, Any]
    validation_result: Optional[ValidationResult] = None
    execution_time: float = 0.0
    resilience_applied: bool = False
    retry_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if invocation was successful"""
        return self.status == InvocationStatus.SUCCESS
    
    @property
    def is_validated(self) -> bool:
        """Check if output passed validation"""
        return (
            self.validation_result is not None 
            and self.validation_result.is_valid
        )


class ModuleController:
    """
    Standardized controller for module invocations
    
    Features:
    - Context injection into module calls
    - Result normalization
    - Validation integration
    - Resilience integration
    - Performance tracking
    - Version enforcement
    """
    
    def __init__(
        self,
        module_registry: Any,
        validation_engine: Optional[ValidationEngine] = None,
        resilience_manager: Optional[ResilienceManager] = None,
        enable_validation: bool = True,
        enable_resilience: bool = True
    ):
        """
        Initialize module controller
        
        Args:
            module_registry: ModuleAdapterRegistry instance
            validation_engine: ValidationEngine instance (creates new if None)
            resilience_manager: ResilienceManager instance (creates new if None)
            enable_validation: Enable automatic validation
            enable_resilience: Enable resilience features
        """
        self.module_registry = module_registry
        self.validation_engine = validation_engine or ValidationEngine()
        self.resilience_manager = resilience_manager or ResilienceManager()
        self.enable_validation = enable_validation
        self.enable_resilience = enable_resilience
        
        # Performance tracking
        self._invocation_stats: Dict[str, Any] = {
            "total_invocations": 0,
            "successful": 0,
            "failed": 0,
            "validated": 0,
            "validation_failed": 0,
            "by_module": {},
        }
        
        logger.info(
            f"ModuleController initialized: "
            f"validation={'ON' if enable_validation else 'OFF'}, "
            f"resilience={'ON' if enable_resilience else 'OFF'}"
        )
    
    def invoke(
        self,
        module_name: str,
        method_name: str,
        context: QuestionContext,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        skip_validation: bool = False,
        skip_resilience: bool = False
    ) -> InvocationResult:
        """
        Invoke a module method with full orchestrator support
        
        Args:
            module_name: Name of module adapter to invoke
            method_name: Method name to call
            context: QuestionContext for this invocation
            args: Positional arguments for method
            kwargs: Keyword arguments for method
            skip_validation: Skip validation for this call
            skip_resilience: Skip resilience features for this call
            
        Returns:
            InvocationResult with normalized output and validation
        """
        start_time = time.time()
        
        args = args or []
        kwargs = kwargs or {}
        
        # Inject context into kwargs
        kwargs_with_context = self._inject_context(kwargs, context)
        
        logger.debug(
            f"Invoking {module_name}.{method_name} for {context.question_id}"
        )
        
        # Check module availability
        available_modules = self.module_registry.get_available_modules()
        if module_name not in available_modules:
            logger.error(f"Module {module_name} not available")
            return self._create_failure_result(
                module_name=module_name,
                method_name=method_name,
                error=f"Module {module_name} not available",
                execution_time=time.time() - start_time
            )
        
        # Create invocation operation
        def invoke_operation():
            return self.module_registry.execute_module_method(
                module_name=module_name,
                method_name=method_name,
                args=args,
                kwargs=kwargs_with_context
            )
        
        # Execute with or without resilience
        if self.enable_resilience and not skip_resilience:
            resilience_result = self.resilience_manager.execute_with_resilience(
                operation=invoke_operation,
                context=context,
                step_id=f"{module_name}.{method_name}"
            )
            
            if not resilience_result.get("success", False):
                return self._create_failure_result(
                    module_name=module_name,
                    method_name=method_name,
                    error=resilience_result.get("error", "Unknown error"),
                    execution_time=resilience_result.get("execution_time", time.time() - start_time),
                    resilience_applied=True,
                    retry_count=resilience_result.get("attempts", 1) - 1
                )
            
            module_result = resilience_result["result"]
            retry_count = resilience_result.get("attempt", 1) - 1
            resilience_applied = retry_count > 0
        else:
            try:
                module_result = invoke_operation()
                retry_count = 0
                resilience_applied = False
            except Exception as e:
                logger.error(
                    f"Invocation failed: {module_name}.{method_name}: {e}",
                    exc_info=True
                )
                return self._create_failure_result(
                    module_name=module_name,
                    method_name=method_name,
                    error=str(e),
                    execution_time=time.time() - start_time
                )
        
        # Normalize module result
        normalized_output = self._normalize_module_result(module_result)
        
        # Validate output if enabled
        validation_result = None
        if self.enable_validation and not skip_validation:
            validation_result = self.validation_engine.validate(
                normalized_output,
                context
            )
            
            if not validation_result.is_valid:
                logger.warning(
                    f"Validation failed for {module_name}.{method_name}: "
                    f"{validation_result.error_count} errors"
                )
        
        # Determine final status
        if normalized_output.get("status") == "failed":
            status = InvocationStatus.FAILURE
        elif validation_result and not validation_result.is_valid:
            status = InvocationStatus.FAILURE
        else:
            status = InvocationStatus.SUCCESS
        
        execution_time = time.time() - start_time
        
        # Create result
        result = InvocationResult(
            status=status,
            module_name=module_name,
            method_name=method_name,
            output=normalized_output,
            validation_result=validation_result,
            execution_time=execution_time,
            resilience_applied=resilience_applied,
            retry_count=retry_count,
            errors=normalized_output.get("errors", []),
            warnings=normalized_output.get("warnings", []),
            metadata={
                "question_id": context.question_id,
                "dimension": context.dimension,
                "policy_area": context.policy_area,
                "context_version": context.version,
            }
        )
        
        # Update stats
        self._update_stats(result)
        
        logger.debug(
            f"Invocation complete: {module_name}.{method_name} - "
            f"{status.value} in {execution_time:.3f}s"
        )
        
        return result
    
    def _inject_context(
        self,
        kwargs: Dict[str, Any],
        context: QuestionContext
    ) -> Dict[str, Any]:
        """
        Inject QuestionContext into kwargs
        
        Adds context as 'question_context' parameter if not already present
        """
        kwargs_with_context = kwargs.copy()
        
        # Add context if not already present
        if "question_context" not in kwargs_with_context:
            kwargs_with_context["question_context"] = context
        
        # Add commonly used context fields as top-level parameters
        if "question_id" not in kwargs_with_context:
            kwargs_with_context["question_id"] = context.question_id
        
        if "dimension" not in kwargs_with_context:
            kwargs_with_context["dimension"] = context.dimension
        
        if "max_score" not in kwargs_with_context:
            kwargs_with_context["max_score"] = context.max_score
        
        return kwargs_with_context
    
    def _normalize_module_result(self, module_result: Any) -> Dict[str, Any]:
        """
        Normalize ModuleResult to standardized dictionary format
        
        Handles both ModuleResult objects and plain dictionaries
        """
        if hasattr(module_result, "to_dict"):
            # ModuleResult object
            result_dict = {
                "module_name": module_result.module_name,
                "class_name": module_result.class_name,
                "method_name": module_result.method_name,
                "status": module_result.status,
                "data": module_result.data,
                "evidence": module_result.evidence,
                "confidence": module_result.confidence,
                "execution_time": module_result.execution_time,
                "errors": module_result.errors,
                "warnings": module_result.warnings,
                "metadata": module_result.metadata,
            }
        elif isinstance(module_result, dict):
            # Already a dictionary
            result_dict = module_result
        else:
            # Unknown format
            logger.warning(f"Unknown module result format: {type(module_result)}")
            result_dict = {
                "status": "completed",
                "data": {"raw_result": module_result},
                "evidence": [],
                "confidence": 0.5,
                "errors": [],
                "warnings": ["Result format not recognized"],
            }
        
        return result_dict
    
    def _create_failure_result(
        self,
        module_name: str,
        method_name: str,
        error: str,
        execution_time: float,
        resilience_applied: bool = False,
        retry_count: int = 0
    ) -> InvocationResult:
        """Create a failure InvocationResult"""
        return InvocationResult(
            status=InvocationStatus.FAILURE,
            module_name=module_name,
            method_name=method_name,
            output={
                "status": "failed",
                "data": {},
                "evidence": [],
                "confidence": 0.0,
                "errors": [error],
            },
            execution_time=execution_time,
            resilience_applied=resilience_applied,
            retry_count=retry_count,
            errors=[error]
        )
    
    def _update_stats(self, result: InvocationResult) -> None:
        """Update invocation statistics"""
        self._invocation_stats["total_invocations"] += 1
        
        if result.is_success:
            self._invocation_stats["successful"] += 1
        else:
            self._invocation_stats["failed"] += 1
        
        if result.is_validated:
            self._invocation_stats["validated"] += 1
        elif result.validation_result and not result.validation_result.is_valid:
            self._invocation_stats["validation_failed"] += 1
        
        # Per-module stats
        module_key = f"{result.module_name}.{result.method_name}"
        if module_key not in self._invocation_stats["by_module"]:
            self._invocation_stats["by_module"][module_key] = {
                "calls": 0,
                "success": 0,
                "failure": 0,
                "avg_time": 0.0,
                "total_time": 0.0
            }
        
        module_stats = self._invocation_stats["by_module"][module_key]
        module_stats["calls"] += 1
        module_stats["total_time"] += result.execution_time
        module_stats["avg_time"] = module_stats["total_time"] / module_stats["calls"]
        
        if result.is_success:
            module_stats["success"] += 1
        else:
            module_stats["failure"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get invocation statistics"""
        stats = self._invocation_stats.copy()
        
        # Add success rate
        total = stats["total_invocations"]
        if total > 0:
            stats["success_rate"] = stats["successful"] / total
            stats["failure_rate"] = stats["failed"] / total
            stats["validation_rate"] = stats["validated"] / total
        else:
            stats["success_rate"] = 0.0
            stats["failure_rate"] = 0.0
            stats["validation_rate"] = 0.0
        
        return stats
    
    def get_available_modules(self) -> List[str]:
        """Get list of available modules"""
        return self.module_registry.get_available_modules()
    
    def get_module_status(self) -> Dict[str, bool]:
        """Get availability status of all modules"""
        return self.module_registry.get_module_status()


if __name__ == "__main__":
    # Test the module controller
    from metadata_service import get_metadata_service
    
    print("=" * 80)
    print("MODULE CONTROLLER TEST")
    print("=" * 80)
    
    # Load metadata
    service = get_metadata_service()
    service.load()
    
    # Get a question context
    context = service.get_question_context("P1-D1-Q1")
    if not context:
        print("ERROR: Could not load question context")
        exit(1)
    
    print(f"\nTesting invocation for: {context.canonical_id}")
    
    # Create module registry (mock for testing)
    try:
        from modules_adapters import ModuleAdapterRegistry
        registry = ModuleAdapterRegistry()
        print(f"✓ Loaded ModuleAdapterRegistry with {len(registry.adapters)} adapters")
    except Exception as e:
        print(f"✗ Could not load ModuleAdapterRegistry: {e}")
        print("  (This is expected if dependencies are not installed)")
        exit(0)
    
    # Create controller
    controller = ModuleController(
        module_registry=registry,
        enable_validation=True,
        enable_resilience=True
    )
    
    # Test invocation
    print("\n" + "-" * 80)
    print("Test: Module Invocation with Context Injection")
    print("-" * 80)
    
    available = controller.get_available_modules()
    print(f"\nAvailable modules: {len(available)}")
    
    if available:
        # Try to invoke a simple method
        module_name = available[0]
        print(f"\nInvoking {module_name}...")
        
        try:
            result = controller.invoke(
                module_name=module_name,
                method_name="get_capabilities",  # Common method
                context=context,
                args=[],
                kwargs={}
            )
            
            print(f"Status: {result.status.value}")
            print(f"Success: {result.is_success}")
            print(f"Validated: {result.is_validated}")
            print(f"Execution Time: {result.execution_time:.4f}s")
            print(f"Resilience Applied: {result.resilience_applied}")
            print(f"Retry Count: {result.retry_count}")
            
            if result.errors:
                print(f"\nErrors: {result.errors}")
            
        except Exception as e:
            print(f"Invocation error: {e}")
    
    # Show stats
    print("\n" + "=" * 80)
    print("MODULE CONTROLLER STATISTICS")
    print("=" * 80)
    
    stats = controller.get_stats()
    print(f"Total Invocations: {stats['total_invocations']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Validated: {stats['validated']}")
    print(f"Validation Rate: {stats['validation_rate']:.1%}")
    
    print("\n" + "=" * 80)
