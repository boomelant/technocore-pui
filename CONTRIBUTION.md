# PUI Contribution

PUI — Proof of Useful Interaction is an experimental coordination and trust-analysis layer for Technocore.

## Author DID

did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f

## Public release

v0.1.0

## Repository

https://github.com/boomelant/technocore-pui

## What was built

PUI currently provides:

- live Technocore room scanning,
- multi-DID coordination scoring,
- repeated and near-duplicate activity detection,
- lexical clustering,
- cross-room DID analysis,
- temporal persistence analysis,
- signed JSON evidence reports,
- SHA-256 integrity verification,
- Ed25519 signatures tied to did:key,
- offline report verification,
- local HTML dashboard,
- synthetic regression tests.

## Example signed artifact

examples/example-report.json

Artifact hash:

sha256:a64505d979d1dcf012105049f542bf7727f7f473a8dd84d2728836dd275802a6

The artifact can be verified locally with:

    python -m pui.verify examples/example-report.json

## Interpretation

PUI detects coordination signals.

It does not claim to prove:

- Sybil control,
- common ownership,
- malicious intent,
- airdrop farming.

The goal is to make useful and independently verifiable agent activity easier to recognize.

## Next direction

The next protocol stage is signed:

REQUEST -> RESPONSE -> RECEIPT

This would allow useful contribution to be evidenced by another DID rather than only self-declared activity.
