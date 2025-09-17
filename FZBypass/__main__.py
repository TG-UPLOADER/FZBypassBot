import asyncio
import logging
import os
from sys import executable

from FZBypass import Bypass, LOGGER, Config
from pyrogram import idle
from pyrogram.filters import command, user

# --- Optional tiny HTTP server for Render Web Service ---
# Comment out if you're running as a Background Worker
try:
    from flask import Flask
    from threading import Thread

    app = Flask(__name__)

    @app.route("/")
    def index():
        return "FZBypass Bot Running"

    def run_web():
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)

    Thread(target=run_web, daemon=True).start()
    LOGGER.info("Keep-alive HTTP server started.")
except Exception as e:
    LOGGER.warning("Flask keep-alive server not started: %s", e)


# --- Restart command handler ---
@Bypass.on_message(command("restart") & user(Config.OWNER_ID))
async def restart_handler(client, message):
    """Owner-only /restart command."""
    restart_msg = await message.reply("<i>Restarting...</i>")
    # Run update script first
    proc = await asyncio.create_subprocess_exec("python3", "update.py")
    await proc.wait()

    # Save message info for after restart
    with open(".restartmsg", "w") as f:
        f.write(f"{restart_msg.chat.id}\n{restart_msg.id}\n")

    # Replace current process with a fresh one
    try:
        os.execl(executable, executable, "-m", "FZBypass")
    except Exception:
        os.execl(executable, executable, "-m", "FZBypassBot.FZBypass")


async def post_restart_message():
    """Send 'Restarted!' message after process restart."""
    if not os.path.isfile(".restartmsg"):
        return

    try:
        with open(".restartmsg") as f:
            lines = f.read().splitlines()
            chat_id, msg_id = map(int, lines)
        os.remove(".restartmsg")
        await Bypass.edit_message_text(
            chat_id=chat_id, message_id=msg_id, text="<i>Restarted ✅</i>"
        )
        LOGGER.info("Post-restart message sent.")
    except Exception as e:
        LOGGER.error("Failed to send post-restart message: %s", e)


def main():
    """Main entrypoint for bot."""
    try:
        Bypass.start()
        LOGGER.info("FZ Bot Started!")
        Bypass.loop.run_until_complete(post_restart_message())
        idle()
    except KeyboardInterrupt:
        LOGGER.info("Bot stopped by user.")
    except Exception as e:
        LOGGER.exception("Fatal error in main loop: %s", e)
    finally:
        Bypass.stop()


if __name__ == "__main__":
    main()
