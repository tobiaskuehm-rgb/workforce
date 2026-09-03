"""python -m workforce <command> --config <file>

run            poll forever
once           one poll round (cron-friendly, and what the tests use)
status         channel, budget today, pending outbound, audit chain
channel on|off the kill switch
verify         audit chain and delivery reconciliation; exit 1 on any finding
backup <path>  consistent copy of the state file, mode 600
identify       list the chat ids that have written to the bot (bootstrap: find allowed_chat_id)
"""

from __future__ import annotations

import argparse
import sys

from . import config as config_module
from .app import App, build_app
from .providers import ProviderError
from .store import Store


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="workforce")
    parser.add_argument("command", choices=["run", "once", "status", "channel", "verify", "backup", "identify"])
    parser.add_argument("argument", nargs="?")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args(argv)
    try:
        cfg = config_module.load(args.config)
    except config_module.ConfigError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.command == "identify":
        # Only the token is read; nothing is processed or answered. Prints chat ids, never text.
        from .config import read_secret
        from .telegram import TelegramClient
        from .telegram import TelegramError
        try:
            client = TelegramClient(read_secret(cfg.secrets_dir, "telegram_bot_token"), base_url=cfg.telegram_base_url)
            updates = client.get_updates(0, 1)
        except (config_module.ConfigError, TelegramError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 2
        seen = {}
        for update in updates:
            chat = (update.get("message") or {}).get("chat") or {}
            if "id" in chat:
                seen[int(chat["id"])] = str(chat.get("type", "?"))
        for chat_id, kind in seen.items():
            print(f"chat_id={chat_id} typ={kind}")
        print("keine Nachricht beim Bot - erst dem Bot schreiben" if not seen else f"{len(seen)} Chat(s)")
        return 0

    if args.command in ("status", "channel", "verify", "backup"):
        store = Store(cfg.db_path)
        if args.command == "channel":
            if args.argument not in ("on", "off"):
                print("FAIL: channel on|off", file=sys.stderr)
                return 2
            store.set_channel("ACTIVE" if args.argument == "on" else "DISABLED", actor="cli", request_id="CLI-CHANNEL")
            print(f"Kanal: {store.channel()}")
            return 0
        if args.command == "backup":
            if not args.argument:
                print("FAIL: backup <pfad>", file=sys.stderr)
                return 2
            store.backup(args.argument)
            print(f"Sicherung: {args.argument}")
            return 0
        ok, bad = store.verify_audit()
        problems = store.reconcile_deliveries()
        if args.command == "status":
            print(App(cfg, store, None, {}).status_text())
            return 0
        print("Audit: " + ("intakt" if ok else f"BESCHAEDIGT ab Zeile {bad}"))
        for p in problems:
            print("Zustellabgleich: " + p)
        print("RESULT: " + ("PASS" if ok and not problems else "FAIL"))
        return 0 if ok and not problems else 1

    try:
        app = build_app(cfg)
    except (config_module.ConfigError, ProviderError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    if args.command == "once":
        print(f"Updates: {app.poll_once()}")
        return 0
    app.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
