package syx.llm.overlord;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Snapshot of game state, serialized to JSON for the LLM bridge.
 * Values must be JSON primitives only — never store game engine objects here.
 */
public class GameState {
    public long timestamp;
    public int tickCount;
    public Map<String, Integer> population = new LinkedHashMap<>();
    public Map<String, Integer> resources = new LinkedHashMap<>();
    public Map<String, Double> happiness = new LinkedHashMap<>();
    public Map<String, Integer> roomCounts = new LinkedHashMap<>();
    public Map<String, Integer> military = new LinkedHashMap<>();
    public Map<String, String> diplomacy = new LinkedHashMap<>();
    public Map<String, Integer> gameTime = new LinkedHashMap<>();
    public List<String> errors = new ArrayList<>();
}
