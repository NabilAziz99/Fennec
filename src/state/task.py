"""
Task system for agent-internal step tracking.

Matches Claude Code's task system:
- task_create: Create a new task
- task_update: Update an existing task (status, subject, dependencies, etc.)
- task_get: Get a task by ID
- task_list: List all tasks

Each task has:
- id, subject, description, status, activeForm
- owner, metadata
- blocks/blockedBy (dependency tracking)
"""

from dataclasses import dataclass, field
from typing import Optional, Any
import uuid


@dataclass
class Task:
    """
    A task in the agent's task list.

    Matches Claude Code's schema:
    - subject: imperative title ("Run tests")
    - description: detailed requirements
    - activeForm: present continuous for spinner ("Running tests")
    - status: pending | in_progress | completed
    - owner: agent name if assigned
    - metadata: arbitrary key-value pairs
    - blocks: task IDs that cannot start until this completes
    - blockedBy: task IDs that must complete before this can start
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    subject: str = ""
    description: str = ""
    status: str = "pending"  # "pending" | "in_progress" | "completed"
    activeForm: str = ""
    owner: str = ""
    metadata: dict = field(default_factory=dict)
    blocks: list[str] = field(default_factory=list)
    blockedBy: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "activeForm": self.activeForm,
            "owner": self.owner,
            "metadata": self.metadata,
            "blocks": list(self.blocks),
            "blockedBy": list(self.blockedBy),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            subject=data.get("subject", data.get("content", "")),
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            activeForm=data.get("activeForm", ""),
            owner=data.get("owner", ""),
            metadata=data.get("metadata", {}),
            blocks=data.get("blocks", []),
            blockedBy=data.get("blockedBy", []),
        )


@dataclass
class TaskStore:
    """
    Flat task store with individual CRUD operations.

    Matches Claude Code's TaskCreate/TaskUpdate/TaskGet/TaskList interface.
    """
    tasks: dict[str, Task] = field(default_factory=dict)
    _counter: int = field(default=0, repr=False)

    def create(
        self,
        subject: str,
        description: str = "",
        activeForm: str = "",
        **kwargs,
    ) -> Task:
        """Create a new task. Returns the created task."""
        self._counter += 1
        task_id = str(self._counter)
        task = Task(
            id=task_id,
            subject=subject,
            description=description,
            status="pending",
            activeForm=activeForm,
            owner=kwargs.get("owner", ""),
            metadata=kwargs.get("metadata", {}),
        )
        self.tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def update(self, task_id: str, **kwargs) -> Optional[Task]:
        """Update a task by ID. Returns updated task or None."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Simple field updates
        for field_name in ("status", "subject", "description", "activeForm", "owner"):
            if field_name in kwargs:
                setattr(task, field_name, kwargs[field_name])

        # Metadata merge (set key to None to delete it)
        if "metadata" in kwargs and isinstance(kwargs["metadata"], dict):
            for k, v in kwargs["metadata"].items():
                if v is None:
                    task.metadata.pop(k, None)
                else:
                    task.metadata[k] = v

        # Dependency: addBlocks
        if "addBlocks" in kwargs:
            for tid in kwargs["addBlocks"]:
                if tid not in task.blocks:
                    task.blocks.append(tid)
                other = self.tasks.get(tid)
                if other and task_id not in other.blockedBy:
                    other.blockedBy.append(task_id)

        # Dependency: addBlockedBy
        if "addBlockedBy" in kwargs:
            for tid in kwargs["addBlockedBy"]:
                if tid not in task.blockedBy:
                    task.blockedBy.append(tid)
                other = self.tasks.get(tid)
                if other and task_id not in other.blocks:
                    other.blocks.append(task_id)

        # When a task completes, remove it from others' blockedBy
        if kwargs.get("status") == "completed":
            for other_task in self.tasks.values():
                if task_id in other_task.blockedBy:
                    other_task.blockedBy.remove(task_id)

        return task

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return list(self.tasks.values())

    def get_summary(self) -> str:
        """Get a text summary for prompt injection."""
        if not self.tasks:
            return "No tasks."

        lines = ["Current Tasks:"]
        for task in self.tasks.values():
            status_icon = {
                "pending": "[ ]",
                "in_progress": "[~]",
                "completed": "[x]",
            }.get(task.status, "[?]")

            parts = [f"  {status_icon} #{task.id} {task.subject}"]

            # Show activeForm when in_progress
            if task.status == "in_progress" and task.activeForm:
                parts = [f"  {status_icon} #{task.id} {task.activeForm}..."]

            # Show open blockers
            open_blockers = [
                bid for bid in task.blockedBy
                if self.tasks.get(bid) and self.tasks[bid].status != "completed"
            ]
            if open_blockers:
                parts.append(f" (blocked by: {', '.join('#' + b for b in open_blockers)})")

            if task.owner:
                parts.append(f" [{task.owner}]")

            lines.append("".join(parts))

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize for state storage."""
        return {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "_counter": self._counter,
        }

    @classmethod
    def from_dict(cls, data) -> "TaskStore":
        """Deserialize from state. Handles both new and legacy formats."""
        store = cls()
        if isinstance(data, dict) and "tasks" in data:
            # New format: {"tasks": {...}, "_counter": N}
            store._counter = data.get("_counter", 0)
            for tid, tdata in data.get("tasks", {}).items():
                store.tasks[tid] = Task.from_dict(tdata)
        elif isinstance(data, list):
            # Legacy format: list of todo dicts
            for i, tdata in enumerate(data):
                task = Task.from_dict(tdata)
                store.tasks[task.id] = task
                store._counter = max(store._counter, i + 1)
        return store


# Backwards compatibility
Todo = Task
TodoList = TaskStore
