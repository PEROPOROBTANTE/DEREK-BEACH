"""
Snapshot Contract (SC) - Immutable Snapshots with Reproducible Summaries
========================================================================

Guarantees immutable snapshots and that reproduction produces identical summaries.
In the first stage, snapshot_manager enforces:
    σ = {standards_hash, corpus_hash, embedding_hash, index_hash}

Key Guarantees:
1. Immutability: Snapshots cannot be modified after creation
2. Reproducibility: Same snapshot produces identical summaries
3. Hash integrity: Four-part sigma ensures complete state capture
4. Verification: Can verify snapshot integrity via hash comparison

Author: FARFAN 3.0 - Contract Enforcement System
Version: 1.0.0
Python: 3.11+
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SnapshotSigma:
    """
    Snapshot sigma (Σ) - Four-part hash capturing complete state
    
    Components:
    - standards_hash: Hash of standards/rules used
    - corpus_hash: Hash of document corpus
    - embedding_hash: Hash of embeddings/vectors
    - index_hash: Hash of indices/structures
    """
    standards_hash: str
    corpus_hash: str
    embedding_hash: str
    index_hash: str
    
    @staticmethod
    def compute_from_components(
        standards: Any,
        corpus: Any,
        embeddings: Any,
        index: Any
    ) -> 'SnapshotSigma':
        """
        Compute sigma from components
        
        Args:
            standards: Standards data to hash
            corpus: Corpus data to hash
            embeddings: Embeddings data to hash
            index: Index data to hash
            
        Returns:
            SnapshotSigma with computed hashes
        """
        return SnapshotSigma(
            standards_hash=_hash_component(standards, "standards"),
            corpus_hash=_hash_component(corpus, "corpus"),
            embedding_hash=_hash_component(embeddings, "embeddings"),
            index_hash=_hash_component(index, "index")
        )
    
    def to_composite_hash(self) -> str:
        """
        Compute composite hash from all four components
        
        Returns:
            Single hash representing entire sigma
        """
        combined = f"{self.standards_hash}|{self.corpus_hash}|{self.embedding_hash}|{self.index_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """
        Verify sigma integrity (all hashes present and valid format)
        
        Returns:
            True if sigma is valid
        """
        hashes = [
            self.standards_hash,
            self.corpus_hash,
            self.embedding_hash,
            self.index_hash
        ]
        
        # All must be non-empty hex strings
        for h in hashes:
            if not h or len(h) != 64:  # SHA-256 produces 64 hex chars
                return False
            try:
                int(h, 16)  # Verify hex format
            except ValueError:
                return False
        
        return True


@dataclass(frozen=True)
class ImmutableSnapshot:
    """
    Immutable snapshot of system state
    
    Frozen dataclass ensuring no modifications after creation.
    Contains all state needed for reproducibility.
    """
    snapshot_id: str
    sigma: SnapshotSigma
    timestamp: str
    version: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # State components (frozen ensures immutability)
    standards_data: Any = None
    corpus_data: Any = None
    embeddings_data: Any = None
    index_data: Any = None
    
    def verify_sigma(self) -> bool:
        """
        Verify sigma matches actual data
        
        Returns:
            True if sigma correctly represents snapshot data
        """
        if not self.sigma.verify_integrity():
            logger.error("Sigma integrity check failed")
            return False
        
        # Recompute sigma from data
        computed_sigma = SnapshotSigma.compute_from_components(
            standards=self.standards_data,
            corpus=self.corpus_data,
            embeddings=self.embeddings_data,
            index=self.index_data
        )
        
        # Compare
        if computed_sigma != self.sigma:
            logger.error("Sigma verification failed: mismatch with actual data")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize snapshot to dictionary"""
        return {
            "snapshot_id": self.snapshot_id,
            "sigma": {
                "standards_hash": self.sigma.standards_hash,
                "corpus_hash": self.sigma.corpus_hash,
                "embedding_hash": self.sigma.embedding_hash,
                "index_hash": self.sigma.index_hash,
                "composite_hash": self.sigma.to_composite_hash(),
            },
            "timestamp": self.timestamp,
            "version": self.version,
            "metadata": self.metadata,
        }
    
    def produce_summary(self) -> Dict[str, Any]:
        """
        Produce reproducible summary from snapshot
        
        Returns:
            Summary dictionary with deterministic structure
        """
        return {
            "snapshot_id": self.snapshot_id,
            "sigma_composite": self.sigma.to_composite_hash(),
            "timestamp": self.timestamp,
            "version": self.version,
            "component_hashes": {
                "standards": self.sigma.standards_hash,
                "corpus": self.sigma.corpus_hash,
                "embeddings": self.sigma.embedding_hash,
                "index": self.sigma.index_hash,
            },
            "metadata_hash": _hash_component(self.metadata, "metadata"),
        }


