package syx.llm.overlord;

import settlement.main.SETT;
import settlement.room.main.ROOMS;
import settlement.room.main.RoomBlueprintImp;
import snake2d.util.sets.LIST;

import java.util.Locale;

final class RoomResolver {

    private RoomResolver() {
    }

    static RoomBlueprintImp resolve(String target) {
        if (target == null || target.isBlank()) {
            return null;
        }
        ROOMS rooms = SETT.ROOMS();
        if (rooms == null) {
            return null;
        }

        String normalized = target.trim().toLowerCase(Locale.ROOT)
            .replace(' ', '_')
            .replace('-', '_');

        RoomBlueprintImp direct = switch (normalized) {
            case "stockpile", "stockpile_crates", "crates", "granary" -> rooms.STOCKPILE;
            case "home", "housing", "house", "settler_tent", "tent", "shelter" -> rooms.HOME;
            case "well" -> first(rooms.WELLS);
            case "farm" -> first(rooms.FARMS);
            case "fishery", "fish" -> first(rooms.FISHERIES);
            case "hunter" -> first(rooms.HUNTERS);
            case "pasture" -> first(rooms.PASTURES);
            case "orchard" -> first(rooms.ORCHARDS);
            case "woodcutter", "wood_cutter" -> rooms.WOOD_CUTTER;
            case "mine" -> first(rooms.MINES);
            case "workshop" -> first(rooms.WORKSHOPS);
            case "builder" -> rooms.BUILDER;
            case "bench" -> rooms.BENCH;
            case "tavern" -> first(rooms.TAVERNS);
            case "market" -> first(rooms.MARKET);
            case "barracks" -> first(rooms.BARRACKS);
            case "inn" -> rooms.INN;
            case "export" -> rooms.EXPORT;
            case "import" -> rooms.IMPORT;
            case "hauler" -> rooms.HAULER;
            case "transport" -> rooms.TRANSPORT;
            case "station" -> rooms.STATION;
            case "janitor" -> rooms.JANITOR;
            case "hospital" -> rooms.HOSPITAL;
            case "guard" -> rooms.GUARD;
            case "prison" -> rooms.PRISON;
            case "court" -> rooms.COURT;
            case "hearth" -> rooms.HEARTH;
            case "cannibal" -> rooms.CANNIBAL;
            default -> null;
        };
        if (direct != null) {
            return direct;
        }

        String key = normalized.startsWith("_") ? normalized : "_" + normalized.toUpperCase(Locale.ROOT);
        for (RoomBlueprintImp blueprint : rooms.imps()) {
            if (blueprint.key.equalsIgnoreCase(key) || blueprint.key.equalsIgnoreCase(normalized)) {
                return blueprint;
            }
        }

        String needle = normalized.toUpperCase(Locale.ROOT);
        for (RoomBlueprintImp blueprint : rooms.imps()) {
            if (blueprint.key.toUpperCase(Locale.ROOT).contains(needle)) {
                return blueprint;
            }
        }
        return null;
    }

    private static RoomBlueprintImp first(LIST<?> list) {
        if (list == null || list.size() == 0) {
            return null;
        }
        Object value = list.get(0);
        return value instanceof RoomBlueprintImp blueprint ? blueprint : null;
    }
}
