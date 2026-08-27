import subprocess
import time
import sys

from pui.chronicle_status import write_status


FILES = [
    "docs/chronicle-status.json",
    "public/chronicle-status.json",
]


def run(*args):
    return subprocess.run(
        args,
        text=True,
        capture_output=True,
    )


def main():
    repo_status = run("git", "status", "--short")

    if repo_status.returncode != 0:
        print(repo_status.stderr.strip())
        raise SystemExit(repo_status.returncode)

    allowed = set(FILES)
    unexpected = []

    for line in repo_status.stdout.splitlines():
        if not line.strip():
            continue

        path = line[3:].strip()

        if path not in allowed:
            unexpected.append(line)

    if unexpected:
        print("PUBLISH ABORTED: unrelated repository changes detected")

        for line in unexpected:
            print(line)

        raise SystemExit(2)

    write_status(publish=True)

    status = run("git", "status", "--short", "--", *FILES)

    if status.returncode != 0:
        print(status.stderr.strip())
        raise SystemExit(status.returncode)

    if not status.stdout.strip():
        print("NO PUBLIC STATUS CHANGES")
        return

    add = run("git", "add", *FILES)

    if add.returncode != 0:
        print(add.stderr.strip())
        raise SystemExit(add.returncode)

    commit = run(
        "git",
        "commit",
        "-m",
        "Update Chronicle public status",
    )

    if commit.returncode != 0:
        print(commit.stdout.strip())
        print(commit.stderr.strip())
        raise SystemExit(commit.returncode)

    push = None

    for attempt, delay in enumerate((5, 15, 30), start=1):
        push = run("git", "push")

        if push.returncode == 0:
            break

        print("GIT PUSH FAILED", f"attempt {attempt}/3")
        print(push.stdout.strip())
        print(push.stderr.strip())

        if attempt < 3:
            print("retry in", delay, "seconds")
            time.sleep(delay)

    if push is None or push.returncode != 0:
        raise SystemExit(push.returncode if push else 1)

    print("PUBLIC STATUS PUBLISHED")


if __name__ == "__main__":
    main()
