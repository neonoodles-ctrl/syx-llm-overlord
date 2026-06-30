package syx.llm.overlord;

import init.type.TERRAIN;
import settlement.main.SETT;
import settlement.room.main.RoomBlueprintImp;
import settlement.room.main.RoomInstance;
import settlement.room.main.throne.THRONE;
import settlement.tilemap.ground.GroundType;
import settlement.tilemap.terrain.Terrain;

/**
 * Exports a compact ASCII tile grid around the throne for LLM map awareness.
 */
final class MapExporter {

    static final int DEFAULT_RADIUS = 20;
    static final int MAX_RADIUS = 35;

    private MapExporter() {
    }

    static void exportTo(GameState state) {
        exportTo(state, DEFAULT_RADIUS);
    }

    static void exportTo(GameState state, int radius) {
        int cx = THRONE.coo().x();
        int cy = THRONE.coo().y();
        radius = Math.max(5, Math.min(radius, MAX_RADIUS));

        state.mapCenterX = cx;
        state.mapCenterY = cy;
        state.mapRadius = radius;
        state.mapLegend =
            "T=throne +=room(building) .=open ~ =water ^=forest/tree M=mountain/cave X=blocked ?=unknown. "
            + "Rows north→south; columns west→east.";

        for (int y = cy - radius; y <= cy + radius; y++) {
            StringBuilder row = new StringBuilder(radius * 2 + 1);
            for (int x = cx - radius; x <= cx + radius; x++) {
                row.append(classify(x, y, cx, cy));
            }
            state.mapRows.add(row.toString());
        }
    }

    private static char classify(int x, int y, int throneX, int throneY) {
        if (x == throneX && y == throneY) {
            return 'T';
        }
        if (!SETT.IN_BOUNDS(x, y)) {
            return '?';
        }

        try {
            RoomInstance instance = SETT.ROOMS().map.instance.get(x, y);
            if (instance != null) {
                RoomBlueprintImp blueprint = SETT.ROOMS().map.blueprintImp.get(x, y);
                if (blueprint != null && blueprint.key != null && !blueprint.key.isEmpty()) {
                    char c = Character.toUpperCase(blueprint.key.charAt(0));
                    if (Character.isLetterOrDigit(c)) {
                        return c;
                    }
                }
                return '+';
            }

            if (SETT.PLACA().willBlock.is(x, y) || SETT.PLACA().solidityWill.is(x, y)) {
                return 'X';
            }

            Terrain.TerrainTile tile = SETT.TERRAIN().get(x, y);
            if (tile != null) {
                TERRAIN terrain = tile.terrain(x, y);
                if (terrain != null) {
                    String key = terrain.key();
                    if (key != null) {
                        String k = key.toUpperCase();
                        if (k.contains("WATER") || k.contains("LAKE") || k.contains("RIVER")) {
                            return '~';
                        }
                        if (k.contains("MOUNT") || k.contains("CAVE") || k.contains("ROCK")) {
                            return 'M';
                        }
                    }
                }
            }

            GroundType ground = SETT.GROUND().MAP.get(x, y);
            if (ground != null) {
                if (ground.vegitation > 0.25) {
                    return '^';
                }
            }

            return '.';
        } catch (Exception e) {
            return '?';
        }
    }
}
