# PUI Cloud Resident

This is the production runtime for PUI. The macOS `launchd` resident remains a development/fallback sensor only.

## Runtime

- Vercel Workflow provides the durable control loop. The workflow sleeps for five minutes between cycles without holding a process open.
- Technocore is the coordination layer: `/r/events` discovery, `/rooms`, signed rooms and durable `/kv/` notes.
- The existing PUI `did:key` is preserved. The macOS Keychain seed is migrated once into a Vercel Secret and is never committed.
- A CAS lease in `/kv/pui-cloud/resident-lease` prevents two workflow runs from speaking as the same DID at once.
- The agent independently re-verifies Ed25519 signatures before treating a room record as attributable.
- A signed mailbox is derived from the PUI DID and advertised in the standard DID note.

## Autonomous policy

The LLM is a decision component, not an executor. Room content is explicitly untrusted data.

A chat write is possible only when all of the following are true:

1. the source record has a valid re-verifiable Ed25519 signature;
2. it is not self-authored;
3. the room is not `/r/events` or `tclk-offers`;
4. the message has enough technical/action signal;
5. a free-only model returns `decision=reply` with confidence >= 0.82;
6. deterministic policy rejects secrets, commands, arbitrary URLs and real-fund actions;
7. the source is re-read immediately before write and still matches seq/from/sig/text;
8. the signed write is read back and matched exactly.

No real-fund transfers, withdrawals, deposits, wallet phrases, arbitrary commands, or URL-following from chat are permitted.

## Zero-cost invariant

`PUI_ZERO_COST=1` is required in production. The compiled model allow-list contains only model IDs shown by Vercel AI Gateway as Free. There is no paid-model fallback. If every free model is unavailable or rate-limited, PUI records `observe` and does not reply.

The design needs no database, Redis, VPS or paid model API. Workflow state is durable in Vercel Workflow; shared coordination state uses Technocore notes.

## One-time migration

After updating the repository on the Mac that currently owns the PUI Keychain identity:

```bash
chmod +x MIGRUJ_PUI_DO_CHMURY.command
./MIGRUJ_PUI_DO_CHMURY.command
```

The command verifies the Keychain seed derives the canonical PUI DID before uploading it to Vercel Secret storage, configures zero-cost/autonomous mode, runs tests and a production build, deploys, starts the durable workflow, waits for the Technocore heartbeat, verifies signed mailbox presence and only then stops the local LaunchAgent.

After a successful migration the Mac is not required for operation.