class SnapshotContract:
    """
    Snapshot Contract enforcer
    
    Guarantees:
    - Snapshot immutability
    - Summary reproducibility
    - Hash integrity via sigma
    """
    
    def __init__(self):
        """Initialize snapshot contract"""
        self._verified_snapshots: Dict[str, ImmutableSnapshot] = {}
        logger.info("Initialized SnapshotContract")
    
    def verify_immutability(self, snapshot: ImmutableSnapshot) -> bool:
        """
        Verify snapshot immutability
        
        Args:
            snapshot: Snapshot to verify
            
        Returns:
            True if snapshot is properly immutable
        """
        # Check that snapshot is frozen dataclass
        if not hasattr(snapshot, '__dataclass_fields__'):
            logger.error("Not a dataclass")
            return False
        
        # Check if frozen attribute is set
        if not snapshot.__dataclass_fields__['snapshot_id'].metadata.get('frozen', False):
            # Try alternative check via setattr
            try:
                # Attempt modification - should raise error for frozen dataclass
                snapshot.snapshot_id = 'modified'
                logger.error("Snapshot is mutable (modification succeeded)")
                return False
            except (AttributeError, dataclasses.FrozenInstanceError):
                # Expected - snapshot is frozen
                pass
        
        # Snapshot is immutable (frozen dataclass)
        logger.debug("Snapshot immutability verified")
        return True
    
    def verify_reproducibility(
        self,
        snapshot: ImmutableSnapshot,
        num_trials: int = 3
    ) -> bool:
        """
        Verify summary reproducibility
        
        Args:
            snapshot: Snapshot to test
            num_trials: Number of reproduction trials
            
        Returns:
            True if all summaries are identical
        """
        summaries = []
        
        for i in range(num_trials):
            summary = snapshot.produce_summary()
            summaries.append(summary)
            logger.debug(f"Trial {i+1} summary hash: {summary['sigma_composite'][:16]}")
        
        # All summaries should be identical
        first = json.dumps(summaries[0], sort_keys=True)
        for i, summary in enumerate(summaries[1:], start=2):
            current = json.dumps(summary, sort_keys=True)
            if current != first:
                logger.error(f"Reproducibility failed: trial {i} differs")
                return False
        
        logger.info(f"Summary reproducibility verified ({num_trials} trials)")
        return True
    
    def verify_sigma_integrity(self, snapshot: ImmutableSnapshot) -> bool:
        """
        Verify sigma integrity
        
        Args:
            snapshot: Snapshot to verify
            
        Returns:
            True if sigma is valid and matches data
        """
        # Check sigma format
        if not snapshot.sigma.verify_integrity():
            return False
        
        # Verify sigma matches actual data
        return snapshot.verify_sigma()
    
    def verify_contract(self, snapshot: ImmutableSnapshot) -> bool:
        """
        Verify all snapshot contract guarantees
        
        Args:
            snapshot: Snapshot to verify
            
        Returns:
            True if all guarantees are met
        """
        # 1. Verify immutability
        if not self.verify_immutability(snapshot):
            logger.error("Contract violation: Immutability check failed")
            return False
        
        # 2. Verify reproducibility
        if not self.verify_reproducibility(snapshot):
            logger.error("Contract violation: Reproducibility check failed")
            return False
        
        # 3. Verify sigma integrity
        if not self.verify_sigma_integrity(snapshot):
            logger.error("Contract violation: Sigma integrity check failed")
            return False
        
        logger.info(f"Snapshot contract verified for {snapshot.snapshot_id}")
        return True


