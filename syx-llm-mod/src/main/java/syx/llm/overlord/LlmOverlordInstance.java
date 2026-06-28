package syx.llm.overlord;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import script.SCRIPT.SCRIPT_INSTANCE;
import snake2d.util.file.FilePutter;
import snake2d.util.file.FileGetter;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

/**
 * The actual mod instance that runs during gameplay.
 * Starts an HTTP API server and reads game state each tick.
 */
public class LlmOverlordInstance implements SCRIPT_INSTANCE {

    private static final int PORT = 47823;
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private HttpServer httpServer;
    private final StateReader stateReader = new StateReader();
    private final CommandExecutor commandExecutor = new CommandExecutor();
    private volatile GameState lastState;
    private int tickCount = 0;

    public LlmOverlordInstance() {
        startHttpServer();
    }

    private void startHttpServer() {
        try {
            httpServer = HttpServer.create(new InetSocketAddress(PORT), 0);
            httpServer.setExecutor(Executors.newFixedThreadPool(2));

            httpServer.createContext("/api/state", this::handleGetState);
            httpServer.createContext("/api/command", this::handlePostCommand);
            httpServer.createContext("/api/health", this::handleHealth);

            httpServer.start();
            System.out.println("[LLM Overlord] HTTP API running at http://localhost:" + PORT);
        } catch (IOException e) {
            System.err.println("[LLM Overlord] Failed to start HTTP server: " + e.getMessage());
        }
    }

    // --- SCRIPT_INSTANCE interface ---

    @Override
    public void update(double ds) {
        tickCount++;
        // Read game state every tick (cheap snapshot)
        try {
            lastState = stateReader.readState();
            lastState.tickCount = tickCount;
        } catch (Exception e) {
            // Don't spam errors every tick
            if (tickCount % 100 == 0) {
                System.err.println("[LLM Overlord] State read error: " + e.getMessage());
            }
        }
    }

    @Override
    public void save(FilePutter file) {
        // Persist tick count across saves
        file.i(tickCount);
    }

    @Override
    public void load(FileGetter file) throws IOException {
        tickCount = file.i();
    }

    // --- HTTP handlers ---

    private void handleHealth(HttpExchange exchange) throws IOException {
        sendJson(exchange, 200, "{\"status\":\"ok\",\"tick\":" + tickCount + "}");
    }

    private void handleGetState(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        if (lastState == null) {
            sendJson(exchange, 503, "{\"error\":\"No state available yet, wait for first tick\"}");
            return;
        }
        sendJson(exchange, 200, GSON.toJson(lastState));
    }

    private void handlePostCommand(HttpExchange exchange) throws IOException {
        if (!"POST".equals(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        try {
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            Command cmd = GSON.fromJson(body, Command.class);
            CommandResult result = commandExecutor.execute(cmd);
            sendJson(exchange, result.success ? 200 : 400, GSON.toJson(result));
        } catch (Exception e) {
            sendJson(exchange, 500, "{\"error\":\"" + e.getMessage() + "\"}");
        }
    }

    private void sendJson(HttpExchange exchange, int statusCode, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
