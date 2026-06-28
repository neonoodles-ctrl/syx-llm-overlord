package syx.llm.overlord;

import game.GAME;
import game.faction.FACTIONS;
import game.faction.player.Player;
import game.faction.FResources;
import init.resources.RESOURCE;
import init.resources.RESOURCES;
import init.race.RACES;
import init.race.Race;
import settlement.main.SETT;
import settlement.stats.STATS;
import settlement.stats.standing.STANDINGS;
import settlement.stats.standing.StandingCitizen;
import settlement.stats.colls.StatsPopulation;
import settlement.room.main.ROOMS;
import settlement.army.ArmyManager;
import settlement.army.div.Div;

import java.util.*;

/**
 * Reads real game state from Songs of Syx internal singletons.
 *
 * Access patterns (verified from SongsOfSyx.jar):
 * - GAME.s() -> SETT
 * - GAME.factions() -> FACTIONS
 * - GAME.player() -> Player
 * - STATS.POP() -> StatsPopulation
 * - STANDINGS.CITIZEN() -> StandingCitizen
 * - SETT.ROOMS() -> ROOMS
 * - RESOURCES.ALL() -> LIST<RESOURCE>
 */
public class StateReader {

    public GameState readState() {
        GameState state = new GameState();
        state.timestamp = System.currentTimeMillis();

        readPopulation(state);
        readHappiness(state);
        readResources(state);
        readMilitary(state);
        readRooms(state);
        readFactions(state);
        readRaces(state);

        return state;
    }

    private void readPopulation(GameState state) {
        try {
            StatsPopulation pop = STATS.POP();
            if (pop == null) return;

            Map<String, Object> popMap = new LinkedHashMap<>();
            // POP.data() returns history by race, get(null) = total
            popMap.put("total", pop.POP.data().get(null));

            state.population = popMap;
        } catch (Exception e) {
            state.errors.add("population: " + e.getMessage());
        }
    }

    private void readHappiness(GameState state) {
        try {
            StandingCitizen citizen = STANDINGS.CITIZEN();
            if (citizen == null) return;

            Race playerRace = GAME.player() != null ? GAME.player().race() : null;

            Map<String, Object> happyMap = new LinkedHashMap<>();
            happyMap.put("happiness", round(citizen.happiness.getD(playerRace)));
            happyMap.put("loyalty", round(citizen.loyalty.getD(playerRace)));
            happyMap.put("fulfillment", round(citizen.fullfillment.getD(playerRace)));
            happyMap.put("expectation", round(citizen.expectation.getD(playerRace)));
            happyMap.put("current", round(citizen.current()));
            happyMap.put("target", round(citizen.target()));

            state.happiness = happyMap;
        } catch (Exception e) {
            state.errors.add("happiness: " + e.getMessage());
        }
    }

    private void readResources(GameState state) {
        try {
            Player player = GAME.player();
            if (player == null) return;

            FResources res = player.res();
            if (res == null) return;

            Map<String, Object> resMap = new LinkedHashMap<>();
            for (RESOURCE r : RESOURCES.ALL()) {
                int available = res.getAvailable(r);
                if (available > 0) {
                    resMap.put(r.key, available);
                }
            }

            // Treasury/credits
            try {
                resMap.put("credits", (int) player.credits().credits());
            } catch (Exception ignored) {}

            state.resources = resMap;
        } catch (Exception e) {
            state.errors.add("resources: " + e.getMessage());
        }
    }

    private void readMilitary(GameState state) {
        try {
            ArmyManager army = SETT.ARMIES();
            if (army == null) return;

            Map<String, Object> milMap = new LinkedHashMap<>();
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
            if (rooms == null) return;

            Map<String, Object> roomMap = new LinkedHashMap<>();
            roomMap.put("stockpile_crates", rooms.STOCKPILE.crates());

            state.roomCounts = roomMap;
        } catch (Exception e) {
            state.errors.add("rooms: " + e.getMessage());
        }
    }

    private void readFactions(GameState state) {
        try {
            Map<String, Object> dipMap = new LinkedHashMap<>();

            Player player = GAME.player();
            if (player != null) {
                dipMap.put("ruler", player.rulerName().toString());
                dipMap.put("race", player.race().key);
                dipMap.put("level", player.level());
            }

            dipMap.put("active_factions", FACTIONS.active().size());

            state.diplomacy = dipMap;
        } catch (Exception e) {
            state.errors.add("diplomacy: " + e.getMessage());
        }
    }

    private void readRaces(GameState state) {
        try {
            List<String> races = new ArrayList<>();
            snake2d.util.sets.LIST<Race> playable = RACES.playable();
            for (int i = 0; i < playable.size(); i++) {
                races.add(playable.get(i).key);
            }
            state.availableRaces = races;
        } catch (Exception e) {
            state.errors.add("races: " + e.getMessage());
        }
    }

    // --- Helpers ---

    private double round(Object val) {
        if (val instanceof Number) {
            return Math.round(((Number) val).doubleValue() * 1000.0) / 1000.0;
        }
        return 0.0;
    }
}