class SnapshotManager:
    """
    Snapshot manager enforcing snapshot contract
    
    Creates and manages immutable snapshots with sigma enforcement.
    """
    
    def __init__(self, contract: Optional[SnapshotContract] = None):
        """
        Initialize snapshot manager
        
        Args:
            contract: Optional snapshot contract enforcer
        """
        self.contract = contract or SnapshotContract()
        self._snapshots: Dict[str, ImmutableSnapshot] = {}
        
        logger.info("Initialized SnapshotManager with contract enforcement")
    
    def create_snapshot(
        self,
        snapshot_id: str,
        standards: Any,
        corpus: Any,
        embeddings: Any,
        index: Any,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = "1.0.0"
    ) -> ImmutableSnapshot:
        """
        Create immutable snapshot with sigma enforcement
        
        Args:
            snapshot_id: Unique snapshot identifier
            standards: Standards data
            corpus: Corpus data
            embeddings: Embeddings data
            index: Index data
            metadata: Optional metadata
            version: Snapshot version
            
        Returns:
            ImmutableSnapshot with verified sigma
            
        Raises:
            ValueError: If snapshot contract is violated
        """
        # Compute sigma from components
        sigma = SnapshotSigma.compute_from_components(
            standards=standards,
            corpus=corpus,
            embeddings=embeddings,
            index=index
        )
        
        # Create immutable snapshot
        snapshot = ImmutableSnapshot(
            snapshot_id=snapshot_id,
            sigma=sigma,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=version,
            metadata=metadata or {},
            standards_data=standards,
            corpus_data=corpus,
            embeddings_data=embeddings,
            index_data=index
        )
        
        # Verify contract
        if not self.contract.verify_contract(snapshot):
            raise ValueError(f"Snapshot contract violation for {snapshot_id}")
        
        # Store verified snapshot
        self._snapshots[snapshot_id] = snapshot
        
        logger.info(f"Created and verified snapshot {snapshot_id}")
        return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[ImmutableSnapshot]:
        """Get snapshot by ID"""
        return self._snapshots.get(snapshot_id)
    
    def verify_snapshot_reproducibility(
        self,
        snapshot_id: str,
        num_trials: int = 3
    ) -> bool:
        """
        Verify snapshot can reproduce identical summaries
        
        Args:
            snapshot_id: Snapshot to verify
            num_trials: Number of reproduction trials
            
        Returns:
            True if reproducibility is verified
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.error(f"Snapshot {snapshot_id} not found")
            return False
        
        return self.contract.verify_reproducibility(snapshot, num_trials)


def _hash_component(component: Any, component_name: str) -> str:
    """
    Hash a component for sigma computation
    
    Args:
        component: Component to hash
        component_name: Name for logging
        
    Returns:
        SHA-256 hash of component
    """
    try:
        # Convert to JSON for deterministic hashing
        if isinstance(component, (dict, list)):
            component_str = json.dumps(component, sort_keys=True)
        elif isinstance(component, str):
            component_str = component
        elif component is None:
            component_str = "null"
        else:
            component_str = str(component)
        
        hash_obj = hashlib.sha256(component_str.encode('utf-8'))
        return hash_obj.hexdigest()
    
    except Exception as e:
        logger.warning(f"Failed to hash {component_name}: {e}, using empty hash")
        return hashlib.sha256(b"").hexdigest()


# Import for frozen check
import dataclasses


if __name__ == "__main__":
    # Test the snapshot contract
    print("=" * 80)
    print("SNAPSHOT CONTRACT (SC) TEST")
    print("=" * 80)
    
    # Create test data
    standards = {"rule_1": "value_1", "rule_2": "value_2"}
    corpus = ["doc1", "doc2", "doc3"]
    embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
    index = {"doc1": 0, "doc2": 1, "doc3": 2}
    
    # Test 1: Create snapshot with sigma
    print("\nTest 1: Snapshot Creation with Sigma")
    manager = SnapshotManager()
    snapshot = manager.create_snapshot(
        snapshot_id="test_snapshot_001",
        standards=standards,
        corpus=corpus,
        embeddings=embeddings,
        index=index,
        metadata={"creator": "test", "purpose": "validation"}
    )
    print(f"  Snapshot ID: {snapshot.snapshot_id}")
    print(f"  Standards Hash: {snapshot.sigma.standards_hash[:16]}...")
    print(f"  Corpus Hash: {snapshot.sigma.corpus_hash[:16]}...")
    print(f"  Embeddings Hash: {snapshot.sigma.embedding_hash[:16]}...")
    print(f"  Index Hash: {snapshot.sigma.index_hash[:16]}...")
    print(f"  Composite Hash: {snapshot.sigma.to_composite_hash()[:16]}...")
    
    # Test 2: Verify immutability
    print("\nTest 2: Immutability Verification")
    try:
        snapshot.snapshot_id = "modified"  # Should fail
        print("  ✗ Snapshot is mutable (FAILED)")
    except (AttributeError, dataclasses.FrozenInstanceError):
        print("  ✓ Snapshot is immutable (PASSED)")
    
    # Test 3: Verify reproducibility
    print("\nTest 3: Summary Reproducibility")
    summary1 = snapshot.produce_summary()
    summary2 = snapshot.produce_summary()
    summary3 = snapshot.produce_summary()
    
    match = (
        summary1['sigma_composite'] == summary2['sigma_composite'] == 
        summary3['sigma_composite']
    )
    print(f"  Summary 1 hash: {summary1['sigma_composite'][:16]}...")
    print(f"  Summary 2 hash: {summary2['sigma_composite'][:16]}...")
    print(f"  Summary 3 hash: {summary3['sigma_composite'][:16]}...")
    print(f"  All identical: {match}")
    
    # Test 4: Verify sigma integrity
    print("\nTest 4: Sigma Integrity Verification")
    sigma_valid = snapshot.sigma.verify_integrity()
    sigma_matches = snapshot.verify_sigma()
    print(f"  Sigma format valid: {sigma_valid}")
    print(f"  Sigma matches data: {sigma_matches}")
    
    # Test 5: Full contract verification
    print("\nTest 5: Full Contract Verification")
    contract = SnapshotContract()
    verified = contract.verify_contract(snapshot)
    print(f"  Contract verified: {verified}")
    
    print("\n" + "=" * 80)
