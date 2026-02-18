# reasoning/__init__.py
# Hybrid AI: First-Principles Reasoning Module
# Integrates symbolic reasoning with the existing Engram memory system

from reasoning.bridge import SemanticBridge
from reasoning.query_router import QueryRouter
from reasoning.axiom_store import AxiomStore
from reasoning.symbolic_reasoning import ReasoningEngine
from reasoning.translator_gate import SecureTranslatorGate
from reasoning.awake_engine import AwakeEngine

__all__ = [
    'SemanticBridge',
    'QueryRouter', 
    'AxiomStore',
    'ReasoningEngine',
    'SecureTranslatorGate',
    'AwakeEngine',
]
