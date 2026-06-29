package syx.llm.overlord;

import settlement.main.SETT;
import settlement.room.main.RoomBlueprintImp;
import settlement.room.main.furnisher.Furnisher;
import settlement.room.main.placement.RoomPlacer;
import settlement.room.main.throne.THRONE;
import snake2d.util.datatypes.AREA;
import snake2d.util.datatypes.COORDINATE;
import snake2d.util.datatypes.RECTANGLE;
import snake2d.util.datatypes.Rec;
import view.tool.PLACER_TYPE;
import view.tool.PlacableFixed;
import view.tool.PlacableMulti;

final class RoomBuilder {

    private static final int SEARCH_RADIUS = 40;
    private static final int DEFAULT_AREA = 4;

    private RoomBuilder() {
    }

    static CommandResult build(String target, int x, int y, java.util.Map<String, Object> params) {
        if (!SETT.IN_BOUNDS(x, y)) {
            return new CommandResult(false, "Coordinates out of bounds: (" + x + "," + y + ")");
        }

        // Release stale TmpArea lock left by interrupted placement (crashes game updater).
        releasePlacementState();

        RoomBlueprintImp blueprint = RoomResolver.resolve(target);
        if (blueprint == null) {
            return new CommandResult(false, "Unknown room type: " + target);
        }
        if (blueprint.constructor() == null) {
            return new CommandResult(false, "Room has no constructor: " + blueprint.key);
        }

        int itemGroup = intParam(params, "group", 0);
        int width = Math.max(1, intParam(params, "width", DEFAULT_AREA));
        int height = Math.max(1, intParam(params, "height", DEFAULT_AREA));

        CommandResult direct = tryBuild(blueprint, x, y, itemGroup, width, height);
        if (direct.success) {
            return direct;
        }

        // Item rooms (well, woodcutter): one attempt only — spiral search re-inits placer and can deadlock TmpArea.
        if (!blueprint.constructor().usesArea()) {
            return direct;
        }

        COORDINATE center = THRONE.coo();
        for (int radius = 1; radius <= SEARCH_RADIUS; radius++) {
            for (int dy = -radius; dy <= radius; dy++) {
                for (int dx = -radius; dx <= radius; dx++) {
                    if (Math.abs(dx) != radius && Math.abs(dy) != radius) {
                        continue;
                    }
                    int tx = center.x() + dx;
                    int ty = center.y() + dy;
                    if (tx == x && ty == y) {
                        continue;
                    }
                    CommandResult attempt = tryBuild(blueprint, tx, ty, itemGroup, width, height);
                    if (attempt.success) {
                        return new CommandResult(true, attempt.message + " (relocated from " + x + "," + y + ")");
                    }
                }
            }
        }

        return new CommandResult(false, direct.message + " (also searched " + SEARCH_RADIUS + " tiles around throne)");
    }

    /** Clear TmpArea + placer embryo so the game updater does not crash on "In use by: PlacerItemSingle". */
    private static void releasePlacementState() {
        PlacementCleanup.release();
    }

    private static CommandResult tryBuild(
        RoomBlueprintImp blueprint,
        int x,
        int y,
        int itemGroup,
        int width,
        int height
    ) {
        if (!SETT.IN_BOUNDS(x, y)) {
            return new CommandResult(false, "Out of bounds: (" + x + "," + y + ")");
        }

        Furnisher constructor = blueprint.constructor();
        RoomPlacer placer = SETT.ROOMS().placement.placer;
        try {
            placer.init(blueprint, 0);

            if (constructor.usesArea()) {
                return buildArea(placer, blueprint, x, y, width, height);
            }
            return buildItem(placer, blueprint, x, y, itemGroup);
        } catch (Exception e) {
            return new CommandResult(false, blueprint.key + " error at (" + x + "," + y + "): " + e.getMessage());
        } finally {
            releasePlacementState();
        }
    }

    private static CommandResult buildItem(
        RoomPlacer placer,
        RoomBlueprintImp blueprint,
        int x,
        int y,
        int itemGroup
    ) {
        if (itemGroup >= blueprint.constructor().pgroups().size()) {
            return new CommandResult(false, "Item group " + itemGroup + " invalid for " + blueprint.key);
        }

        PlacableFixed itemPlacer = placer.item(itemGroup);
        CharSequence problem = itemPlacer.placableWhole(x, y);
        if (problem != null) {
            return new CommandResult(false, blueprint.key + " not placeable at (" + x + "," + y + "): " + problem);
        }

        itemPlacer.place(x, y, 0, 0);
        return new CommandResult(true, "Built " + blueprint.key + " at (" + x + "," + y + ")");
    }

    private static CommandResult buildArea(
        RoomPlacer placer,
        RoomBlueprintImp blueprint,
        int x,
        int y,
        int width,
        int height
    ) {
        RectArea area = new RectArea(x, y, width, height);
        PlacableMulti areaPlacer = (PlacableMulti) placer.area();

        for (int ty = area.body().y1(); ty < area.body().y2(); ty++) {
            for (int tx = area.body().x1(); tx < area.body().x2(); tx++) {
                CharSequence tileProblem = areaPlacer.isPlacable(tx, ty, area, PLACER_TYPE.SQUARE);
                if (tileProblem != null) {
                    return new CommandResult(false, blueprint.key + " area blocked at (" + tx + "," + ty + "): " + tileProblem);
                }
            }
        }

        for (int ty = area.body().y1(); ty < area.body().y2(); ty++) {
            for (int tx = area.body().x1(); tx < area.body().x2(); tx++) {
                areaPlacer.place(tx, ty, area, PLACER_TYPE.SQUARE);
            }
        }

        CharSequence createProblem = placer.createProblem();
        if (createProblem != null) {
            placer.init(null, 0);
            return new CommandResult(false, blueprint.key + " create blocked: " + createProblem);
        }

        CharSequence warning = placer.createWarning();
        placer.create();
        String message = "Built " + blueprint.key + " area " + width + "x" + height + " at (" + x + "," + y + ")";
        if (warning != null) {
            message += " (warning: " + warning + ")";
        }
        return new CommandResult(true, message);
    }

    private static int intParam(java.util.Map<String, Object> params, String key, int defaultValue) {
        if (params == null || !params.containsKey(key)) {
            return defaultValue;
        }
        Object raw = params.get(key);
        if (raw instanceof Number number) {
            return number.intValue();
        }
        return defaultValue;
    }

    private static final class RectArea implements AREA {
        private final Rec body;

        RectArea(int x, int y, int width, int height) {
            body = new Rec().setDim(width, height).moveX1Y1(x, y);
        }

        @Override
        public RECTANGLE body() {
            return body;
        }

        @Override
        public boolean is(int tile) {
            int tx = tile % SETT.TWIDTH;
            int ty = tile / SETT.TWIDTH;
            return is(tx, ty);
        }

        @Override
        public boolean is(int tx, int ty) {
            return body.holdsPoint(tx, ty);
        }

        @Override
        public int area() {
            return body.width() * body.height();
        }
    }
}
