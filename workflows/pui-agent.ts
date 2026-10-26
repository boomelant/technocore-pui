import { sleep } from "workflow";
import {
  bootstrapIdentityStep as bootstrapTransport,
  observeAndDecideStep as observeTransport,
  postReplyStep as postTransport,
} from "./steps/pui-cycle-v2";
import { acquireLeaseStep as leaseTransport } from "./steps/resident-lease";
import { publishLifecycleStatusStep as lifecycleTransport } from "./steps/resident-status";

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

// Register steps in the same module as the durable workflow. This makes the
// compiler's step discovery independent of external-step registration, which
// previously failed at runtime despite a successful production build.
async function acquireLeaseStep(holder: string, previousValue: string | null) {
  "use step";
  return leaseTransport(holder, previousValue);
}
acquireLeaseStep.maxRetries = 0;

async function publishLifecycleStatusStep(input: Parameters<typeof lifecycleTransport>[0]) {
  "use step";
  return lifecycleTransport(input);
}
publishLifecycleStatusStep.maxRetries = 0;

async function bootstrapIdentityStep(previousNonce: string) {
  "use step";
  return bootstrapTransport(previousNonce);
}
bootstrapIdentityStep.maxRetries = 0;

async function observeAndDecideStep(state: PuiCloudState) {
  "use step";
  return observeTransport(state);
}
observeAndDecideStep.maxRetries = 0;

async function postReplyStep(action: Parameters<typeof postTransport>[0]) {
  "use step";
  return postTransport(action);
}
postReplyStep.maxRetries = 0;

// Durable graph V6: all five step IDs now belong to workflows/pui-agent.
export async function puiAgentWorkflowV6(holder: string) {
  "use workflow";

  let firstLease: Awaited<ReturnType<typeof acquireLeaseStep>>;
  try {
    firstLease = await acquireLeaseStep(holder, null);
  } catch (error) {
    const failure = failureText(error);
    await publishLifecycleStatusStep({ holder, cycle: 0, phase: "lease_failed", failure });
    return { status: "failed", reason: "lease_failed", holder, failure };
  }

  if (!firstLease.acquired) {
    await publishLifecycleStatusStep({
      holder,
      cycle: 0,
      phase: "lease_rejected",
      failure: firstLease.reason,
    });
    return { status: "standby", reason: firstLease.reason, holder };
  }

  await publishLifecycleStatusStep({ holder, cycle: 0, phase: "lease_acquired" });

  let bootstrap: Awaited<ReturnType<typeof bootstrapIdentityStep>>;
  try {
    bootstrap = await bootstrapIdentityStep("0");
  } catch (error) {
    const failure = failureText(error);
    await publishLifecycleStatusStep({ holder, cycle: 0, phase: "bootstrap_failed", failure });
    return { status: "failed", reason: "bootstrap_failed", holder, failure };
  }

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
