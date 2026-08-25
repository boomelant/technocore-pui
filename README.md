# PUI — Proof of Useful Interaction

Experimental trust and coordination analysis layer for Technocore.

Author DID:

`did:key:z6Mkub4QuoxnRWkzjKLmJtcikyoYjVEhrZVtvs2EA3PX1N3f`

## Why this exists

Technocore gives agents a lightweight way to communicate using signed `did:key` identities.

A signature proves control of a key.

It does not prove that:

- multiple DIDs are independent,
- activity is organic,
- a contribution was useful,
- an agent created value for another agent.

PUI explores a missing layer:

**evidence of useful interaction rather than self-declared participation.**

## What the current prototype does

The scanner reads live Technocore rooms and measures:

- signed DID participation,
- author diversity,
- one-shot DID ratio,
- message repetition,
- template concentration,
- semantic coordination clusters,
- cross-room DID activity,
- recurring DIDs across snapshots,
- recurring templates across time.

It then produces:

- local snapshots,
- a signed JSON report,
- a SHA-256 report hash,
- an Ed25519 signature tied to the author's DID,
- a local HTML dashboard.

## Example observed pattern

A room can show very high DID diversity while simultaneously containing highly repetitive activity.

That means identity diversity alone can overestimate organic participation.

PUI separates:

`many identities`

from:

`many independently useful interactions`.

## Run

The project intentionally has minimal system impact.

Requirements:

- macOS
- Python 3.12+
- local virtual environment
- `cryptography`

Run:

```bash
./run.sh

The application:

reads selected live Technocore rooms,
analyzes coordination signals,
stores a snapshot,
compares recent history,
generates a signed report,
updates the local dashboard.
Project layout
pui/
  identity.py
  technocore.py
  protocol.py
  scoring.py
  clusters.py
  coordination.py
  graph.py
  history.py
  report.py
  dashboard.py
  main.py

spec/
  PUI-1.md

data/
  local snapshots and reports
Security

The private Ed25519 seed is not stored in the repository.

It remains in macOS Keychain.

Generated reports contain only the public DID and cryptographic signatures.

Interpretation

PUI scores are heuristic signals.

They do not prove:

malicious intent,
common ownership,
Sybil control,
identity fraud,
airdrop farming.

The project detects patterns worth investigating.

Longer-term direction

The scanner is only the observational first stage.

The intended PUI protocol introduces signed:

REQUEST
RESPONSE
RECEIPT

objects.

A receiving agent can cryptographically acknowledge that another DID delivered something useful.

This enables a future capability graph:

DID -> interaction -> independent receipt -> capability evidence

instead of a global self-declared reputation score.

Status

Experimental prototype.

The goal is to test whether useful agent interaction can become a portable, cryptographically verifiable primitive without changing Technocore's lightweight architecture.
