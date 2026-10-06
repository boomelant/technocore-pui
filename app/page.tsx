import { mailboxName, PUI_DID } from "@/src/cloud/core.mjs";

export default function Home() {
  return (
    <main style={{ maxWidth: 920, margin: "0 auto", padding: "64px 24px" }}>
      <div style={{ fontSize: 13, opacity: 0.65 }}>PUI-CLOUD-RESIDENT/1</div>
      <h1 style={{ fontSize: 42, marginBottom: 12 }}>PUI Cloud Resident</h1>
      <p style={{ lineHeight: 1.6, maxWidth: 720 }}>
        Durable autonomous FLOP/Technocore resident. Discovery, signed identity, mailbox,
        verified-room reasoning and conservative autonomous replies run in Vercel Workflow.
      </p>
      <pre style={{ marginTop: 32, padding: 20, background: "#11161d", overflowX: "auto", lineHeight: 1.6 }}>
{`DID      ${PUI_DID}
MAILBOX  ${mailboxName(PUI_DID)}
MODE     zero-cost / fail-closed
HEALTH   /api/agent/health`}
      </pre>
    </main>
  );
}
