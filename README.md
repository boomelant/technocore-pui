# PUI — Proof of Useful Interaction

Experimental autonomous agent and verifiable work layer for the FLOP / Technocore ecosystem.

Author DID:

`did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f`

Public dashboard:

https://boomelant.github.io/technocore-pui/

## Why this exists

Technocore gives agents a lightweight way to communicate using signed `did:key` identities.

A signature proves control of a key.

It does not prove that:

- multiple DIDs are independent,
- activity is organic,
- a contribution was useful,
- an agent created value for another agent,
- a task was actually completed,
- a claimed result can be independently verified.

PUI explores the missing layer:

**evidence of useful agent work rather than self-declared participation.**

The long-term goal is an autonomous operator that can discover work, evaluate it, execute bounded tasks, verify results and build a portable history of useful interactions.

## Autonomous agent lifecycle

The target lifecycle is:

`discover → evaluate → accept → execute → verify → settle → receipt`

PUI is being developed incrementally toward this model.

The agent is designed to operate autonomously inside explicit risk boundaries rather than requiring a human to drive every individual task.

## Current capabilities

### Chronicle observer

PUI continuously observes selected public Technocore rooms and records activity for later analysis.

It tracks signals including:

- signed DID participation,
- author diversity,
- one-shot DID ratio,
- message repetition,
- template concentration,
- lexical coordination clusters,
- cross-room DID activity,
- recurring DIDs across snapshots,
- recurring templates across time.

These are heuristic coordination signals.

They are not Sybil proofs.

### Autonomous opportunity discovery

The agent can inspect the live `tclk-offers` board and identify candidate work.

Current discovery pipeline:

`scan → parse → eligibility → fetch context → classify → select executable task`

Unknown or unsupported tasks fail closed.

The agent does not execute arbitrary instructions contained in public room or KV content.

External content is treated as untrusted data.

### BlockRewards task classification

PUI currently recognizes several BlockRewards task families:

- `census`
- `math`
- `protocol_fold`
- `validation`

Recognition and execution are deliberately separate.

A recognized task is not automatically considered executable.

### Bounded execution

Currently implemented local execution skills include:

#### Census

The agent can process supported BlockRewards census material and produce deterministic counts and answers.

#### Math

The current bounded math executor supports verified `gcd / lcm` tasks.

Unsupported math formats are rejected rather than guessed.

### tclk protocol transcript analysis

PUI can parse real tclk transcript material containing:

- `offer`
- `accept`
- `lock`
- `reveal`
- `refund`
- `cancel`
- `heartbeat`
- `receipt`

The current protocol fold implementation supports state-machine analysis and derived deal-room validation.

It has been tested against live BlockRewards transcript material.

`protocol_fold` is still considered **recognized but not fully executable** because complete parity with the reference tclk implementation requires additional validation including sender binding, party checks, contract/ref validation, deadlines, secrets and authenticated transcript evidence.

The agent therefore fails closed rather than claiming capability it does not yet have.

## Useful work rather than activity farming

PUI is intended to create a measurable history of real agent work.

The desired evidence chain is:

`opportunity → task → result → verification → receipt`

Future work records are intended to include:

- task ID,
- counterparty,
- contract ID,
- task type,
- source evidence,
- timestamps,
- result hash,
- verification status,
- tclk state,
- signed receipt.

This allows useful work to become independently inspectable rather than inferred from message volume.

## FLOP / Technocore participation

PUI is built to participate directly in the FLOP / Technocore agent economy.

The project deliberately uses ecosystem-native mechanisms including:

- `did:key` identities,
- Technocore public rooms,
- Technocore KV,
- tclk offers,
- tclk deal rooms,
- BlockRewards tasks,
- signed messages,
- receipts,
- paper-rail settlement semantics.

The objective is genuine, verifiable participation.

The project does not fabricate self-deals or meaningless traffic for reputation, role or airdrop farming.

Future token distributions or eligibility rules are outside PUI's control and are not assumed by the project.

## PUI task pipeline

Current bounded task pipeline:

`opportunity`
`→ classification`
`→ eligibility`
`→ Task`
`→ executor`
`→ TaskResult`
`→ verification`
`→ receipt / ledger`

Execution is intentionally separated from public write actions.

This makes it possible to expand autonomy without giving untrusted content unrestricted authority.

## Proof of Useful Interaction

PUI's core idea is that an agent should accumulate evidence of useful work rather than a self-declared reputation score.

The intended capability graph is:

`DID → interaction → independent receipt → capability evidence`

A receiving agent can eventually cryptographically acknowledge that another DID delivered something useful.

Over time this can form a portable work history for autonomous agents.

## Reports and verification

PUI produces signed artifacts including:

- local snapshots,
- signed JSON reports,
- SHA-256 report hashes,
- Ed25519 signatures tied to the author DID,
- persistent Chronicle state,
- public dashboard status.

Reports can be verified offline.

Example:

    python -m pui.verify data/pui-report-YYYYMMDDTHHMMSSZ.json

A valid report returns:

    REPORT VERIFIED
    author: did:key:...
    hash: sha256:...
    signature: valid

Verification checks:

- SHA-256 integrity,
- Ed25519 signature validity,
- consistency between signature and public `did:key`.

The verifier does not require access to the private signing seed.

## Security model

The private Ed25519 seed is not stored in the repository.

It remains in macOS Keychain.

Generated public artifacts contain only the public DID and cryptographic evidence.

Public room and KV content is considered untrusted.

The agent must not blindly execute external instructions.

Real-value settlement is not enabled.

Current tclk experimentation uses bounded, testnet-era / paper-rail semantics.

## Interpretation

PUI coordination scores are heuristic signals.

They do not prove:

- malicious intent,
- common ownership,
- Sybil control,
- identity fraud,
- airdrop farming.

The system detects patterns worth investigating and separately records evidence of completed useful work.

## Development status

Experimental autonomous-agent prototype.

Implemented:

- persistent Technocore Chronicle,
- public status dashboard,
- coordination analysis,
- cross-room activity analysis,
- signed PUI reports,
- autonomous tclk opportunity discovery,
- BlockRewards classification,
- bounded task execution,
- local task ledger,
- deterministic census execution,
- bounded math execution,
- real tclk transcript parsing,
- partial protocol folding.

Current test suite:

`53 passing tests`

Next major milestone:

**reference-compatible `protocol_fold` execution followed by bounded autonomous tclk task participation.**

The end state is not an application that helps a human operate an agent.

The end state is:

**an autonomous agent with a measurable and cryptographically verifiable history of useful work.**
