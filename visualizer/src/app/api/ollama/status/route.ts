import { NextResponse } from "next/server";

export async function GET() {
  const baseUrl = process.env.OLLAMA_BASE_URL || "http://localhost:11434";

  try {
    const response = await fetch(`${baseUrl}/api/tags`, {
      method: "GET",
    });

    if (response.ok) {
      const data = await response.json();
      const models = (data.models || []).map((m: { name?: string }) => m.name || "unknown");

      return NextResponse.json({
        connected: true,
        baseUrl,
        models,
      });
    }

    return NextResponse.json({
      connected: false,
      error: `HTTP ${response.status}`,
    });
  } catch (error) {
    return NextResponse.json({
      connected: false,
      error: error instanceof Error ? error.message : "Connection failed",
    });
  }
}