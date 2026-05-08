from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BetaMode(str, Enum):
    OFF = "off"
    SHADOW = "shadow"
    ACTIVE = "active"


class ComplexityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class SelectionItem:
    id: str
    relevance: float = 0.0
    reason: str = ""


@dataclass
class SelectorDecision:
    selected_tools: list[str] = field(default_factory=list)
    selected_skills: list[str] = field(default_factory=list)
    selected_tool_items: list[SelectionItem] = field(default_factory=list)
    selected_skill_items: list[SelectionItem] = field(default_factory=list)
    selected_tool_relevance: dict[str, float] = field(default_factory=dict)
    selected_skill_relevance: dict[str, float] = field(default_factory=dict)
    selected_tool_reasons: dict[str, str] = field(default_factory=dict)
    selected_skill_reasons: dict[str, str] = field(default_factory=dict)
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    confidence: float = 0.0
    reason: str = ""


@dataclass
class RouterDecision:
    provider: Optional[str] = None
    model: Optional[str] = None
    selected_tools: list[str] = field(default_factory=list)
    selected_skills: list[str] = field(default_factory=list)
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    confidence: float = 0.0
    reason: str = ""


@dataclass
class BetaDecisionLog:
    timestamp: str
    mode: BetaMode
    prompt_hash: str
    selector_model: str
    router_enabled: bool
    selected_provider: Optional[str]
    selected_model: Optional[str]
    selected_tools: list[str]
    selected_skills: list[str]
    complexity: ComplexityLevel
    confidence: float
    fallback_used: bool
    fallback_reason: Optional[str]
    normal_estimated_context_tokens: int = 0
    beta_estimated_context_tokens: int = 0
    estimated_tokens_saved: int = 0
    selected_tools_count: int = 0
    available_tools_count: int = 0
    selected_skills_count: int = 0
    available_skills_count: int = 0
    baseline_required_tools: list[str] = field(default_factory=list)
    llm_selected_tools: list[str] = field(default_factory=list)
    llm_added_tools: list[str] = field(default_factory=list)
    pruned_optional_tools: list[str] = field(default_factory=list)

