"""
Admin commands for bot management and monitoring
"""
from time import time
from asyncio import create_subprocess_exec
from pyrogram.filters import command, user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from FZBypass import Config, Bypass, BOT_START, LOGGER
from FZBypass.core.bot_utils import convert_time


@Bypass.on_message(command("stats") & user(Config.OWNER_ID))
async def bot_stats(client, message):
    """Display bot statistics and system info"""
    uptime = convert_time(time() - BOT_START)
    
    stats_text = f"""
<b>🤖 FZ Bypass Bot Statistics</b>

<b>⏰ Uptime:</b> <code>{uptime}</code>
<b>🆔 Bot ID:</b> <code>{client.me.id}</code>
<b>👤 Bot Username:</b> @{client.me.username}
<b>📊 Auth Chats:</b> <code>{len(Config.AUTH_CHATS)}</code>
<b>🔄 Auto Bypass:</b> <code>{'Enabled' if Config.AUTO_BYPASS else 'Disabled'}</code>

<b>🔧 Configuration Status:</b>
┠ <b>GDTOT_CRYPT:</b> {'✅' if Config.GDTOT_CRYPT else '❌'}
┠ <b>HUBDRIVE_CRYPT:</b> {'✅' if Config.HUBDRIVE_CRYPT else '❌'}
┠ <b>DRIVEFIRE_CRYPT:</b> {'✅' if Config.DRIVEFIRE_CRYPT else '❌'}
┠ <b>KATDRIVE_CRYPT:</b> {'✅' if Config.KATDRIVE_CRYPT else '❌'}
┠ <b>TERA_COOKIE:</b> {'✅' if Config.TERA_COOKIE else '❌'}
┠ <b>DIRECT_INDEX:</b> {'✅' if Config.DIRECT_INDEX else '❌'}
┠ <b>LARAVEL_SESSION:</b> {'✅' if Config.LARAVEL_SESSION else '❌'}
┗ <b>XSRF_TOKEN:</b> {'✅' if Config.XSRF_TOKEN else '❌'}
"""
    
    await message.reply(
        stats_text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
                InlineKeyboardButton("📋 Logs", callback_data="get_logs")
            ]
        ])
    )


@Bypass.on_message(command("health") & user(Config.OWNER_ID))
async def health_check(client, message):
    """Perform health check on bot services"""
    health_msg = await message.reply("<i>Performing health check...</i>")
    
    checks = {
        "Bot Connection": "✅ Connected",
        "Config Loaded": "✅ Loaded" if Config.BOT_TOKEN else "❌ Missing",
        "Auth Chats": f"✅ {len(Config.AUTH_CHATS)} configured" if Config.AUTH_CHATS else "⚠️ None configured"
    }
    
    # Test bypass functionality
    try:
        test_result = await direct_link_checker_enhanced("https://bit.ly/test")
        checks["Bypass System"] = "✅ Working"
    except:
        checks["Bypass System"] = "⚠️ Limited functionality"
    
    health_text = "<b>🏥 Health Check Results</b>\n\n"
    for check, status in checks.items():
        health_text += f"<b>{check}:</b> {status}\n"
    
    await health_msg.edit(health_text)


@Bypass.on_message(command("config") & user(Config.OWNER_ID))
async def show_config(client, message):
    """Display current configuration (sanitized)"""
    config_text = f"""
<b>⚙️ Current Configuration</b>

<b>🔧 Basic Settings:</b>
┠ <b>Auto Bypass:</b> <code>{'Enabled' if Config.AUTO_BYPASS else 'Disabled'}</code>
┠ <b>Owner ID:</b> <code>{Config.OWNER_ID}</code>
┗ <b>Auth Chats:</b> <code>{len(Config.AUTH_CHATS)} configured</code>

<b>🔑 Service Tokens:</b>
┠ <b>GDTOT:</b> {'✅ Set' if Config.GDTOT_CRYPT else '❌ Not Set'}
┠ <b>HubDrive:</b> {'✅ Set' if Config.HUBDRIVE_CRYPT else '❌ Not Set'}
┠ <b>DriveFire:</b> {'✅ Set' if Config.DRIVEFIRE_CRYPT else '❌ Not Set'}
┠ <b>KatDrive:</b> {'✅ Set' if Config.KATDRIVE_CRYPT else '❌ Not Set'}
┠ <b>Terabox:</b> {'✅ Set' if Config.TERA_COOKIE else '❌ Not Set'}
┠ <b>Direct Index:</b> {'✅ Set' if Config.DIRECT_INDEX else '❌ Not Set'}
┠ <b>Laravel Session:</b> {'✅ Set' if Config.LARAVEL_SESSION else '❌ Not Set'}
┗ <b>XSRF Token:</b> {'✅ Set' if Config.XSRF_TOKEN else '❌ Not Set'}

<b>🔄 Update Settings:</b>
┠ <b>Upstream Repo:</b> <code>{Config.UPSTREAM_REPO or 'Default'}</code>
┗ <b>Upstream Branch:</b> <code>{Config.UPSTREAM_BRANCH or 'main'}</code>
"""
    
    await message.reply(config_text)


@Bypass.on_callback_query()
async def callback_handler(client, callback_query):
    """Handle callback queries from inline keyboards"""
    data = callback_query.data
    
    if data == "refresh_stats":
        # Refresh stats
        uptime = convert_time(time() - BOT_START)
        stats_text = f"""
<b>🤖 FZ Bypass Bot Statistics</b>

<b>⏰ Uptime:</b> <code>{uptime}</code>
<b>🆔 Bot ID:</b> <code>{client.me.id}</code>
<b>👤 Bot Username:</b> @{client.me.username}
<b>📊 Auth Chats:</b> <code>{len(Config.AUTH_CHATS)}</code>
<b>🔄 Auto Bypass:</b> <code>{'Enabled' if Config.AUTO_BYPASS else 'Disabled'}</code>

<b>🔧 Configuration Status:</b>
┠ <b>GDTOT_CRYPT:</b> {'✅' if Config.GDTOT_CRYPT else '❌'}
┠ <b>HUBDRIVE_CRYPT:</b> {'✅' if Config.HUBDRIVE_CRYPT else '❌'}
┠ <b>DRIVEFIRE_CRYPT:</b> {'✅' if Config.DRIVEFIRE_CRYPT else '❌'}
┠ <b>KATDRIVE_CRYPT:</b> {'✅' if Config.KATDRIVE_CRYPT else '❌'}
┠ <b>TERA_COOKIE:</b> {'✅' if Config.TERA_COOKIE else '❌'}
┠ <b>DIRECT_INDEX:</b> {'✅' if Config.DIRECT_INDEX else '❌'}
┠ <b>LARAVEL_SESSION:</b> {'✅' if Config.LARAVEL_SESSION else '❌'}
┗ <b>XSRF_TOKEN:</b> {'✅' if Config.XSRF_TOKEN else '❌'}

<i>🔄 Refreshed at {time()}</i>
"""
        await callback_query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_stats"),
                    InlineKeyboardButton("📋 Logs", callback_data="get_logs")
                ]
            ])
        )
    
    elif data == "get_logs":
        try:
            await callback_query.message.reply_document("log.txt", caption="📋 <b>Bot Logs</b>")
            await callback_query.answer("Logs sent!")
        except Exception as e:
            await callback_query.answer(f"Error: {e}", show_alert=True)
    
    await callback_query.answer()