import { NextResponse } from "next/server";
import { Readable } from "stream";

export const dynamic = "force-dynamic";

interface ChatRequest {
  message: string;
  model?: string;
  maxDepth?: number;
  useRLM?: boolean;
}

export async function POST(request: Request) {
  try {
    const body: ChatRequest = await request.json();
    const { message, model = "llama3.2", maxDepth = 3, useRLM = true } = body;

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        function sendEvent(data: object) {
          const payload = `data: ${JSON.stringify(data)}\n\n`;
          controller.enqueue(encoder.encode(payload));
        }

        try {
          sendEvent({ type: "status", status: "starting", message: "Initializing RLM..." });

          const baseUrl = process.env.OLLAMA_BASE_URL || "http://localhost:11434";
          const fullPrompt = useRLM
            ? `You are a recursive language model that can use the REPL to execute code. The context variable 'context' contains the user's message: "${message}". Use llm_query() if needed to answer. Set FINAL_VAR("answer", <your answer>) when done.`
            : message;

          if (!useRLM) {
            sendEvent({ type: "status", status: "running", message: "Calling Ollama..." });

            const response = await fetch(`${baseUrl}/api/chat`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                model,
                messages: [{ role: "user", content: message }],
                stream: false,
              }),
            });

            if (!response.ok) {
              throw new Error(`Ollama error: ${response.status}`);
            }

            const data = await response.json();
            const assistantMessage = data.message?.content || "";

            sendEvent({
              type: "node",
              node: {
                id: `root_${Date.now()}`,
                parentId: null,
                depth: 0,
                prompt: message,
                response: assistantMessage,
                timestamp: Date.now(),
              },
            });

            sendEvent({
              type: "status",
              status: "completed",
              message: "Complete",
            });

            sendEvent({
              type: "final",
              finalAnswer: assistantMessage,
            });
          } else {
            sendEvent({ type: "status", status: "running", message: "Running RLM with depth " + maxDepth });

            const rootNodeId = `root_${Date.now()}`;

            try {
              const rlmResponse = await callRLMWithCallbacks(
                message,
                model,
                maxDepth,
                (depth, modelName, prompt) => {
                  const nodeId = `node_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`;
                  sendEvent({
                    type: "node",
                    node: {
                      id: nodeId,
                      parentId: depth === 0 ? rootNodeId : null,
                      depth,
                      prompt: prompt,
                      response: "",
                      timestamp: Date.now(),
                    },
                  });
                  return nodeId;
                },
                (depth, modelName, duration, error) => {
                  sendEvent({
                    type: "status",
                    status: "running",
                    message: `Sub-call completed: depth=${depth}, model=${modelName}`,
                  });
                }
              );

              sendEvent({
                type: "node",
                node: {
                  id: rootNodeId,
                  parentId: null,
                  depth: 0,
                  prompt: message,
                  response: rlmResponse,
                  timestamp: Date.now(),
                },
              });

              sendEvent({
                type: "status",
                status: "completed",
                message: "Complete",
              });

              sendEvent({
                type: "final",
                finalAnswer: rlmResponse,
              });
            } catch (rlmError) {
              sendEvent({
                type: "status",
                status: "error",
                message: rlmError instanceof Error ? rlmError.message : "RLM execution failed",
              });
            }
          }

          controller.enqueue(encoder.encode("data: [DONE]\n\n"));
          controller.close();
        } catch (error) {
          sendEvent({
            type: "status",
            status: "error",
            message: error instanceof Error ? error.message : "Unknown error",
          });
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Invalid request" },
      { status: 400 }
    );
  }
}

async function callRLMWithCallbacks(
  prompt: string,
  model: string,
  maxDepth: number,
  onSubcallStart: (
    depth: number,
    modelName: string,
    prompt: string
  ) => string,
  onSubcallComplete: (
    depth: number,
    modelName: string,
    duration: number,
    error: string | null
  ) => void
): Promise<string> {
  const baseUrl = process.env.OLLAMA_BASE_URL || "http://localhost:11434";

  const response = await fetch(`${baseUrl}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      prompt: `You are a recursive language model. Context: "${prompt}". 

Your task is to answer the user's question. You can use Python code blocks to help you think through the problem.

Steps:
1. Understand the question
2. Use code to reason or compute if needed
3. Provide your final answer

When you have an answer, output it as:
FINAL_ANSWER: <your answer here>

Do not output anything else after your final answer.`,
      stream: false,
    }),
  });

  if (!response.ok) {
    throw new Error(`Ollama error: ${response.status}`);
  }

  const data = await response.json();
  return data.response || "No response";
}

export async function GET() {
  return NextResponse.json({
    status: "ok",
    message: "Chat endpoint. POST with { message, model, maxDepth, useRLM }",
  });
}