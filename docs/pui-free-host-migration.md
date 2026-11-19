# PUI — migration away from Vercel (LOW, original DID only)

## Current blocker (2026-11-19)
Vercel project `technocore-pui` reports `live: false`; last READY artifact is 2026-10-18.
`.github/workflows/technocore-activity.yml` currently calls
`https://technocore-pui.vercel.app/api/agent/start` and is **not** a resident.
The durable `workflows/pui-agent.ts` loop uses Vercel Workflow, so merely
rescheduling the existing watchdog cannot revive the agent.

## Identity and hard safety requirements
- **Never create or rotate DID.** The only accepted DID is
  `did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f`.
- The seed reportedly exists in macOS Keychain. A trusted owner must move it
  to GitHub Actions repository secret `PUI_SEED` if using Actions. Never
  print, commit, artifact, or paste the seed into issues or chat.
- Call `assertPuiIdentity` before any network write; fail closed on mismatch.
- The preflight workflow is **manual and read-only**. It confirms identity
  and network access; it does not revive the resident or write any posts.
- Use the existing `pui-cloud/resident-lease` conditional CAS; never start
  another active writer while a valid Vercel lease remains.
- Every public POST needs a distinct exact nonce, Ed25519 signature, source
  validation, idempotency claim, and a subsequent read-back matching DID,
  room, nonce, signature and text with numeric `seq`.
- Ambiguous POST must **not** be retried. Do not count HTTP 200, claimed
  status KV, or a watchdog SUCCESS as signed visibility.
- No paid model, no wallet/transfer, no new worker, no other DID.

## Phased migration
1. Run `PUI free-host migration preflight (read-only)` manually. Its success
   means only that the original DID can be derived and public reads work.
2. Extract a **finite** stateful cycle from
   `workflows/steps/pui-cycle-v2.ts` into Node runtime without `use workflow`
   or `sleep('5m')`; use fixed, bounded room reads and no model requirement.
3. Add tests for protocol Unicode, exact 19-digit nonce JSON handling,
   small-order Ed25519 rejection, message-window gaps, lease contention,
   ambiguous writes, and matching read-back. Resolve PRs #59–#62 conflicts.
4. Add a bounded `schedule` workflow at a non-round minute (e.g. every 15
   minutes) **only after** all tests pass and original seed is available.
   GitHub Actions is a scheduled batch platform, not a guaranteed 24/7 daemon;
   public repository hosted runners have usage/TOS conditions.
5. Prove one genuine signed room+seq read-back under canonical DID, then
   record independent participants' replies and actual further engagement.
6. Move the same finite cycle to a pre-existing Always Free Oracle VM or an
   always-on Mac for continuous execution. Use `systemd` / `launchd` and
   a persistent local state store. Never run two writers concurrently.
7. Decommission the old Vercel watchdog **after** the new holder is proven.

## Acceptance checklist
- [ ] Original key securely available to new runner
- [ ] Read-only preflight PASS
- [ ] Node standalone finite cycle and tests PASS
- [ ] Lease collision tests PASS, only one holder
- [ ] First signed room+seq + independent read-back
- [ ] Real participant reply and one genuine continuation
- [ ] No paid resource usage

No checkbox is satisfied merely by opening this draft PR.
