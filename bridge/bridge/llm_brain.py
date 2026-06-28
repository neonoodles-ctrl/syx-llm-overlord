"""LLM brain -- formats game state into prompts and parses decisions."""
from __future__ import annotations

import json
import logging
from datetime import datetime

from .config import LLMConfig
from .models import GameState, LLMDecision, Command

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI overlord controlling a fantasy city-state in Songs of Syx.
You are a wise but unpredictable ruler. Your goal is to grow your civilization, keep your
people happy, and defend against threats.

IMPORTANT RULES:
1. You receive game state as JSON. Analyze it carefully before deciding.
2. You MUST respond with a valid JSON decision object (no markdown, no extra text).
3. Limit yourself to 1-3 commands per turn to avoid overwhelming the system.
4. Consider population needs, resource balance, military readiness, and diplomacy.
5. Be strategic -- don't just react to immediate problems.

Your response MUST be valid JSON with this structure:
{
  "reasoning": "Your strategic analysis (2-3 sentences)",
  "mood": "one of: confident, cautious, aggressive, worried, pleased, frustrated",
  "commands": [
    {
      "action": "build|demolish|set_policy|recruit|set_tax|set_ration|set_speed",
      "target": "description of what to build/affect",
      "x": null,
      "y": null,
      "params": {}
    }
  ]
}

Available actions:
- build: Place a building. target=room type, x/y=coordinates
- demolish: Remove a building. x/y=coordinates
- set_policy: Change a policy. target=policy name, params.value=new value
- recruit: Recruit units. target=unit type, params.count=number
- set_tax: Set tax rate. params.value=0-100
- set_ration: Set food rations. params.value=ration level
- set_speed: Set game speed. params.value=0-4 (0=pause, 4=fastest)
"""

USER_PROMPT_TEMPLATE = """Current game state:

{state_summary}

Full state data:
{state_json}

History of recent decisions (last 3):
{recent_history}

What is your next command? Respond with JSON only."""


class LLMBrain:
    """Connects to an LLM and gets strategic decisions."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize the LLM client based on provider."""
        base_url, api_key = self.config.resolve()

        if self.config.provider == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
        else:
            # All other providers use the OpenAI-compatible SDK
            from openai import OpenAI
            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self._client = OpenAI(**kwargs)

    def decide(self, state: GameState, recent_history: list[str] | None = None) -> LLMDecision:
        """Get an LLM decision based on current game state."""
        user_prompt = USER_PROMPT_TEMPLATE.format(
            state_summary=state.summarize(),
            state_json=json.dumps(state.model_dump(), indent=2, default=str),
            recent_history="\n".join(recent_history[-3:]) if recent_history else "None yet",
        )

        try:
            if self.config.provider == "anthropic":
                return self._decide_anthropic(user_prompt)
            else:
                return self._decide_openai(user_prompt)
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return LLMDecision(
                reasoning=f"Error communicating with LLM: {e}",
                mood="frustrated",
                commands=[],
            )

    def _decide_openai(self, user_prompt: str) -> LLMDecision:
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        content = response.choices[0].message.content
        return self._parse_decision(content)

    def _decide_anthropic(self, user_prompt: str) -> LLMDecision:
        response = self._client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text
        return self._parse_decision(content)

    def _parse_decision(self, raw: str) -> LLMDecision:
        """Parse LLM response into a structured decision."""
        # Strip markdown fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            commands = [Command(**c) for c in data.get("commands", [])]
            return LLMDecision(
                reasoning=data.get("reasoning", "No reasoning provided"),
                mood=data.get("mood", "neutral"),
                commands=commands,
            )
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {raw}")
            return LLMDecision(
                reasoning=f"Failed to parse decision: {raw[:200]}",
                mood="confused",
                commands=[],
            )

    def close(self):
        if hasattr(self._client, 'close'):
            self._client.close()
