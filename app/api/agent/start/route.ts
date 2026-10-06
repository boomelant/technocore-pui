import { start } from "workflow/api";
import { puiAgentWorkflow } from "@/workflows/pui-agent";

function authorized(request: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret) return false;
  return request.headers.get("authorization") === `Bearer ${secret}`;
}

async function launch(request: Request) {
  if (!authorized(request)) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  if (!process.env.PUI_SEED) {
    return Response.json({ error: "PUI_SEED missing" }, { status: 503 });
  }
  const holder = `vercel-${crypto.randomUUID().replaceAll("-", "").slice(0, 12)}`;
  const run = await start(puiAgentWorkflow, [holder]);
  return Response.json({ status: "started", runId: run.runId, holder });
}

export const GET = launch;
export const POST = launch;
