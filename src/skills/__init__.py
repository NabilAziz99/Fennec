"""
Skills module for dynamic knowledge injection.
"""

from .registry import (
    SkillsRegistry,
    get_skills_registry,
    get_skill,
    get_skills_for_hypothesis,
)

__all__ = [
    "SkillsRegistry",
    "get_skills_registry",
    "get_skill",
    "get_skills_for_hypothesis",
]
