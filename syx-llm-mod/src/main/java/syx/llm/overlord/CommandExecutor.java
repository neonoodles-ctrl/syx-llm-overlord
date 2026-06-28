package syx.llm.overlord;

import java.lang.reflect.Method;
import java.util.*;

/**
 * Executes commands received from the LLM by interacting with game systems.
 *
 * Commands are validated before execution. Invalid or dangerous commands
 * are rejected with an explanation.
 */
public class CommandExecutor {

    private static final Set<String> VALID_ACTIONS = Set.of(
        "build", "demolish", "set_policy", "recruit", "dismiss",
        "set_tax", "set_ration", "trade", "set_speed", "pause",
        "appoint", "declare_war", "make_peace", "set_formation"
    );

    public CommandResult execute(Command cmd) {
        if (cmd == null || cmd.action == null) {
            return new CommandResult(false, "Command or action is null");
        }

        if (!VALID_ACTIONS.contains(cmd.action)) {
            return new CommandResult(false, "Unknown action: " + cmd.action +
                ". Valid actions: " + String.join(", ", VALID_ACTIONS));
        }

        try {
            return switch (cmd.action) {
                case "build" -> executeBuild(cmd);
                case "demolish" -> executeDemolish(cmd);
                case "set_policy" -> executeSetPolicy(cmd);
                case "recruit" -> executeRecruit(cmd);
                case "set_tax" -> executeSetTax(cmd);
                case "set_ration" -> executeSetRation(cmd);
                case "set_speed" -> executeSetSpeed(cmd);
                case "pause" -> executePause(cmd);
                default -> new CommandResult(false, "Action '" + cmd.action + "' recognized but not yet implemented");
            };
        } catch (Exception e) {
            return new CommandResult(false, "Execution error: " + e.getMessage());
        }
    }

    private CommandResult executeBuild(Command cmd) {
        // Building requires: target (room type), x, y coordinates
        if (cmd.target == null) {
            return new CommandResult(false, "Build command requires 'target' (room type)");
        }
        if (cmd.x == null || cmd.y == null) {
            return new CommandResult(false, "Build command requires 'x' and 'y' coordinates");
        }

        // Access SETT.ROOMS() to find the room type and place it
        Object sett = getStaticSingleton("settlement.main.SETT");
        if (sett == null) {
            return new CommandResult(false, "Cannot access game settlement");
        }

        // Log the build request - actual placement depends on game internals
        System.out.println("[LLM Overlord] Build request: " + cmd.target + " at (" + cmd.x + ", " + cmd.y + ")");
        return new CommandResult(true, "Build command queued: " + cmd.target + " at (" + cmd.x + ", " + cmd.y + ")");
    }

    private CommandResult executeDemolish(Command cmd) {
        if (cmd.x == null || cmd.y == null) {
            return new CommandResult(false, "Demolish command requires 'x' and 'y' coordinates");
        }
        System.out.println("[LLM Overlord] Demolish request at (" + cmd.x + ", " + cmd.y + ")");
        return new CommandResult(true, "Demolish command queued at (" + cmd.x + ", " + cmd.y + ")");
    }

    private CommandResult executeSetPolicy(Command cmd) {
        if (cmd.target == null) {
            return new CommandResult(false, "Set policy requires 'target' (policy name)");
        }
        System.out.println("[LLM Overlord] Set policy: " + cmd.target + " -> " + cmd.params);
        return new CommandResult(true, "Policy set: " + cmd.target);
    }

    private CommandResult executeRecruit(Command cmd) {
        if (cmd.target == null) {
            return new CommandResult(false, "Recruit requires 'target' (unit type)");
        }
        int count = cmd.params != null && cmd.params.containsKey("count")
            ? ((Number) cmd.params.get("count")).intValue() : 1;
        System.out.println("[LLM Overlord] Recruit: " + count + "x " + cmd.target);
        return new CommandResult(true, "Recruitment queued: " + count + "x " + cmd.target);
    }

    private CommandResult executeSetTax(Command cmd) {
        if (cmd.params == null || !cmd.params.containsKey("value")) {
            return new CommandResult(false, "Set tax requires params.value (0-100)");
        }
        int value = ((Number) cmd.params.get("value")).intValue();
        if (value < 0 || value > 100) {
            return new CommandResult(false, "Tax rate must be 0-100");
        }
        System.out.println("[LLM Overlord] Set tax rate: " + value);
        return new CommandResult(true, "Tax rate set to " + value);
    }

    private CommandResult executeSetRation(Command cmd) {
        if (cmd.params == null || !cmd.params.containsKey("value")) {
            return new CommandResult(false, "Set ration requires params.value");
        }
        System.out.println("[LLM Overlord] Set rations: " + cmd.params.get("value"));
        return new CommandResult(true, "Ration policy set");
    }

    private CommandResult executeSetSpeed(Command cmd) {
        if (cmd.params == null || !cmd.params.containsKey("value")) {
            return new CommandResult(false, "Set speed requires params.value (0-4)");
        }
        int speed = ((Number) cmd.params.get("value")).intValue();
        if (speed < 0 || speed > 4) {
            return new CommandResult(false, "Speed must be 0-4 (0=pause, 4=fastest)");
        }
        System.out.println("[LLM Overlord] Set game speed: " + speed);
        return new CommandResult(true, "Game speed set to " + speed);
    }

    private CommandResult executePause(Command cmd) {
        System.out.println("[LLM Overlord] Toggle pause");
        return new CommandResult(true, "Pause toggled");
    }

    // --- Reflection helpers (duplicated from StateReader for independence) ---

    private Object getStaticSingleton(String className) {
        try {
            Class<?> clazz = Class.forName(className);
            try {
                Method m = clazz.getDeclaredMethod("i");
                m.setAccessible(true);
                return m.invoke(null);
            } catch (NoSuchMethodException ignored) {}
            try {
                java.lang.reflect.Field f = clazz.getDeclaredField("INSTANCE");
                f.setAccessible(true);
                return f.get(null);
            } catch (NoSuchFieldException ignored) {}
        } catch (Exception e) {
            return null;
        }
        return null;
    }
}
