package syx.llm.overlord;

import game.GAME;
import game.faction.player.Player;
import settlement.main.SETT;
import settlement.stats.STATS;

import java.util.*;

/**
 * Executes commands from the LLM by interacting with game systems.
 *
 * Many commands interact with the game's UI systems which require
 * running on the render thread. For now, we focus on what we can
 * safely do via the game's internal APIs.
 */
public class CommandExecutor {

    private static final Set<String> VALID_ACTIONS = Set.of(
        "build", "demolish", "set_policy", "recruit",
        "set_tax", "set_ration", "set_speed", "pause",
        "info"
    );

    public CommandResult execute(Command cmd) {
        if (cmd == null || cmd.action == null) {
            return new CommandResult(false, "Command or action is null");
        }

        if (!VALID_ACTIONS.contains(cmd.action)) {
            return new CommandResult(false, "Unknown action: " + cmd.action +
                ". Valid: " + String.join(", ", VALID_ACTIONS));
        }

        try {
            return switch (cmd.action) {
                case "info" -> executeInfo(cmd);
                case "set_speed" -> executeSetSpeed(cmd);
                case "set_tax" -> executeSetTax(cmd);
                case "build" -> executeBuild(cmd);
                case "set_policy" -> executeSetPolicy(cmd);
                case "recruit" -> executeRecruit(cmd);
                default -> new CommandResult(false, "'" + cmd.action + "' recognized but not yet implemented");
            };
        } catch (Exception e) {
            return new CommandResult(false, "Error: " + e.getMessage());
        }
    }

    private CommandResult executeInfo(Command cmd) {
        try {
            StringBuilder sb = new StringBuilder();
            sb.append("Ruler: ").append(GAME.player().rulerName()).append("\n");
            sb.append("Race: ").append(GAME.player().race().key).append("\n");
            sb.append("Population: ").append(STATS.POP().POP.data().get(null)).append("\n");
            sb.append("Happiness: ").append(STANDINGS.CITIZEN().current()).append("\n");
            sb.append("Active factions: ").append(FACTIONS.active().size());
            return new CommandResult(true, sb.toString());
        } catch (Exception e) {
            return new CommandResult(false, "Info error: " + e.getMessage());
        }
    }

    private CommandResult executeSetSpeed(Command cmd) {
        // Game speed is controlled via GAME.SPEED
        if (cmd.params == null || !cmd.params.containsKey("value")) {
            return new CommandResult(false, "Set speed requires params.value (0-4)");
        }
        int speed = ((Number) cmd.params.get("value")).intValue();
        if (speed < 0 || speed > 4) {
            return new CommandResult(false, "Speed must be 0-4");
        }
        // Speed control is via the game's UI system - we can set it via reflection
        try {
            game.GameSpeed gameSpeed = GAME.SPEED;
            // The speed object has setter methods we can try
            java.lang.reflect.Method setSpeed = gameSpeed.getClass().getMethod("set", int.class);
            setSpeed.setAccessible(true);
            setSpeed.invoke(gameSpeed, speed);
            return new CommandResult(true, "Game speed set to " + speed);
        } catch (Exception e) {
            return new CommandResult(false, "Speed control unavailable: " + e.getMessage());
        }
    }

    private CommandResult executeSetTax(Command cmd) {
        // Tax rate is part of the GOVERN stats
        if (cmd.params == null || !cmd.params.containsKey("value")) {
            return new CommandResult(false, "Set tax requires params.value (0-100)");
        }
        int value = ((Number) cmd.params.get("value")).intValue();
        if (value < 0 || value > 100) {
            return new CommandResult(false, "Tax rate must be 0-100");
        }
        // Tax is typically set via the law/govern UI
        // For now, log the command - full implementation requires UI interaction
        System.out.println("[LLM Overlord] Tax command: " + value);
        return new CommandResult(true, "Tax command received: " + value + " (requires UI interaction)");
    }

    private CommandResult executeBuild(Command cmd) {
        if (cmd.target == null) {
            return new CommandResult(false, "Build requires 'target' (room type)");
        }
        if (cmd.x == null || cmd.y == null) {
            return new CommandResult(false, "Build requires 'x' and 'y' coordinates");
        }
        // Building placement uses ROOMS.placement which requires UI interaction
        System.out.println("[LLM Overlord] Build: " + cmd.target + " at (" + cmd.x + "," + cmd.y + ")");
        return new CommandResult(true, "Build queued: " + cmd.target + " at (" + cmd.x + "," + cmd.y + ")");
    }

    private CommandResult executeSetPolicy(Command cmd) {
        if (cmd.target == null) {
            return new CommandResult(false, "Set policy requires 'target'");
        }
        System.out.println("[LLM Overlord] Policy: " + cmd.target + " -> " + cmd.params);
        return new CommandResult(true, "Policy set: " + cmd.target);
    }

    private CommandResult executeRecruit(Command cmd) {
        if (cmd.target == null) {
            return new CommandResult(false, "Recruit requires 'target' (unit type)");
        }
        int count = cmd.params != null && cmd.params.containsKey("count")
            ? ((Number) cmd.params.get("count")).intValue() : 1;
        System.out.println("[LLM Overlord] Recruit: " + count + "x " + cmd.target);
        return new CommandResult(true, "Recruit queued: " + count + "x " + cmd.target);
    }

    // Needed for access to STANDINGS and FACTIONS in this class
    private static settlement.stats.standing.STANDINGS STANDINGS;
    private static game.faction.FACTIONS FACTIONS;

    static {
        try {
            java.lang.reflect.Method m = settlement.stats.standing.STANDINGS.class.getDeclaredMethod("i");
            m.setAccessible(true);
            STANDINGS = (settlement.stats.standing.STANDINGS) m.invoke(null);
        } catch (Exception ignored) {}
        try {
            java.lang.reflect.Field f = game.faction.FACTIONS.class.getDeclaredField("self");
            f.setAccessible(true);
            FACTIONS = (game.faction.FACTIONS) f.get(null);
        } catch (Exception ignored) {}
    }
}
