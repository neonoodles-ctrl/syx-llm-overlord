package syx.llm.overlord;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import script.SCRIPT;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

/**
 * Songs of Syx mod that exposes game state via HTTP and accepts commands,
 * allowing an external LLM to observe and control the game.
 *
 * Enable this script in new game settings under "Scripts".
 */
public class LlmOverlordScript implements SCRIPT {

    private static final int PORT = 47823;
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

    private HttpServer httpServer;
    private final StateReader stateReader = new StateReader();
    private final CommandExecutor commandExecutor = new CommandExecutor();

    @Override
    public void initBeforeGameInited() {
        System.out.println("[LLM Overlord] Initializing...");
    }

    @Override
    public void initBeforeGameCreated() {
        System.out.println("[LLM Overlord] Starting HTTP API on port " + PORT);
        try {
            httpServer = HttpServer.create(new InetSocketAddress(PORT), 0);
            httpServer.setExecutor(Executors.newFixedThreadPool(2));

            httpServer.createContext("/api/state", this::handleGetState);
            httpServer.createContext("/api/command", this::handlePostCommand);
            httpServer.createContext("/api/info", this::handleGetInfo);
            httpServer.createContext("/api/health", this::handleHealth);

            httpServer.start();
            System.out.println("[LLM Overlord] HTTP API running at http://localhost:" + PORT);
        } catch (IOException e) {
            System.err.println("[LLM Overlord] Failed to start HTTP server: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void handleHealth(HttpExchange exchange) throws IOException {
        sendJson(exchange, 200, "{\"status\":\"ok\",\"mod\":\"syx-llm-overlord\"}");
    }

    private void handleGetInfo(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        String info = GSON.toJson(new java.util.HashMap<>() {{
            put("mod", "syx-llm-overlord");
            put("version", "1.0.0");
            put("port", PORT);
            put("endpoints", java.util.List.of(
                "GET /api/health",
                "GET /api/info",
                "GET /api/state",
                "POST /api/command"
            ));
        }});
        sendJson(exchange, 200, info);
    }

    private void handleGetState(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"Method not allowed\"}");
            return;
        }
        try {
            GameState state = stateReader.readState();
            sendJson(exchange, 200, GSON.toJson(state));
        } catch (Exception e) {
            System.err.println("[LLM Overlord] Error reading state: " + e.getMessage());
            sendJson(exchange, 500, "{\"error\":\"Failed to read game state: " + e.getMessage() + "\"}");
        }
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
            System.err.println("[LLM Overlord] Error executing command: " + e.getMessage());
            sendJson(exchange, 500, "{\"error\":\"Command execution failed: " + e.getMessage() + "\"}");
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
