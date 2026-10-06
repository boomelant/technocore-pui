import { sleep } from "workflow/sleep";
import {
  acquireLeaseStep,
  bootstrapIdentityStep,
  observeAndDecideStep,
  postReplyStep,
} from "./steps/pui-cycle";

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
};

export async function puiAgentWorkflow(holder: string) {
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
    totalReplies: bootstrap.presence === "confirmed" ? 1 : 0,
    leaseValue: firstLease.value,
    mailbox: bootstrap.mailbox,
  };

  while (true) {
    const cycleResult = await observeAndDecideStep(state);
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
