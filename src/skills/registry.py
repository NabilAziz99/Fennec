"""
Skills registry for dynamic knowledge injection.

Loads skill content from markdown files (compatible with Strix's skill format)
and injects them into agent prompts based on the hypothesis requirements.
"""

import os
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..state.hypothesis import Hypothesis


class SkillsRegistry:
    """
    Manages loading of skill knowledge from markdown files.

    Skills are markdown files with optional YAML frontmatter containing
    specialized knowledge about vulnerability types, frameworks, etc.

    Directory structure:
    skills/
    ├── vulnerabilities/
    │   ├── sql_injection.md
    │   ├── xss.md
    │   └── ...
    ├── frameworks/
    │   ├── fastapi.md
    │   └── ...
    └── technologies/
        ├── firebase.md
        └── ...
    """

    def __init__(self, skills_dirs: list[str] = None):
        """
        Initialize the registry.

        Args:
            skills_dirs: List of directories to search for skills.
                         If None, uses default locations.
        """
        if skills_dirs is None:
            # Default location: local skills in knowledge/
            skills_dir = Path(__file__).parent / "knowledge"
            skills_dirs = [str(skills_dir)]

        self.skills_dirs = [Path(d) for d in skills_dirs if Path(d).exists()]
        self._cache: dict[str, str] = {}
        self._available_skills: Optional[set[str]] = None

    def get_skill(self, skill_name: str) -> Optional[str]:
        """
        Load a skill's content by name.

        Args:
            skill_name: Name of the skill (e.g., "sql_injection", "xss")

        Returns:
            The skill content (markdown without frontmatter) or None if not found
        """
        # Normalize name
        skill_name = skill_name.lower().replace("-", "_").replace(" ", "_")

        # Check cache
        if skill_name in self._cache:
            return self._cache[skill_name]

        # Search in all skill directories
        subdirs = ["vulnerabilities", "frameworks", "technologies", "protocols", "cloud", "reconnaissance"]

        for skills_dir in self.skills_dirs:
            # Try direct match
            direct_path = skills_dir / f"{skill_name}.md"
            if direct_path.exists():
                content = self._load_skill_file(direct_path)
                if content:
                    self._cache[skill_name] = content
                    return content

            # Try in subdirectories
            for subdir in subdirs:
                path = skills_dir / subdir / f"{skill_name}.md"
                if path.exists():
                    content = self._load_skill_file(path)
                    if content:
                        self._cache[skill_name] = content
                        return content

        return None

    def _load_skill_file(self, path: Path) -> Optional[str]:
        """Load and process a skill file, stripping YAML frontmatter."""
        try:
            content = path.read_text(encoding="utf-8")

            # Strip YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()

            return content
        except Exception:
            return None

    def get_available_skills(self) -> set[str]:
        """Get all available skill names."""
        if self._available_skills is not None:
            return self._available_skills

        skills = set()
        subdirs = ["vulnerabilities", "frameworks", "technologies", "protocols", "cloud", "reconnaissance"]

        for skills_dir in self.skills_dirs:
            # Check root
            for path in skills_dir.glob("*.md"):
                if path.name != "README.md":
                    skills.add(path.stem.lower())

            # Check subdirs
            for subdir in subdirs:
                subdir_path = skills_dir / subdir
                if subdir_path.exists():
                    for path in subdir_path.glob("*.md"):
                        if path.name != "README.md":
                            skills.add(path.stem.lower())

        self._available_skills = skills
        return skills

    def get_skills_for_hypothesis(self, hypothesis: "Hypothesis") -> str:
        """
        Get combined skill knowledge for a hypothesis.

        Args:
            hypothesis: The hypothesis with skills to load

        Returns:
            Combined skill content wrapped in XML tags
        """
        skills_content = []

        for skill_name in hypothesis.skills:
            content = self.get_skill(skill_name)
            if content:
                # Wrap in XML tags for clear separation
                skills_content.append(
                    f'<skill name="{skill_name}">\n{content}\n</skill>'
                )

        if skills_content:
            return "<specialized_knowledge>\n" + "\n\n".join(skills_content) + "\n</specialized_knowledge>"

        return ""

    def validate_skills(self, skill_names: list[str]) -> tuple[list[str], list[str]]:
        """
        Validate a list of skill names.

        Returns:
            Tuple of (valid_skills, invalid_skills)
        """
        available = self.get_available_skills()
        valid = []
        invalid = []

        for name in skill_names:
            normalized = name.lower().replace("-", "_").replace(" ", "_")
            if normalized in available or self.get_skill(normalized):
                valid.append(normalized)
            else:
                invalid.append(name)

        return valid, invalid


# Global instance
_registry: Optional[SkillsRegistry] = None


def get_skills_registry() -> SkillsRegistry:
    """Get or create the global skills registry."""
    global _registry
    if _registry is None:
        _registry = SkillsRegistry()
    return _registry


def get_skill(skill_name: str) -> Optional[str]:
    """Convenience function to get a skill by name."""
    return get_skills_registry().get_skill(skill_name)


def get_skills_for_hypothesis(hypothesis: "Hypothesis") -> str:
    """Convenience function to get skills for a hypothesis."""
    return get_skills_registry().get_skills_for_hypothesis(hypothesis)
