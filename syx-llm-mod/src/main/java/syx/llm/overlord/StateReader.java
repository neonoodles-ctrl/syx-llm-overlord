package syx.llm.overlord;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.*;

/**
 * Reads game state from Songs of Syx internal singletons via reflection.
 *
 * Key entry points:
 * - game.GAME        -> game instance
 * - settlement.main.SETT -> settlement data
 * - settlement.stats.STATS -> population, happiness stats
 * - game.faction.FACTIONS -> factions and diplomacy
 */
public class StateReader {

    private static final Gson GSON = new GsonBuilder().create();

    public GameState readState() {
        GameState state = new GameState();
        state.timestamp = System.currentTimeMillis();

        try {
            readPopulation(state);
        } catch (Exception e) {
            state.errors.add("population: " + e.getMessage());
        }

        try {
            readResources(state);
        } catch (Exception e) {
            state.errors.add("resources: " + e.getMessage());
        }

        try {
            readHappiness(state);
        } catch (Exception e) {
            state.errors.add("happiness: " + e.getMessage());
        }

        try {
            readRooms(state);
        } catch (Exception e) {
            state.errors.add("rooms: " + e.getMessage());
        }

        try {
            readMilitary(state);
        } catch (Exception e) {
            state.errors.add("military: " + e.getMessage());
        }

        try {
            readDiplomacy(state);
        } catch (Exception e) {
            state.errors.add("diplomacy: " + e.getMessage());
        }

        try {
            readTime(state);
        } catch (Exception e) {
            state.errors.add("time: " + e.getMessage());
        }

        return state;
    }

    private void readPopulation(GameState state) throws Exception {
        // Access SETT.ROOMS().population or STATS for population data
        Object sett = getStaticField("settlement.main.SETT", "INSTANCE");
        if (sett == null) sett = getStaticSingleton("settlement.main.SETT");
        if (sett == null) return;

        // Try to get population stats
        Object stats = getStaticField("settlement.stats.STATS", "INSTANCE");
        if (stats == null) stats = getStaticSingleton("settlement.stats.STATS");

        if (stats != null) {
            // Population count via reflection
            Object pop = invokeMethod(stats, "pop");
            if (pop != null) {
                state.population = new HashMap<>();
                state.population.put("total", getIntFromObject(pop, "size"));
            }
        }
    }

    private void readResources(GameState state) throws Exception {
        Object sett = getStaticSingleton("settlement.main.SETT");
        if (sett == null) return;

        // Try STOCKPILE access
        Object stockpile = invokeMethod(sett, "STOCKPILE");
        if (stockpile == null) stockpile = invokeMethod(sett, "stockpile");
        if (stockpile != null) {
            state.resources = new HashMap<>();
            // Read available resources - exact method depends on game version
            Object all = invokeMethod(stockpile, "all");
            if (all instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> resMap = (Map<String, Object>) all;
                for (Map.Entry<String, Object> entry : resMap.entrySet()) {
                    state.resources.put(entry.getKey(), getIntValue(entry.getValue()));
                }
            }
        }
    }

    private void readHappiness(GameState state) throws Exception {
        Object stats = getStaticSingleton("settlement.stats.STATS");
        if (stats == null) return;

        state.happiness = new HashMap<>();
        // Try standings/happiness access
        Object standings = invokeMethod(stats, "STANDINGS");
        if (standings == null) standings = invokeMethod(stats, "standings");
        if (standings != null) {
            // Read overall happiness
            Object overall = invokeMethod(standings, "overall");
            if (overall != null) {
                state.happiness.put("overall", getDoubleValue(overall));
            }
        }
    }

    private void readRooms(GameState state) throws Exception {
        Object sett = getStaticSingleton("settlement.main.SETT");
        if (sett == null) return;

        Object rooms = invokeMethod(sett, "ROOMS");
        if (rooms == null) rooms = invokeMethod(sett, "rooms");
        if (rooms != null) {
            state.roomCounts = new HashMap<>();
            // Try to enumerate room types and counts
            Object all = invokeMethod(rooms, "all");
            if (all instanceof Collection) {
                state.roomCounts.put("total", ((Collection<?>) all).size());
            }
        }
    }

    private void readMilitary(GameState state) throws Exception {
        Object sett = getStaticSingleton("settlement.main.SETT");
        if (sett == null) return;

        state.military = new HashMap<>();
        // Military info via army/recruit systems
        Object army = invokeMethod(sett, "ARMY");
        if (army == null) army = invokeMethod(sett, "army");
        if (army != null) {
            Object divisions = invokeMethod(army, "divisions");
            if (divisions instanceof Collection) {
                state.military.put("divisions", ((Collection<?>) divisions).size());
            }
        }
    }

    private void readDiplomacy(GameState state) throws Exception {
        Object factions = getStaticSingleton("game.faction.FACTIONS");
        if (factions == null) return;

        state.diplomacy = new HashMap<>();
        Object player = invokeMethod(factions, "player");
        if (player != null) {
            state.diplomacy.put("player_faction", String.valueOf(player));
        }
    }

    private void readTime(GameState state) throws Exception {
        Object game = getStaticSingleton("game.GAME");
        if (game == null) return;

        state.gameTime = new HashMap<>();
        // Try to read game time/day
        Object time = invokeMethod(game, "time");
        if (time != null) {
            Object day = invokeMethod(time, "day");
            Object year = invokeMethod(time, "year");
            if (day != null) state.gameTime.put("day", getIntValue(day));
            if (year != null) state.gameTime.put("year", getIntValue(year));
        }
    }

    // --- Reflection helpers ---

    private Object getStaticSingleton(String className) {
        try {
            Class<?> clazz = Class.forName(className);
            // Try INSTANCE field
            try {
                Field f = clazz.getDeclaredField("INSTANCE");
                f.setAccessible(true);
                return f.get(null);
            } catch (NoSuchFieldException ignored) {}
            // Try i() method
            try {
                Method m = clazz.getDeclaredMethod("i");
                m.setAccessible(true);
                return m.invoke(null);
            } catch (NoSuchMethodException ignored) {}
            // Try getInstance()
            try {
                Method m = clazz.getDeclaredMethod("getInstance");
                m.setAccessible(true);
                return m.invoke(null);
            } catch (NoSuchMethodException ignored) {}
        } catch (Exception e) {
            System.err.println("[LLM Overlord] Could not access " + className + ": " + e.getMessage());
        }
        return null;
    }

    private Object getStaticField(String className, String fieldName) {
        try {
            Class<?> clazz = Class.forName(className);
            Field f = clazz.getDeclaredField(fieldName);
            f.setAccessible(true);
            return f.get(null);
        } catch (Exception e) {
            return null;
        }
    }

    private Object invokeMethod(Object obj, String methodName) {
        if (obj == null) return null;
        try {
            Method m = obj.getClass().getDeclaredMethod(methodName);
            m.setAccessible(true);
            return m.invoke(obj);
        } catch (Exception e) {
            return null;
        }
    }

    private int getIntFromObject(Object obj, String field) {
        try {
            Field f = obj.getClass().getDeclaredField(field);
            f.setAccessible(true);
            return f.getInt(obj);
        } catch (Exception e) {
            return getIntValue(obj);
        }
    }

    private int getIntValue(Object obj) {
        if (obj instanceof Number) return ((Number) obj).intValue();
        return 0;
    }

    private double getDoubleValue(Object obj) {
        if (obj instanceof Number) return ((Number) obj).doubleValue();
        return 0.0;
    }
}
