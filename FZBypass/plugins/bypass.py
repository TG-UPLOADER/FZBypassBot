from time import time
from asyncio import create_task, gather, sleep as asleep
from pyrogram.filters import command, user
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from pyrogram.enums import MessageEntityType
from pyrogram.errors import QueryIdInvalid

from FZBypass import Config, Bypass, BOT_START
from FZBypass.core.bypass_checker import direct_link_checker, is_excep_link
from FZBypass.core.bypass_enhanced import batch_bypass, get_file_info
from FZBypass.core.bypass_indian import indian_shortener_bypass
from FZBypass.core.bot_utils import AuthChatsTopics, convert_time, BypassFilter


@Bypass.on_message(command("start"))
async def start_msg(client, message):
    await message.reply(
        f"""<b><i>FZ Bypass Bot!</i></b>
    
    <i>A Powerful Elegant Multi Threaded Bot written in Python... which can Bypass Various Shortener Links, Scrape links, and More ... </i>
    
    <i><b>Bot Started {convert_time(time() - BOT_START)} ago...</b></i>

🛃 <b>Use Me Here :</b> @CyberPunkGrp <i>(Bypass Topic)</i>""",
        quote=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🎓 Dev", url="https://t.me/SilentDemonSD"),
                    InlineKeyboardButton(
                        "🔍 Deploy Own",
                        url="https://github.com/SilentDemonSD/FZBypassBot",
                    ),
                ]
            ]
        ),
    )


@Bypass.on_message(BypassFilter & (user(Config.OWNER_ID) | AuthChatsTopics))
async def bypass_check(client, message):
    uid = message.from_user.id
    if (reply_to := message.reply_to_message) and (
        reply_to.text is not None or reply_to.caption is not None
    ):
        txt = reply_to.text or reply_to.caption
        entities = reply_to.entities or reply_to.caption_entities
    elif Config.AUTO_BYPASS or len(message.text.split()) > 1:
        txt = message.text
        entities = message.entities
    else:
        return await message.reply("<i>No Link Provided!</i>")

    wait_msg = await message.reply("<i>Bypassing...</i>")
    start = time()

    link, tlinks, no = "", [], 0
    
    # Extract all links first
    for enty in entities:
        if enty.type == MessageEntityType.URL:
            link = txt[enty.offset : (enty.offset + enty.length)]
        elif enty.type == MessageEntityType.TEXT_LINK:
            link = enty.url

        if link:
            no += 1
            tlinks.append(link)
            link = ""

    # Use enhanced batch processing
    if len(tlinks) > 1:
        await wait_msg.edit(f"<i>Processing {len(tlinks)} links...</i>")
        # Try Indian shortener bypass first for batch processing
        completed_tasks = []
        for link in tlinks:
            try:
                result = await indian_shortener_bypass(link)
                completed_tasks.append(result)
            except:
                try:
                    result = await direct_link_checker(link)
                    completed_tasks.append(result)
                except Exception as e:
                    completed_tasks.append(e)
    else:
        if tlinks:
            try:
                result = await indian_shortener_bypass(tlinks[0])
                completed_tasks = [result]
            except:
                completed_tasks = [await direct_link_checker(tlinks[0])]
        else:
            completed_tasks = []

    parse_data = []
    for result, link in zip(completed_tasks, tlinks):
        if isinstance(result, Exception):
            bp_link = f"\n┖ <b>Bypass Error:</b> {result}"
        elif is_excep_link(link):
            bp_link = result
        elif isinstance(result, list):
            bp_link, ui = "", "┖"
            for ind, lplink in reversed(list(enumerate(result, start=1))):
                bp_link = f"\n{ui} <b>{ind}x Bypass Link:</b> {lplink}" + bp_link
                ui = "┠"
        else:
            bp_link = f"\n┖ <b>Bypass Link:</b> {result}"

        if is_excep_link(link):
            parse_data.append(f"{bp_link}\n\n━━━━━━━✦✗✦━━━━━━━\n\n")
        else:
            parse_data.append(
                f"┎ <b>Source Link:</b> {link}{bp_link}\n\n━━━━━━━✦✗✦━━━━━━━\n\n"
            )

    end = time()

    if len(parse_data) != 0:
        parse_data[-1] = (
            parse_data[-1]
            + f"┎ <b>Total Links : {no}</b>\n┠ <b>Results In <code>{convert_time(end - start)}</code></b> !\n┖ <b>By </b>{message.from_user.mention} ( #ID{message.from_user.id} )"
        )
    tg_txt = "━━━━━━━✦✗✦━━━━━━━\n\n"
    for tg_data in parse_data:
        tg_txt += tg_data
        if len(tg_txt) > 4000:
            await wait_msg.edit(tg_txt, disable_web_page_preview=True)
            wait_msg = await message.reply(
                "<i>Fetching...</i>", reply_to_message_id=wait_msg.id
            )
            tg_txt = ""
            await asleep(2.5)

    if tg_txt != "":
        await wait_msg.edit(tg_txt, disable_web_page_preview=True)
    else:
        await wait_msg.delete()


