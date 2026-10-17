import { PUI_DID, TECHNOCORE_BASE } from "@/src/cloud/core.mjs";
import { PUI_RESIDENT_REVISION } from "@/src/cloud/participation.mjs";

type LifecyclePhase = "bootstrapped" | "observe_failed";

type LifecycleStatusInput = {
  holder: string;
  cycle: number;
  presence: string;
  phase: LifecyclePhase;
  failure?: string | null;
};

function clippedFailure(value: string | null | undefined) {
  const text = String(value ?? "unknown runtime failure").replace(/\s+/g, " ").trim();
  return text.slice(0, 180);
}

export async function publishLifecycleStatusStep(input: LifecycleStatusInput) {
  "use step";

  const failure = input.failure ? `runtime ${input.phase}: ${clippedFailure(input.failure)}` : null;
  const status = {
    protocol: "PUI-CLOUD-RESIDENT/2",
    revision: PUI_RESIDENT_REVISION,
    did: PUI_DID,
    holder: input.holder,
    at: new Date().toISOString(),
    cycle: input.cycle,
    presence: input.presence,
    watchRooms: [],
    observedThisCycle: 0,
    totalObserved: 0,
    totalReplies: 0,
    candidate: null,
    replyCandidate: null,
    decision: failure
      ? { decision: "observe", confidence: 1, model: null, failure }
      : null,
    officialChanged: [],
    zeroCost: true,
    phase: input.phase,
  };

  const response = await fetch(`${TECHNOCORE_BASE}/kv/pui-cloud/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ value: JSON.stringify(status) }),
    cache: "no-store",
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`lifecycle status write HTTP ${response.status}: ${body.slice(0, 160)}`);
  }
  return status;
}
publishLifecycleStatusStep.maxRetries = 0;
