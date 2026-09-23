"""Local, explicitly approved Technocore reply. Never reads or prints key material."""
import argparse
import json

from .chat_reply import prepare_reply, send_reviewed_reply


def main(argv=None):
    parser = argparse.ArgumentParser(description="Draft or send one source-linked signed reply")
    parser.add_argument("--room", required=True, help="Existing public room or own mailbox")
    parser.add_argument("--source-seq", required=True, type=int, help="Existing signed message sequence")
    parser.add_argument("--reply", required=True, help="Substantive reply, written after reviewing source")
    parser.add_argument("--send", action="store_true", help="Explicitly approve signing and posting")
    args = parser.parse_args(argv)

    draft = prepare_reply(args.room, args.source_seq, args.reply)
    if not args.send:
        print(json.dumps(draft, ensure_ascii=False, indent=2))
        return 0

    receipt = send_reviewed_reply(draft, approved=True)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["status"] in ("confirmed", "already_posted") else 2


if __name__ == "__main__":
    raise SystemExit(main())