@Bypass.on_message(command("log") & user(Config.OWNER_ID))
async def send_logs(client, message):
    await message.reply_document("log.txt", quote=True)


@Bypass.on_inline_query()
async def inline_query(client, query):
    answers = []
    string = query.query.lower()
    if string.startswith("!bp "):
        link = string.strip("!bp ")
        start = time()
        try:
            # Use enhanced bypass for inline queries
            try:
                bp_link = await indian_shortener_bypass(link)
            except:
                bp_link = await direct_link_checker(link, onlylink=True)
            end = time()

            if not is_excep_link(link):
                bp_link = (
                    f"┎ <b>Source Link:</b> {link}\n┃\n┖ <b>Bypass Link:</b> {bp_link}"
                )
            answers.append(
                InlineQueryResultArticle(
                    title="✅️ Bypass Link Success !",
                    input_message_content=InputTextMessageContent(
                        f"{bp_link}\n\n✎﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Took Only <code>{convert_time(end - start)}</code></b>",
                        disable_web_page_preview=True,
                    ),
                    description=f"Bypass via !bp {link}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Bypass Again",
                                    switch_inline_query_current_chat="!bp ",
                                )
                            ]
                        ]
                    ),
                )
            )
        except Exception as e:
            bp_link = f"<b>Bypass Error:</b> {e}"
            end = time()

            answers.append(
                InlineQueryResultArticle(
                    title="❌️ Bypass Link Error !",
                    input_message_content=InputTextMessageContent(
                        f"┎ <b>Source Link:</b> {link}\n┃\n┖ {bp_link}\n\n✎﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Took Only <code>{convert_time(end - start)}</code></b>",
                        disable_web_page_preview=True,
                    ),
                    description=f"Bypass via !bp {link}",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Bypass Again",
                                    switch_inline_query_current_chat="!bp ",
                                )
                            ]
                        ]
                    ),
                )
            )

    else:
        answers.append(
            InlineQueryResultArticle(
                title="♻️ Bypass Usage: In Line",
                input_message_content=InputTextMessageContent(
                    """<b><i>FZ Bypass Bot!</i></b>
    
    <i>A Powerful Elegant Multi Threaded Bot written in Python... which can Bypass Various Shortener Links, Scrape links, and More ... </i>
    
🎛 <b>Inline Use :</b> !bp [Single Link]""",
                ),
                description="Bypass via !bp [link]",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "FZ Channel", url="https://t.me/FXTorrentz"
                            ),
                            InlineKeyboardButton(
                                "Try Bypass", switch_inline_query_current_chat="!bp "
                            ),
                        ]
                    ]
                ),
            )
        )
    try:
        await query.answer(results=answers, cache_time=0)
    except QueryIdInvalid:
        pass
