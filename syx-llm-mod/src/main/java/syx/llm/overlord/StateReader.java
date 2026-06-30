package syx.llm.overlord;

import game.GAME;
import game.GameSpeed;
import game.faction.FACTIONS;
import game.faction.FResources;
import game.faction.player.Player;
import game.time.TIME;
import init.resources.RESOURCE;
import init.resources.RESOURCES;
import init.race.Race;
import settlement.army.ArmyManager;
import settlement.army.div.Div;
import settlement.main.SETT;
import settlement.room.main.ROOMS;
import settlement.room.main.throne.THRONE;
import settlement.stats.STATS;
import settlement.stats.colls.StatsPopulation;
import settlement.stats.standing.STANDINGS;
import settlement.stats.standing.StandingCitizen;
import util.data.INT;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Reads game state using only primitive extractions safe for JSON export.
 */
public class StateReader {

    public GameState readState() {
        GameState state = new GameState();
        state.timestamp = System.currentTimeMillis();

        readGameTime(state);
        readGameSpeed(state);
        readThrone(state);
        readMapGrid(state);
        readPopulation(state);
        readHappiness(state);
        readResources(state);
        readMilitary(state);
        readRooms(state);
        readFactions(state);

        return state;
    }

    private void readGameTime(GameState state) {
        try {
            Map<String, Integer> time = new LinkedHashMap<>();
            time.put("day", TIME.days().bitCurrent());
            time.put("year", TIME.years().bitCurrent());
            time.put("hour", TIME.hours().bitCurrent());
            state.gameTime = time;
        } catch (Exception e) {
            state.errors.add("gameTime: " + e.getMessage());
        }
    }

    private void readGameSpeed(GameState state) {
        try {
            GameSpeed speed = GAME.SPEED;
            Map<String, Double> speedMap = new LinkedHashMap<>();
            speedMap.put("target", speed.speedTarget());
            speedMap.put("actual", speed.speed());
            speedMap.put("paused", speed.isPaused() ? 1.0 : 0.0);
            state.gameSpeed = speedMap;
        } catch (Exception e) {
            state.errors.add("gameSpeed: " + e.getMessage());
        }
    }

    private void readThrone(GameState state) {
        try {
            Map<String, Integer> throne = new LinkedHashMap<>();
            throne.put("x", THRONE.coo().x());
            throne.put("y", THRONE.coo().y());
            state.throne = throne;
        } catch (Exception e) {
            state.errors.add("throne: " + e.getMessage());
        }
    }

    private void readMapGrid(GameState state) {
        try {
            MapExporter.exportTo(state);
        } catch (Exception e) {
            state.errors.add("mapGrid: " + e.getMessage());
        }
    }

    private void readPopulation(GameState state) {
        try {
            StatsPopulation pop = STATS.POP();
            if (pop == null) {
                return;
            }
            Map<String, Integer> popMap = new LinkedHashMap<>();
            popMap.put("total", intValue(pop.POP.data().get(null)));
            state.population = popMap;
        } catch (Exception e) {
            state.errors.add("population: " + e.getMessage());
        }
    }

    private void readHappiness(GameState state) {
        try {
            StandingCitizen citizen = STANDINGS.CITIZEN();
            if (citizen == null) {
                return;
            }

            Race playerRace = GAME.player() != null ? GAME.player().race() : null;
            Map<String, Double> happyMap = new LinkedHashMap<>();
            happyMap.put("happiness", round(citizen.happiness.getD(playerRace)));
            happyMap.put("loyalty", round(citizen.loyalty.getD(playerRace)));
            happyMap.put("fulfillment", round(citizen.fullfillment.getD(playerRace)));
            happyMap.put("expectation", round(citizen.expectation.getD(playerRace)));
            happyMap.put("current", round(citizen.current()));
            happyMap.put("target", round(citizen.target()));
            happyMap.put("overall", round(citizen.current()));
            state.happiness = happyMap;
        } catch (Exception e) {
            state.errors.add("happiness: " + e.getMessage());
        }
    }

    private void readResources(GameState state) {
        try {
            Player player = GAME.player();
            if (player == null) {
                return;
            }

            FResources res = player.res();
            if (res == null) {
                return;
            }

            Map<String, Integer> resMap = new LinkedHashMap<>();
            int listed = 0;
            for (RESOURCE r : RESOURCES.ALL()) {
                int available = res.getAvailable(r);
                if (available > 0) {
                    resMap.put(r.key, available);
                    listed++;
                    if (listed >= 32) {
                        break;
                    }
                }
            }

            try {
                resMap.put("credits", (int) player.credits().credits());
            } catch (Exception ignored) {
            }

            state.resources = resMap;
        } catch (Exception e) {
            state.errors.add("resources: " + e.getMessage());
        }
    }

    private void readMilitary(GameState state) {
        try {
            ArmyManager army = SETT.ARMIES();
            if (army == null) {
                return;
            }

            Map<String, Integer> milMap = new LinkedHashMap<>();
            snake2d.util.sets.LIST<Div> divisions = army.divisions();
            milMap.put("divisions", divisions.size());

            int totalMen = 0;
            for (int i = 0; i < divisions.size(); i++) {
                totalMen += divisions.get(i).menNrOf();
            }
            milMap.put("total_soldiers", totalMen);
            state.military = milMap;
        } catch (Exception e) {
            state.errors.add("military: " + e.getMessage());
        }
    }

    private void readRooms(GameState state) {
        try {
            ROOMS rooms = SETT.ROOMS();
            if (rooms == null) {
                return;
            }

            Map<String, Integer> roomMap = new LinkedHashMap<>();
            roomMap.put("stockpile_crates", rooms.STOCKPILE.crates());
            state.roomCounts = roomMap;
        } catch (Exception e) {
            state.errors.add("rooms: " + e.getMessage());
        }
    }

    private void readFactions(GameState state) {
        try {
            Map<String, String> dipMap = new LinkedHashMap<>();
            Player player = GAME.player();
            if (player != null) {
                dipMap.put("ruler", player.rulerName().toString());
                dipMap.put("race", player.race().key);
                dipMap.put("level", String.valueOf(player.level()));
            }
            dipMap.put("active_factions", String.valueOf(FACTIONS.active().size()));
            state.diplomacy = dipMap;
        } catch (Exception e) {
            state.errors.add("diplomacy: " + e.getMessage());
        }
    }

    private static int intValue(Object value) {
        if (value instanceof INT) {
            return ((INT) value).get();
        }
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return 0;
    }

    private static double round(Object val) {
        if (val instanceof Number) {
            return Math.round(((Number) val).doubleValue() * 1000.0) / 1000.0;
        }
        return 0.0;
    }
}
