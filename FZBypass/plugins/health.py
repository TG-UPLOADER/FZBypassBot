"""
Health monitoring commands
"""
from pyrogram.filters import command, user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from FZBypass import Config, Bypass
from FZBypass.core.health import health_checker
from FZBypass.core.performance import perf_monitor


@Bypass.on_message(command("health") & user(Config.OWNER_ID))
async def health_command(client, message):
    """Display comprehensive health status"""
    health_msg = await message.reply("<i>🔍 Performing health check...</i>")
    
    # Perform full health check
    health_data = await health_checker.full_health_check()
    overall_status = health_checker.get_status_summary()
    
    # Format health report
    status_emoji = {
        'healthy': '✅',
        'warning': '⚠️',
        'unhealthy': '❌',
        'unknown': '❓'
    }
    
    health_text = f"""
<b>🏥 System Health Report</b>
<b>Overall Status:</b> {status_emoji.get(overall_status, '❓')} <code>{overall_status.upper()}</code>

<b>💾 System Resources:</b>
"""
    
    if 'memory_usage' in health_data:
        mem = health_data['memory_usage']
        health_text += f"┠ <b>Memory:</b> <code>{mem['value']}</code>\n"
    
    if 'cpu_usage' in health_data:
        cpu = health_data['cpu_usage']
        health_text += f"┠ <b>CPU:</b> <code>{cpu['value']}</code>\n"
    
    # Configuration status
    config_check = health_data.get('config', {})
    config_status = status_emoji.get(config_check.get('status'), '❓')
    health_text += f"\n<b>⚙️ Configuration:</b> {config_status}\n"
    
    if 'optional_configured' in config_check:
        health_text += f"┠ <b>Optional Configs:</b> <code>{config_check['optional_configured']}</code>\n"
    
    if 'missing_required' in config_check:
        health_text += f"┗ <b>Missing:</b> <code>{', '.join(config_check['missing_required'])}</code>\n"
    
    # Bypass functionality
    bypass_check = health_data.get('bypass', {})
    bypass_status = status_emoji.get(bypass_check.get('status'), '❓')
    health_text += f"\n<b>🔗 Bypass System:</b> {bypass_status}\n"
    
    if 'success_rate' in bypass_check:
        health_text += f"┠ <b>Test Success Rate:</b> <code>{bypass_check['success_rate']}</code>\n"
    
    if 'working_bypasses' in bypass_check:
        health_text += f"┗ <b>Working Tests:</b> <code>{bypass_check['working_bypasses']}</code>\n"
    
    await health_msg.edit(
        health_text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_health"),
                InlineKeyboardButton("📊 Performance", callback_data="show_perf")
            ]
        ])
    )


@Bypass.on_callback_query()
async def health_callbacks(client, callback_query):
    """Handle health monitoring callbacks"""
    data = callback_query.data
    
    if data == "refresh_health":
        await callback_query.answer("🔄 Refreshing health status...")
        # Trigger health command
        await health_command(client, callback_query.message)
    
    elif data == "show_perf":
        overall_stats = perf_monitor.get_overall_stats()
        
        perf_text = f"""
<b>📊 Performance Overview</b>

<b>🌐 Overall Metrics:</b>
┠ <b>Average Time:</b> <code>{overall_stats['avg_time']}s</code>
┠ <b>Success Rate:</b> <code>{overall_stats['success_rate']}%</code>
┠ <b>Total Attempts:</b> <code>{overall_stats['total_attempts']}</code>
┗ <b>Domains:</b> <code>{overall_stats['domains_supported']}</code>

<i>Use /perf for detailed statistics</i>
"""
        
        await callback_query.edit_message_text(
            perf_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Health", callback_data="refresh_health")]
            ])
        )
    
    await callback_query.answer()