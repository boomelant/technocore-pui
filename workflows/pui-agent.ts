import { sleep } from "workflow";
import {
  acquireLeaseStep,
  bootstrapIdentityStep,
  observeAndDecideStep,
  postReplyStep,
} from "./steps/pui-cycle-v2";
import { publishLifecycleStatusStep } from "./steps/resident-status";

export type PuiCloudState = {
  cycle: number;
  eventCursor: number | null;
  roomCursors: Record<string, number>;
  dynamicRooms: string[];
  officialHashes: Record<string, string>;
  cooldowns: Record<string, number>;
  lastNonceByRoom: Record<string, string>;
  totalObserved: number;
  totalReplies: number;
  leaseValue: string | null;
  mailbox: string;
  holder: string;
  presence: string;
};

function failureText(error: unknown) {
  if (error instanceof Error) return `${error.name}: ${error.message}`;
  return String(error);
}

// Version the workflow symbol when the durable orchestration contract changes.
// This prevents a new /start call from reviving an older registered definition.
export async function puiAgentWorkflowV3(holder: string) {
  "use workflow";

  const firstLease = await acquireLeaseStep(holder, null);
  if (!firstLease.acquired) {
    return { status: "standby", reason: firstLease.reason, holder };
  }

  const bootstrap = await bootstrapIdentityStep("0");
  let state: PuiCloudState = {
    cycle: 0,
    eventCursor: null,
    roomCursors: {},
    dynamicRooms: [],
    officialHashes: {},
    cooldowns: {},
    lastNonceByRoom: { [bootstrap.mailbox]: bootstrap.nonce },
    totalObserved: 0,
    totalReplies: 0,
    leaseValue: firstLease.value,
    mailbox: bootstrap.mailbox,
    holder,
    presence: bootstrap.presence,
  };

  await publishLifecycleStatusStep({
    holder,
    cycle: 0,
    presence: bootstrap.presence,
    phase: "bootstrapped",
  });

  while (true) {
    let cycleResult: Awaited<ReturnType<typeof observeAndDecideStep>>;
    try {
      cycleResult = await observeAndDecideStep(state);
    } catch (error) {
      const failure = failureText(error);
      await publishLifecycleStatusStep({
        holder,
        cycle: state.cycle,
        presence: state.presence,
        phase: "observe_failed",
        failure,
      });
      return { status: "failed", reason: "observe_failed", holder, failure };
    }

    state = cycleResult.state;

    if (cycleResult.action) {
      const posted = await postReplyStep(cycleResult.action);
      if (posted.status === "confirmed") state.totalReplies += 1;
    }

    await sleep("5m");

    const lease = await acquireLeaseStep(holder, state.leaseValue);
    if (!lease.acquired) {
      return { status: "standby", reason: lease.reason, holder };
    }
    state.leaseValue = lease.value;
  }
}
