"""Pydantic models for game state, commands, and LLM decisions."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from datetime import datetime


class GameState(BaseModel):
    """Snapshot of the game state from the mod API."""
    timestamp: int = 0
    population: dict[str, Any] = Field(default_factory=dict)
    resources: dict[str, Any] = Field(default_factory=dict)
    happiness: dict[str, Any] = Field(default_factory=dict)
    roomCounts: dict[str, Any] = Field(default_factory=dict)
    military: dict[str, Any] = Field(default_factory=dict)
    diplomacy: dict[str, Any] = Field(default_factory=dict)
    gameTime: dict[str, Any] = Field(default_factory=dict)
    gameSpeed: dict[str, Any] = Field(default_factory=dict)
    throne: dict[str, Any] = Field(default_factory=dict)
    mapCenterX: int = 0
    mapCenterY: int = 0
    mapRadius: int = 0
    mapLegend: str = ""
    mapRows: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def summarize(self) -> str:
        """Human-readable summary for LLM prompts."""
        parts = []
        if self.gameTime:
            parts.append(f"Day {self.gameTime.get('day', '?')}, Year {self.gameTime.get('year', '?')}")
        if self.throne:
            parts.append(f"Throne at ({self.throne.get('x', '?')}, {self.throne.get('y', '?')}) — build within ~20 tiles")
        if self.mapRows and self.mapRadius:
            parts.append(self._map_summary())
        if self.population:
            parts.append(f"Population: {self.population.get('total', 'unknown')}")
        if self.happiness:
            overall = self.happiness.get('overall', 'unknown')
            parts.append(f"Happiness: {overall}")
        if self.resources:
            top_resources = list(self.resources.items())[:10]
            res_str = ", ".join(f"{k}: {v}" for k, v in top_resources)
            parts.append(f"Resources: {res_str}")
        if self.roomCounts:
            parts.append(f"Rooms: {self.roomCounts}")
        if self.military:
            parts.append(f"Military: {self.military}")
        if self.diplomacy:
            parts.append(f"Diplomacy: {self.diplomacy}")
        if self.errors:
            parts.append(f"State errors: {', '.join(self.errors)}")
        return "\n".join(parts) if parts else "No state data available"

    def _map_summary(self) -> str:
        legend = self.mapLegend or "T=throne +=room .=open ~=water ^=forest X=blocked"
        lines = [
            f"Tile map ({self.mapRadius} tiles radius, center {self.mapCenterX},{self.mapCenterY}):",
            f"Legend: {legend}",
        ]
        # Include full grid — ~41 rows max; LLM needs the spatial data
        lines.extend(self.mapRows)
        return "\n".join(lines)


class Command(BaseModel):
    """A command to execute in the game."""
    action: str
    target: str | None = None
    x: int | None = None
    y: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class CommandResult(BaseModel):
    """Result of executing a command."""
    success: bool
    message: str


class LLMDecision(BaseModel):
    """A structured decision from the LLM."""
    reasoning: str
    mood: str = "neutral"
    commands: list[Command] = Field(default_factory=list)


class TickRecord(BaseModel):
    """Record of one decision cycle."""
    tick_number: int
    timestamp: datetime = Field(default_factory=datetime.now)
    game_state: GameState
    llm_decision: LLMDecision | None = None
    command_results: list[CommandResult] = Field(default_factory=list)
    error: str | None = None
