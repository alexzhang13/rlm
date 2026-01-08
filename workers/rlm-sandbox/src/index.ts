/**
 * RLM Sandbox Worker
 *
 * Cloudflare Worker providing sandbox execution for CloudflareREPL.
 * Implements the API endpoints required by rlm/environments/cloudflare_repl.py
 */

import { getSandbox } from "@cloudflare/sandbox";

// Re-export Sandbox for Durable Objects binding
export { Sandbox } from "@cloudflare/sandbox";

interface Env {
  Sandbox: DurableObjectNamespace;
  // Optional: Bearer token for authentication
  AUTH_TOKEN?: string;
}

interface ExecRequest {
  sandbox_id: string;
  command: string;
}

interface WriteRequest {
  sandbox_id: string;
  path: string;
  content: string;
}

/**
 * Validate authentication token
 */
function validateAuth(request: Request, env: Env): Response | null {
  // If no AUTH_TOKEN configured, allow all requests (dev mode)
  if (!env.AUTH_TOKEN) {
    return null;
  }

  const authHeader = request.headers.get("Authorization");
  if (!authHeader) {
    return Response.json(
      { error: "Authorization header required" },
      { status: 401 }
    );
  }

  const token = authHeader.replace(/^Bearer\s+/i, "");
  if (token !== env.AUTH_TOKEN) {
    return Response.json({ error: "Invalid token" }, { status: 401 });
  }

  return null;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Health check - no auth required
    if (url.pathname === "/" || url.pathname === "/health") {
      return Response.json({
        status: "ok",
        service: "rlm-sandbox",
        timestamp: Date.now(),
      });
    }

    // All sandbox endpoints require auth
    const authError = validateAuth(request, env);
    if (authError) {
      return authError;
    }

    // ==================== Sandbox Endpoints ====================

    /**
     * POST /sandbox/exec
     * Execute a command in the sandbox
     *
     * Request body: { sandbox_id: string, command: string }
     * Response: { stdout: string, stderr: string, exitCode: number, success: boolean }
     */
    if (url.pathname === "/sandbox/exec" && request.method === "POST") {
      try {
        const body = (await request.json()) as ExecRequest;

        if (!body.sandbox_id || !body.command) {
          return Response.json(
            { error: "sandbox_id and command are required" },
            { status: 400 }
          );
        }

        const sandbox = getSandbox(env.Sandbox, body.sandbox_id);
        const result = await sandbox.exec(body.command);

        return Response.json({
          stdout: result.stdout,
          stderr: result.stderr,
          exitCode: result.exitCode,
          success: result.success,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return Response.json({ error: message }, { status: 500 });
      }
    }

    /**
     * POST /sandbox/write
     * Write a file to the sandbox
     *
     * Request body: { sandbox_id: string, path: string, content: string }
     * Response: { success: boolean }
     */
    if (url.pathname === "/sandbox/write" && request.method === "POST") {
      try {
        const body = (await request.json()) as WriteRequest;

        if (!body.sandbox_id || !body.path || body.content === undefined) {
          return Response.json(
            { error: "sandbox_id, path, and content are required" },
            { status: 400 }
          );
        }

        const sandbox = getSandbox(env.Sandbox, body.sandbox_id);
        await sandbox.writeFile(body.path, body.content);

        return Response.json({ success: true });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return Response.json({ error: message, success: false }, { status: 500 });
      }
    }

    /**
     * GET /sandbox/read
     * Read a file from the sandbox
     *
     * Query params: sandbox_id, path
     * Response: { content: string, success: boolean }
     */
    if (url.pathname === "/sandbox/read" && request.method === "GET") {
      try {
        const sandboxId = url.searchParams.get("sandbox_id");
        const path = url.searchParams.get("path");

        if (!sandboxId || !path) {
          return Response.json(
            { error: "sandbox_id and path query params are required" },
            { status: 400 }
          );
        }

        const sandbox = getSandbox(env.Sandbox, sandboxId);
        const file = await sandbox.readFile(path);

        return Response.json({
          content: file.content,
          success: true,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return Response.json(
          { error: message, content: "", success: false },
          { status: 500 }
        );
      }
    }

    /**
     * GET /sandbox/health
     * Check if sandbox is healthy
     *
     * Query params: sandbox_id (optional, defaults to "health-check")
     */
    if (url.pathname === "/sandbox/health" && request.method === "GET") {
      try {
        const sandboxId = url.searchParams.get("sandbox_id") || "health-check";
        const sandbox = getSandbox(env.Sandbox, sandboxId);
        const result = await sandbox.exec("python3 --version");

        return Response.json({
          status: "healthy",
          python: result.stdout.trim(),
          exitCode: result.exitCode,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown error";
        return Response.json(
          { status: "unhealthy", error: message },
          { status: 500 }
        );
      }
    }

    // 404 for unknown routes
    return Response.json(
      {
        error: "Not found",
        endpoints: [
          "GET /health",
          "POST /sandbox/exec",
          "POST /sandbox/write",
          "GET /sandbox/read",
          "GET /sandbox/health",
        ],
      },
      { status: 404 }
    );
  },
};
