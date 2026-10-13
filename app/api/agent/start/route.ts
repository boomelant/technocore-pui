import { start } from "workflow/api";
import { puiAgentWorkflow } from "@/workflows/pui-agent";
import { verifyGithubActionsOidc } from "@/src/cloud/github-oidc.mjs";

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
  const holder = `vercel-${crypto.randomUUID().replaceAll("-", "").slice(0, 12)}`;
  const run = await start(puiAgentWorkflow, [holder]);
  return Response.json({ status: "started", runId: run.runId, holder });
}

export const GET = launch;
export const POST = launch;
