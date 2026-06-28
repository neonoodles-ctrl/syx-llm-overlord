package syx.llm.overlord;

import java.util.*;

/**
 * Snapshot of game state, serialized to JSON for the LLM bridge.
 */
public class GameState {
    public long timestamp;
    public Map<String, Object> population;
    public Map<String, Object> resources;
    public Map<String, Object> happiness;
    public Map<String, Object> roomCounts;
    public Map<String, Object> military;
    public Map<String, Object> diplomacy;
    public Map<String, Object> gameTime;
    public List<String> errors = new ArrayList<>();
}
