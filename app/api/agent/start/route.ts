import { start } from "workflow/api";
import { puiAgentWorkflowV4 } from "@/workflows/pui-agent";
import { verifyGithubActionsOidc } from "@/src/cloud/github-oidc.mjs";

const HOLDER = /^[a-z0-9][a-z0-9-]{0,38}$/;

async function authorized(request: Request) {
  const auth = request.headers.get("authorization") ?? "";
  const secret = process.env.CRON_SECRET;
  if (secret && auth === `Bearer ${secret}`) return true;

  if (!auth.startsWith("Bearer ")) return false;
  const token = auth.slice("Bearer ".length).trim();
  if (!token) return false;

  return verifyGithubActionsOidc(token);
}

async function launch(request: Request) {
  if (!(await authorized(request))) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!process.env.PUI_SEED) {
    return Response.json({ error: "PUI_SEED missing" }, { status: 503 });
  }

  const requestedHolder = request.headers.get("x-pui-holder")?.trim() ?? "";
  if (requestedHolder && !HOLDER.test(requestedHolder)) {
    return Response.json({ error: "invalid holder" }, { status: 400 });
  }
  const holder = requestedHolder || `vercel-${crypto.randomUUID().replaceAll("-", "").slice(0, 12)}`;
  try {
    const run = await start(puiAgentWorkflowV4, [holder]);
    return Response.json({ status: "started", runId: run.runId, holder, workflow: "puiAgentWorkflowV4" });
  } catch (error) {
    // Never echo arbitrary exception text to clients (it may contain secrets).
    // Return an allowlisted reason so an authenticated watchdog can distinguish
    // an unregistered workflow from a transient server-side failure.
    const message = error instanceof Error ? error.message : String(error);
    const kind = /step .*not registered in the current deployment/i.test(message)
      ? "workflow_step_unregistered"
      : /invalid workflow function|workflow .*not registered|cannot find workflow/i.test(message)
        ? "workflow_entry_unregistered"
        : "workflow_start_failed";
    console.error("PUI resident start failed", {
      kind,
      name: error instanceof Error ? error.name : "UnknownError",
    });
    return Response.json(
      { error: kind, workflow: "puiAgentWorkflowV4" },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}

export const GET = launch;
export const POST = launch;
