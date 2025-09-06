from re import match
from urllib.parse import urlparse

from FZBypass.core.bypass_dlinks import *
from FZBypass.core.bypass_ddl import *
from FZBypass.core.bypass_scrape import *
from FZBypass.core.bypass_enhanced import *
from FZBypass.core.bypass_indian import *
from FZBypass.core.bot_utils import get_dl
from FZBypass.core.exceptions import DDLException

fmed_list = [
    "fembed.net",
    "fembed.com",
    "femax20.com",
    "fcdn.stream",
    "feurl.com",
    "layarkacaxxi.icu",
    "naniplay.nanime.in",
    "naniplay.nanime.biz",
    "naniplay.com",
    "mm9842.com",
]


def is_share_link(url):
    return bool(
        match(
            r"https?:\/\/.+\.(gdtot|filepress|pressbee|gdflix)\.\S+|https?:\/\/(gdflix|filepress|pressbee|onlystream|filebee|appdrive)\.\S+",
            url,
        )
    )


def is_excep_link(url):
    return bool(
        match(
            r"https?:\/\/.+\.(1tamilmv|gdtot|filepress|pressbee|gdflix|sharespark)\.\S+|https?:\/\/(sharer|onlystream|hubdrive|katdrive|drivefire|skymovieshd|toonworld4all|kayoanime|cinevood|gdflix|filepress|pressbee|filebee|appdrive)\.\S+",
            url,
        )
    )


async def direct_link_checker(link, onlylink=False):
    """Enhanced direct link checker with improved error handling and performance"""
    try:
        # First try Indian shortener bypass
        result = await indian_shortener_bypass(link)
        if result and await validate_bypass_result(link, result):
            if onlylink:
                return result
            return await smart_loop_bypass(link)
    except DDLException:
        # Continue to other bypass methods if Indian shortener fails
        pass
    
    try:
        # First try the enhanced bypass system
        result = await direct_link_checker_enhanced(link)
        if result and await validate_bypass_result(link, result):
            if onlylink:
                return result
            return await smart_loop_bypass(link)
    except DDLException:
        # Fall back to original system if enhanced fails
        pass
    
    # Original bypass logic as fallback
    domain = urlparse(link).hostname

    # File Hoster Links
    if bool(match(r"https?:\/\/(yadi|disk.yandex)\.\S+", link)):
        return await yandex_disk(link)
    elif bool(match(r"https?:\/\/.+\.mediafire\.\S+", link)):
        return await mediafire(link)
    elif bool(match(r"https?:\/\/shrdsk\.\S+", link)):
        return await shrdsk(link)
    elif any(
        x in domain
        for x in [
            "1024tera",
            "terabox",
            "nephobox",
            "4funbox",
            "mirrobox",
            "momerybox",
            "teraboxapp",
        ]
    ):
        return await terabox(link)
    elif "drive.google.com" in link:
        return get_dl(link, True)

    # DDL Links
    elif bool(match(r"https?:\/\/try2link\.\S+", link)):
        blink = await try2link(link)
    elif bool(match(r"https?:\/\/(gyanilinks|gtlinks)\.\S+", link)):
        blink = await gyanilinks(link)
    
    # Try Indian shortener bypass as fallback
    try:
        blink = await indian_shortener_bypass(link)
    except DDLException:
        pass
    
    elif bool(match(r"https?:\/\/ouo\.\S+", link)):
        blink = await ouo(link)
    elif bool(match(r"https?:\/\/(shareus|shrs)\.\S+", link)):
        blink = await shareus(link)
    elif bool(match(r"https?:\/\/(.+\.)?dropbox\.\S+", link)):
        blink = await dropbox(link)
    elif bool(match(r"https?:\/\/linkvertise\.\S+", link)):
        blink = await linkvertise(link)
    elif bool(match(r"https?:\/\/rslinks\.\S+", link)):
        blink = await rslinks(link)
    elif bool(match(r"https?:\/\/(bit|tinyurl|(.+\.)short|shorturl|t)\.\S+", link)):
        blink = await shorter(link)
    elif bool(match(r"https?:\/\/appurl\.\S+", link)):
        blink = await appurl(link)
    elif bool(match(r"https?:\/\/surl\.\S+", link)):
        blink = await surl(link)
    elif bool(match(r"https?:\/\/thinfi\.\S+", link)):
        blink = await thinfi(link)
    elif bool(match(r"https?:\/\/justpaste\.\S+", link)):
        blink = await justpaste(link)
    elif bool(match(r"https?:\/\/linksxyz\.\S+", link)):
        blink = await linksxyz(link)

    # DL Sites
    elif bool(match(r"https?:\/\/cinevood\.\S+", link)):
        return await cinevood(link)
    elif bool(match(r"https?:\/\/kayoanime\.\S+", link)):
        return await kayoanime(link)
    elif bool(match(r"https?:\/\/toonworld4all\.\S+", link)):
        return await toonworld4all(link)
    elif bool(match(r"https?:\/\/skymovieshd\.\S+", link)):
        return await skymovieshd(link)
    elif bool(match(r"https?:\/\/.+\.sharespark\.\S+", link)):
        return await sharespark(link)
    elif bool(match(r"https?:\/\/.+\.1tamilmv\.\S+", link)):
        return await tamilmv(link)

    # DL Links
    elif bool(match(r"https?:\/\/hubdrive\.\S+", link)):
        return await drivescript(link, Config.HUBDRIVE_CRYPT, "HubDrive")
    elif bool(match(r"https?:\/\/katdrive\.\S+", link)):
        return await drivescript(link, Config.KATDRIVE_CRYPT, "KatDrive")
    elif bool(match(r"https?:\/\/drivefire\.\S+", link)):
        return await drivescript(link, Config.DRIVEFIRE_CRYPT, "DriveFire")
    elif bool(match(r"https?:\/\/sharer\.\S+", link)):
        return await sharerpw(link)
    elif is_share_link(link):
        if "gdtot" in domain:
            return await gdtot(link)
        elif "filepress" in domain or "pressbee" in domain:
            return await filepress(link)
        elif "appdrive" in domain or "gdflix" in domain:
            return await appflix(link)
        else:
            return await sharer_scraper(link)

    # Exceptions
    elif bool(match(r"https?:\/\/.+\.technicalatg\.\S+", link)):
        raise DDLException("Bypass Not Allowed !")
    else:
        raise DDLException(
            f"<i>No Bypass Function Found for your Link :</i> <code>{link}</code>"
        )

    if onlylink:
        return blink

    links = []
    while True:
        try:
            links.append(blink)
            blink = await direct_link_checker(blink, onlylink=True)
            if is_excep_link(links[-1]):
                links.append("\n\n" + blink)
                break
        except Exception:
            break
    return links
