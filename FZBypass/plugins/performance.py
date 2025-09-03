"""
Performance monitoring commands
"""
from pyrogram.filters import command, user
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from FZBypass import Config, Bypass
from FZBypass.core.performance import perf_monitor, rate_limiter


@Bypass.on_message(command("perf") & user(Config.OWNER_ID))
async def performance_stats(client, message):
    """Display performance statistics"""
    overall_stats = perf_monitor.get_overall_stats()
    
    perf_text = f"""
<b>📊 Performance Statistics</b>

<b>🌐 Overall Performance:</b>
┠ <b>Average Time:</b> <code>{overall_stats['avg_time']}s</code>
┠ <b>Success Rate:</b> <code>{overall_stats['success_rate']}%</code>
┠ <b>Total Attempts:</b> <code>{overall_stats['total_attempts']}</code>
┗ <b>Domains Supported:</b> <code>{overall_stats['domains_supported']}</code>

<b>🔝 Top Performing Domains:</b>
"""
    
    # Get top 5 domains by success rate
    domain_stats = []
    for domain in perf_monitor.stats:
        stats = perf_monitor.get_domain_stats(domain)
        if stats['total_attempts'] >= 3:  # Only show domains with enough data
            domain_stats.append((domain, stats))
    
    # Sort by success rate
    domain_stats.sort(key=lambda x: x[1]['success_rate'], reverse=True)
    
    for i, (domain, stats) in enumerate(domain_stats[:5], 1):
        perf_text += f"\n{i}. <code>{domain}</code> - {stats['success_rate']}% ({stats['avg_time']}s avg)"
    
    await message.reply(
        perf_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_perf")]
        ])
    )


@Bypass.on_message(command("limits") & user(Config.OWNER_ID))
async def rate_limits(client, message):
    """Display current rate limiting status"""
    limits_text = """
<b>⚡ Rate Limiting Status</b>

<b>🔧 Current Settings:</b>
┠ <b>Max Requests:</b> <code>10 per minute</code>
┠ <b>Time Window:</b> <code>60 seconds</code>
┗ <b>Concurrent Limit:</b> <code>5 requests</code>

<b>📈 Active Limits:</b>
"""
    
    active_users = len(rate_limiter.requests)
    limits_text += f"┗ <b>Active Users:</b> <code>{active_users}</code>"
    
    await message.reply(limits_text)