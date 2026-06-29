package syx.llm.overlord;

import com.google.gson.Gson;
import script.SCRIPT.SCRIPT_INSTANCE;
import snake2d.util.file.FilePutter;
import snake2d.util.file.FileGetter;

import java.io.IOException;

/**
 * Mod instance: HTTP API + per-tick state snapshots.
 * JSON is built on the game thread; HTTP handlers return cached bytes only.
 */
public class LlmOverlordInstance implements SCRIPT_INSTANCE {

    private static final int PORT = 47823;
    private static final int MAX_STATE_BYTES = 256_000;
    private static final Gson GSON = new Gson();

    private SimpleHttpServer httpServer;
    private final StateReader stateReader = new StateReader();
    private final CommandExecutor commandExecutor = new CommandExecutor();
    private volatile String lastStateJson = "{\"error\":\"warming up\"}";
    private int tickCount = 0;

    public LlmOverlordInstance() {
        startHttpServer();
    }

    private void startHttpServer() {
        try {
            httpServer = new SimpleHttpServer(PORT, 1);
            httpServer.route("/api/health", this::handleHealth);
            httpServer.route("/api/state", this::handleGetState);
            httpServer.route("/api/command", this::handlePostCommand);
            httpServer.start();
            System.out.println("[LLM Overlord] HTTP API running at http://localhost:" + PORT);
        } catch (IOException e) {
            System.err.println("[LLM Overlord] Failed to start HTTP server: " + e.getMessage());
        }
    }

    @Override
    public void update(double ds) {
        tickCount++;
        if (tickCount != 1 && tickCount % 10 != 0) {
            return;
        }
        try {
            GameState state = stateReader.readState();
            state.tickCount = tickCount;
            String json = GSON.toJson(state);
            if (json.length() > MAX_STATE_BYTES) {
                json = "{\"error\":\"state too large\",\"tick\":" + tickCount + "}";
            }
            lastStateJson = json;
        } catch (OutOfMemoryError oom) {
            lastStateJson = "{\"error\":\"oom reading state\",\"tick\":" + tickCount + "}";
            System.err.println("[LLM Overlord] OOM reading state at tick " + tickCount);
        } catch (Exception e) {
            if (tickCount % 100 == 0) {
                System.err.println("[LLM Overlord] State read error: " + e.getMessage());
            }
        }
    }

    @Override
    public void save(FilePutter file) {
        file.i(tickCount);
    }

    @Override
    public void load(FileGetter file) throws IOException {
        tickCount = file.i();
    }

    private void handleHealth(SimpleHttpServer.Request request, SimpleHttpServer.Response response) {
        response.json(200, "{\"status\":\"ok\",\"tick\":" + tickCount + "}");
    }

    private void handleGetState(SimpleHttpServer.Request request, SimpleHttpServer.Response response) {
        if (!"GET".equals(request.method)) {
            response.json(405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        if (tickCount < 1) {
            response.json(503, "{\"error\":\"No state available yet, wait for first tick\"}");
            return;
        }
        response.json(200, lastStateJson);
    }

    private void handlePostCommand(SimpleHttpServer.Request request, SimpleHttpServer.Response response) {
        if (!"POST".equals(request.method)) {
            response.json(405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        try {
            Command cmd = GSON.fromJson(request.body, Command.class);
            CommandResult result = commandExecutor.execute(cmd);
            response.json(result.success ? 200 : 400, GSON.toJson(result));
        } catch (Exception e) {
            response.json(500, "{\"error\":\"" + escapeJson(e.getMessage()) + "\"}");
        }
    }

    private static String escapeJson(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}
