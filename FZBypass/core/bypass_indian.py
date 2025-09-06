"""
Universal Indian Shortener Bypass Functions
Comprehensive collection of Indian shortener bypass methods
"""
from asyncio import sleep as asleep, timeout, TimeoutError
from time import time, sleep
from re import findall, match, search, sub, DOTALL
from urllib.parse import urlparse, parse_qs, quote, unquote
from uuid import uuid4
from base64 import b64decode, b64encode
from json import loads, dumps
from random import choice, randint

from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from aiohttp import ClientSession, ClientTimeout
from requests import Session, get as rget, post as rpost

from FZBypass import Config, LOGGER
from FZBypass.core.exceptions import DDLException
from FZBypass.core.recaptcha import recaptchaV3


class IndianBypassSession:
    """Enhanced session for Indian shorteners with specific headers and handling"""
    
    def __init__(self):
        self.timeout = ClientTimeout(total=45)
        self.user_agents = [
            'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.headers = {
            'User-Agent': choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def get_with_retry(self, url, retries=3, **kwargs):
        """Get request with retry mechanism for Indian sites"""
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.get(url, **kwargs) as response:
                        return await response.text(), response.cookies, response.status, response.headers
            except Exception as e:
                if attempt == retries - 1:
                    raise DDLException(f"Failed after {retries} attempts: {str(e)}")
                await asleep(2)
    
    async def post_with_retry(self, url, data=None, json=None, retries=3, **kwargs):
        """Post request with retry mechanism"""
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.post(url, data=data, json=json, **kwargs) as response:
                        return await response.text(), response.cookies, response.status, response.headers
            except Exception as e:
                if attempt == retries - 1:
                    raise DDLException(f"Failed after {retries} attempts: {str(e)}")
                await asleep(2)


# Universal Indian Shortener Bypass Functions

async def indian_transcript_v1(url: str, domain: str, referer: str, sleep_time: float) -> str:
    """Standard Indian shortener bypass method"""
    session = IndianBypassSession()
    code = url.rstrip("/").split("/")[-1]
    
    try:
        # Get initial page
        html, cookies, status, headers = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': referer}
        )
        
        if status != 200:
            raise DDLException(f"HTTP {status} error")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for Cloudflare or other protections
        title = soup.find('title')
        if title and any(x in title.text.lower() for x in ['just a moment', 'checking', 'please wait']):
            raise DDLException("Site protection detected")
        
        # Extract form data
        form_data = {}
        for inp in soup.find_all('input'):
            name = inp.get('name')
            value = inp.get('value')
            if name and value:
                form_data[name] = value
        
        # Look for hidden tokens
        for script in soup.find_all('script'):
            if script.string:
                # Extract common token patterns
                token_patterns = [
                    r'_token["\']?\s*[:=]\s*["\']([^"\']+)',
                    r'csrf[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)',
                    r'authenticity[_-]?token["\']?\s*[:=]\s*["\']([^"\']+)'
                ]
                for pattern in token_patterns:
                    if match := search(pattern, script.string, DOTALL):
                        form_data['_token'] = match.group(1)
                        break
        
        if not form_data:
            raise DDLException("No form data found")
        
        # Wait before submitting
        await asleep(sleep_time)
        
        # Submit form
        submit_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{domain}/{code}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response_text, _, status, _ = await session.post_with_retry(
            f"{domain}/links/go",
            data=form_data,
            headers=submit_headers,
            cookies=cookies
        )
        
        if status != 200:
            raise DDLException(f"Form submission failed with HTTP {status}")
        
        try:
            result = loads(response_text)
            if 'url' in result:
                return result['url']
            elif 'link' in result:
                return result['link']
            elif 'destination' in result:
                return result['destination']
            else:
                raise DDLException("No URL in response")
        except Exception:
            # Try to extract URL from HTML response
            soup = BeautifulSoup(response_text, 'html.parser')
            for link in soup.find_all('a', href=True):
                if 'http' in link['href'] and link['href'] != url:
                    return link['href']
            raise DDLException("Invalid response format")
            
    except TimeoutError:
        raise DDLException("Request timeout")
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Bypass error: {str(e)}")


async def indian_transcript_v2(url: str, domain: str, referer: str, sleep_time: float, custom_data=None) -> str:
    """Advanced Indian shortener bypass with custom data handling"""
    session = IndianBypassSession()
    code = url.rstrip("/").split("/")[-1]
    
    try:
        # First request with specific referer
        html, cookies, status, headers = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': referer}
        )
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract all possible form data
        form_data = {}
        
        # Standard form inputs
        for inp in soup.find_all('input'):
            name = inp.get('name')
            value = inp.get('value')
            if name:
                form_data[name] = value or ''
        
        # Custom data if provided
        if custom_data:
            form_data.update(custom_data)
        
        # Extract JavaScript variables
        for script in soup.find_all('script'):
            if script.string:
                # Common patterns in Indian shorteners
                patterns = [
                    r'var\s+(\w+)\s*=\s*["\']([^"\']+)["\']',
                    r'let\s+(\w+)\s*=\s*["\']([^"\']+)["\']',
                    r'const\s+(\w+)\s*=\s*["\']([^"\']+)["\']'
                ]
                for pattern in patterns:
                    matches = findall(pattern, script.string)
                    for var_name, var_value in matches:
                        if any(x in var_name.lower() for x in ['token', 'key', 'id', 'code']):
                            form_data[var_name] = var_value
        
        # Wait with random variation
        wait_time = sleep_time + randint(1, 3)
        await asleep(wait_time)
        
        # Submit with enhanced headers
        submit_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{domain}/{code}",
            'Origin': domain,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        # Try multiple endpoints
        endpoints = ['/links/go', '/go', '/redirect', '/link', '/short']
        
        for endpoint in endpoints:
            try:
                response_text, _, status, _ = await session.post_with_retry(
                    f"{domain}{endpoint}",
                    data=form_data,
                    headers=submit_headers,
                    cookies=cookies
                )
                
                if status == 200:
                    # Try JSON parsing
                    try:
                        result = loads(response_text)
                        if 'url' in result and result['url']:
                            return result['url']
                        elif 'link' in result and result['link']:
                            return result['link']
                    except:
                        pass
                    
                    # Try HTML parsing
                    soup = BeautifulSoup(response_text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http') and href != url:
                            return href
                    
                    # Check for redirect in response
                    if 'location' in response_text.lower():
                        location_match = search(r'location["\']?\s*[:=]\s*["\']([^"\']+)', response_text, DOTALL)
                        if location_match:
                            return location_match.group(1)
                            
            except Exception:
                continue
        
        raise DDLException("All endpoints failed")
        
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Advanced bypass error: {str(e)}")


async def indian_transcript_v3(url: str, domain: str, referer: str, sleep_time: float) -> str:
    """Multi-step Indian shortener bypass"""
    session = IndianBypassSession()
    code = url.rstrip("/").split("/")[-1]
    
    try:
        # Step 1: Initial page load
        html, cookies, status, headers = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': referer}
        )
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Step 2: Look for intermediate steps
        intermediate_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(x in href for x in ['/verify', '/check', '/validate', '/continue']):
                intermediate_links.append(href)
        
        current_url = f"{domain}/{code}"
        current_cookies = cookies
        
        # Process intermediate steps
        for step, link in enumerate(intermediate_links[:3]):  # Max 3 steps
            if not link.startswith('http'):
                link = domain + link
            
            await asleep(2)  # Wait between steps
            
            html, current_cookies, status, headers = await session.get_with_retry(
                link,
                headers={'Referer': current_url},
                cookies=current_cookies
            )
            
            current_url = link
            soup = BeautifulSoup(html, 'html.parser')
        
        # Step 3: Final form submission
        form_data = {}
        for inp in soup.find_all('input'):
            name = inp.get('name')
            value = inp.get('value')
            if name:
                form_data[name] = value or ''
        
        # Add common required fields
        form_data.update({
            'action': 'verify',
            'step': 'final',
            'verified': '1'
        })
        
        await asleep(sleep_time)
        
        response_text, _, status, _ = await session.post_with_retry(
            f"{domain}/links/go",
            data=form_data,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': current_url
            },
            cookies=current_cookies
        )
        
        # Parse final response
        try:
            result = loads(response_text)
            return result.get('url') or result.get('link') or result.get('destination')
        except:
            soup = BeautifulSoup(response_text, 'html.parser')
            for link in soup.find_all('a', href=True):
                if link['href'].startswith('http') and link['href'] != url:
                    return link['href']
        
        raise DDLException("Multi-step bypass failed")
        
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Multi-step error: {str(e)}")


# Specific Indian Shortener Functions

async def adrinolinks_bypass(url: str) -> str:
    """Enhanced Adrinolinks bypass"""
    return await indian_transcript_v1(
        url, "https://adrinolinks.in", "https://bhojpuritop.in/", 8
    )


async def adsfly_bypass(url: str) -> str:
    """Enhanced Adsfly bypass"""
    return await indian_transcript_v1(
        url, "https://go.adsfly.in/", "https://letest25.co/", 3
    )


async def anlinks_bypass(url: str) -> str:
    """Enhanced Anlinks bypass"""
    return await indian_transcript_v2(
        url, "https://anlinks.in/", "https://dsblogs.fun/", 8
    )


async def bindaaslinks_bypass(url: str) -> str:
    """Bindaaslinks bypass"""
    return await indian_transcript_v1(
        url, "https://appsinsta.com/blog", "https://pracagov.com/", 3
    )


async def bringlifes_bypass(url: str) -> str:
    """Bringlifes bypass"""
    return await indian_transcript_v1(
        url, "https://bringlifes.com/", "https://loanoffering.in/", 5
    )


async def dalink_bypass(url: str) -> str:
    """Dalink bypass"""
    return await indian_transcript_v2(
        url, "https://get.tamilhit.tech/MR-X/tamil/", "https://www.tamilhit.tech/", 8
    )


async def droplink_bypass(url: str) -> str:
    """Droplink bypass"""
    return await indian_transcript_v1(
        url, "https://droplink.co/", "https://yoshare.net/", 3.1
    )


async def dtglinks_bypass(url: str) -> str:
    """DTGLinks bypass"""
    return await indian_transcript_v1(
        url, "https://happyfiles.dtglinks.in/", "https://tech.filohappy.in/", 5
    )


async def dulink_bypass(url: str) -> str:
    """DuLink bypass"""
    return await indian_transcript_v1(
        url, "https://du-link.in", "https://profitshort.com/", 0
    )


async def earn2me_bypass(url: str) -> str:
    """Earn2Me bypass"""
    return await indian_transcript_v1(
        url, "https://blog.filepresident.com/", "https://easyworldbusiness.com/", 5
    )


async def earn2short_bypass(url: str) -> str:
    """Earn2Short bypass"""
    return await indian_transcript_v1(
        url, "https://go.earn2short.in/", "https://tech.insuranceinfos.in/", 0.8
    )


async def earn4link_bypass(url: str) -> str:
    """Earn4Link bypass"""
    return await indian_transcript_v2(
        url, "https://m.open2get.in/", "https://ezeviral.com/", 8
    )


async def earnmoneykamalo_bypass(url: str) -> str:
    """Earn Money Kamalo bypass"""
    return await indian_transcript_v1(
        url, "https://go.moneykamalo.com/", "https://bloging.techkeshri.com/", 4
    )


async def easysky_bypass(url: str) -> str:
    """EasySky bypass"""
    return await indian_transcript_v2(
        url, "https://techy.veganab.co/", "https://camdigest.com/", 5
    )


async def evolinks_bypass(url: str) -> str:
    """Evolinks bypass"""
    return await indian_transcript_v1(
        url, "https://ads.evolinks.in/", url, 3
    )


async def ez4short_bypass(url: str) -> str:
    """EZ4Short bypass"""
    return await indian_transcript_v1(
        url, "https://ez4short.com/", "https://ez4mods.com/", 5
    )


async def gyanilinks_bypass(url: str) -> str:
    """Enhanced Gyanilinks bypass"""
    code = url.split('/')[-1]
    useragent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    domain = "https://go.bloggingaro.com"
    
    session = IndianBypassSession()
    
    try:
        # First request
        html, cookies, status, headers = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': 'https://tech.hipsonyc.com/', 'User-Agent': useragent}
        )
        
        # Second request
        html, cookies, status, headers = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': 'https://hipsonyc.com/', 'User-Agent': useragent},
            cookies=cookies
        )
        
        soup = BeautifulSoup(html, 'html.parser')
        data = {inp.get('name'): inp.get('value') for inp in soup.find_all('input')}
        
        await asleep(5)
        
        response_text, _, status, _ = await session.post_with_retry(
            f"{domain}/links/go",
            data=data,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': useragent,
                'Referer': f"{domain}/{code}"
            },
            cookies=cookies
        )
        
        if 'application/json' in headers.get('Content-Type', ''):
            result = loads(response_text)
            return result['url']
        
        raise DDLException("Invalid response format")
        
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Gyanilinks bypass failed: {str(e)}")


async def indianshortner_bypass(url: str) -> str:
    """Indian Shortner bypass"""
    return await indian_transcript_v1(
        url, "https://indianshortner.com/", "https://moddingzone.in/", 5
    )


async def indyshare_bypass(url: str) -> str:
    """IndyShare bypass"""
    return await indian_transcript_v1(
        url, "https://indyshare.net", "https://insurancewolrd.in/", 3.1
    )


async def instantearn_bypass(url: str) -> str:
    """InstantEarn bypass"""
    return await indian_transcript_v1(
        url, "https://get.instantearn.in/", "https://love.petrainer.in/", 5
    )


async def kpslink_bypass(url: str) -> str:
    """KPSLink bypass"""
    return await indian_transcript_v1(
        url, "https://kpslink.in/", "https://infotamizhan.xyz/", 3.1
    )


async def kpslink_v2_bypass(url: str) -> str:
    """KPSLink V2 bypass"""
    return await indian_transcript_v1(
        url, "https://v2.kpslink.in/", "https://infotamizhan.xyz/", 5
    )


async def krownlinks_bypass(url: str) -> str:
    """KrownLinks bypass"""
    return await indian_transcript_v1(
        url, "https://go.hostadviser.net/", "blog.hostadviser.net/", 8
    )


async def link4earn_bypass(url: str) -> str:
    """Link4Earn bypass"""
    return await indian_transcript_v1(
        url, "https://link4earn.com", "https://studyis.xyz/", 6
    )


async def linkfly_bypass(url: str) -> str:
    """LinkFly bypass"""
    return await indian_transcript_v2(
        url, "https://insurance.yosite.net/", "https://yosite.net/", 10
    )


async def linkjust_bypass(url: str) -> str:
    """LinkJust bypass"""
    return await indian_transcript_v1(
        url, "https://linkjust.com/", "https://forexrw7.com/", 3.1
    )


async def linkpays_bypass(url: str) -> str:
    """LinkPays bypass"""
    return await indian_transcript_v1(
        url, "https://tech.smallinfo.in/Gadget/", "https://finance.filmypoints.in/", 6
    )


async def links1_bypass(url: str) -> str:
    """Link1s bypass"""
    return await indian_transcript_v1(
        url, "https://link1s.com", "https://anhdep24.com/", 9
    )


async def linkshortx_bypass(url: str) -> str:
    """LinkShortX bypass"""
    return await indian_transcript_v1(
        url, "https://linkshortx.in/", "https://nanotech.org.in/", 4.9
    )


async def linksly_bypass(url: str) -> str:
    """LinksLy bypass"""
    return await indian_transcript_v1(
        url, "https://go.linksly.co/", "https://en.themezon.net/", 5
    )


async def linksxyz_bypass(url: str) -> str:
    """LinksXYZ bypass - Direct extraction method"""
    try:
        session = IndianBypassSession()
        html, _, _, _ = await session.get_with_retry(url)
        soup = BeautifulSoup(html, "html.parser")
        
        redirect_links = soup.select('div[id="redirect-info"] > a')
        if redirect_links:
            return redirect_links[0]["href"]
        
        raise DDLException("Redirect link not found")
        
    except Exception as e:
        raise DDLException(f"LinksXYZ bypass failed: {str(e)}")


async def linkyearn_bypass(url: str) -> str:
    """LinkYearn bypass"""
    return await indian_transcript_v1(
        url, "https://linkyearn.com", "https://gktech.uk/", 5
    )


async def mdisk_bypass(url: str) -> str:
    """MDisk bypass"""
    return await indian_transcript_v1(
        url, "https://mdisk.pro", "https://www.meclipstudy.in/", 5
    )


async def mdiskshortner_bypass(url: str) -> str:
    """MDisk Shortner bypass"""
    return await indian_transcript_v1(
        url, "https://mdiskshortner.link", "https://yosite.net/", 0
    )


async def modijiurl_bypass(url: str) -> str:
    """ModijiURL bypass"""
    return await indian_transcript_v1(
        url, "https://modijiurl.com/", "https://loanoffering.in/", 8
    )


async def moneycase_bypass(url: str) -> str:
    """MoneyCase bypass"""
    return await indian_transcript_v1(
        url, "https://last.moneycase.link/", "https://www.infokeeda.xyz/", 3.1
    )


async def mplaylink_bypass(url: str) -> str:
    """MPlayLink bypass"""
    return await indian_transcript_v1(
        url, "https://tera-box.cloud/", "https://mvplaylink.in.net/", 5
    )


async def narzolinks_bypass(url: str) -> str:
    """NarzoLinks bypass"""
    return await indian_transcript_v1(
        url, "https://go.narzolinks.click/", "https://hydtech.in/", 5
    )


async def omnifly_bypass(url: str) -> str:
    """OmniFly bypass"""
    return await indian_transcript_v1(
        url, "https://f.omnifly.in.net/", "https://ignitesmm.com/", 5
    )


async def onepagelink_bypass(url: str) -> str:
    """OnePageLink bypass"""
    return await indian_transcript_v1(
        url, "https://go.onepagelink.in/", "https://gorating.in/", 3.1
    )


async def paisakamalo_bypass(url: str) -> str:
    """Paisa Kamalo bypass"""
    return await indian_transcript_v1(
        url, "https://go.paisakamalo.in", "https://healthtips.techkeshri.com/", 5
    )


async def pandaznetwork_bypass(url: str) -> str:
    """PandazNetwork bypass"""
    return await indian_transcript_v1(
        url, "https://pandaznetwork.com/", "https://panda.freemodsapp.xyz/", 5
    )


async def pdisk_bypass(url: str) -> str:
    """PDisk bypass"""
    return await indian_transcript_v1(
        url, "https://last.moneycase.link/", "https://www.webzeni.com/", 4.9
    )


async def pdiskshortener_bypass(url: str) -> str:
    """PDisk Shortener bypass"""
    return await indian_transcript_v1(
        url, "https://pdiskshortener.com/", "", 10
    )


async def publicearn_bypass(url: str) -> str:
    """PublicEarn bypass"""
    return await indian_transcript_v1(
        url, "https://publicearn.com/", "https://careersides.com/", 4.9
    )


async def rocklinks_bypass(url: str) -> str:
    """RockLinks bypass"""
    return await indian_transcript_v1(
        url, "https://land.povathemes.com/", "https://blog.disheye.com/", 4.9
    )


async def ronylink_bypass(url: str) -> str:
    """Enhanced RonyLink bypass"""
    return await indian_transcript_v1(
        url, "https://go.ronylink.com/", "https://livejankari.com/", 3
    )


async def sheralinks_bypass(url: str) -> str:
    """SheraLinks bypass"""
    return await indian_transcript_v1(
        url, "https://sheralinks.com/", "https://blogyindia.com/", 0.8
    )


async def short2url_bypass(url: str) -> str:
    """Short2URL bypass"""
    return await indian_transcript_v2(
        url, "https://techyuth.xyz/blog", "https://blog.coin2pay.xyz/", 10
    )


async def shortingly_bypass(url: str) -> str:
    """Shortingly bypass"""
    return await indian_transcript_v1(
        url, "https://go.blogytube.com/", "https://blogytube.com/", 5
    )


async def shorito_bypass(url: str) -> str:
    """Shorito bypass"""
    return await indian_transcript_v1(
        url, "https://go.shorito.com/", "https://healthgo.gorating.in/", 8
    )


async def shrinke_bypass(url: str) -> str:
    """Shrinke bypass"""
    return await indian_transcript_v1(
        url, "https://en.shrinke.me/", "https://themezon.net/", 15
    )


async def shrinkforearn_bypass(url: str) -> str:
    """ShrinkForEarn bypass"""
    return await indian_transcript_v1(
        url, "https://shrinkforearn.in/", "https://wp.uploadfiles.in/", 8
    )


async def sklinks_bypass(url: str) -> str:
    """SKLinks bypass"""
    return await indian_transcript_v1(
        url, "https://sklinks.in", "https://dailynew.online/", 5
    )


async def sxslink_bypass(url: str) -> str:
    """SXSLink bypass"""
    return await indian_transcript_v1(
        url, "https://getlink.sxslink.com/", "https://cinemapettai.in/", 5
    )


async def tamizhmasters_bypass(url: str) -> str:
    """TamilMasters bypass"""
    return await indian_transcript_v1(
        url, "https://tamizhmasters.com/", "https://pokgames.com/", 5
    )


async def tglink_bypass(url: str) -> str:
    """TGLink bypass"""
    return await indian_transcript_v1(
        url, "https://tglink.in/", "https://www.proappapk.com/", 5
    )


async def tinyfy_bypass(url: str) -> str:
    """TinyFy bypass"""
    return await indian_transcript_v1(
        url, "https://tinyfy.in", "https://www.yotrickslog.tech/", 0
    )


async def tnlink_bypass(url: str) -> str:
    """TNLink bypass"""
    return await indian_transcript_v1(
        url, "https://news.sagenews.in/", "https://knowstuff.in/", 5
    )


async def tnshort_bypass(url: str) -> str:
    """TNShort bypass"""
    return await indian_transcript_v1(
        url, "https://news.sagenews.in/", "https://movies.djnonstopmusic.in/", 5
    )


async def tnvalue_bypass(url: str) -> str:
    """TNValue bypass"""
    return await indian_transcript_v1(
        url, "https://page.finclub.in/", "https://finclub.in/", 8
    )


async def tulinks_bypass(url: str) -> str:
    """TuLinks bypass"""
    return await indian_transcript_v1(
        url, "https://tulinks.one", "https://www.blogger.com/", 8
    )


async def tulinks_online_bypass(url: str) -> str:
    """TuLinks Online bypass"""
    return await indian_transcript_v1(
        url, "https://go.tulinks.online", "https://tutelugu.co/", 8
    )


async def url4earn_bypass(url: str) -> str:
    """URL4Earn bypass"""
    return await indian_transcript_v1(
        url, "https://go.url4earn.in/", "https://techminde.com/", 8
    )


async def urllinkshort_bypass(url: str) -> str:
    """URLLinkShort bypass"""
    return await indian_transcript_v1(
        url, "https://web.urllinkshort.in", "https://suntechu.in/", 5
    )


async def urlsopen_bypass(url: str) -> str:
    """URLsOpen bypass"""
    return await indian_transcript_v1(
        url, "https://s.humanssurvival.com/", "https://1topjob.xyz/", 5
    )


async def urlspay_bypass(url: str) -> str:
    """URLsPay bypass"""
    return await indian_transcript_v1(
        url, "https://finance.smallinfo.in/", "https://tech.filmypoints.in/", 5
    )


async def v2links_bypass(url: str) -> str:
    """V2Links bypass"""
    return await indian_transcript_v1(
        url, "https://vzu.us/", "https://newsbawa.com/", 5
    )


async def viplinks_bypass(url: str) -> str:
    """VIPLinks bypass"""
    return await indian_transcript_v1(
        url, "https://m.vip-link.net/", "https://m.leadcricket.com/", 5
    )


async def vipurl_bypass(url: str) -> str:
    """VIPURL bypass"""
    return await indian_transcript_v1(
        url, "https://count.vipurl.in/", "https://kiss6kartu.in/", 5
    )


async def vplinks_bypass(url: str) -> str:
    """VPLinks bypass"""
    return await indian_transcript_v1(
        url, "https://vplink.in", "https://insurance.findgptprompts.com/", 5
    )


async def xpshort_bypass(url: str) -> str:
    """XPShort bypass"""
    return await indian_transcript_v1(
        url, "https://xpshort.com/", "https://www.comptegratuite.com/", 4.9
    )


async def ziplinker_bypass(url: str) -> str:
    """ZipLinker bypass"""
    return await indian_transcript_v1(
        url, "https://ziplinker.net", "https://fintech.techweeky.com/", 1
    )


# Additional specialized bypasses for complex Indian shorteners

async def try2link_enhanced_bypass(url: str) -> str:
    """Enhanced Try2Link bypass with multiple referers"""
    domain = 'https://try2link.com'
    code = url.split('/')[-1]
    
    session = IndianBypassSession()
    
    referers = [
        'https://hightrip.net/',
        'https://to-travel.net/',
        'https://world2our.com/',
        'https://techymozo.com/',
        'https://blog.disheye.com/'
    ]
    
    for referer in referers:
        try:
            html, cookies, status, _ = await session.get_with_retry(
                f'{domain}/{code}',
                headers={"Referer": referer}
            )
            
            if status == 200:
                soup = BeautifulSoup(html, "html.parser")
                go_link = soup.find(id="go-link")
                
                if go_link:
                    inputs = go_link.find_all("input")
                    data = {inp.get('name'): inp.get('value') for inp in inputs}
                    
                    await asleep(6)
                    
                    response_text, _, status, headers = await session.post_with_retry(
                        f"{domain}/links/go",
                        data=data,
                        headers={"X-Requested-With": "XMLHttpRequest"},
                        cookies=cookies
                    )
                    
                    if 'application/json' in headers.get('Content-Type', ''):
                        json_data = loads(response_text)
                        if 'url' in json_data:
                            return json_data['url']
                            
        except Exception:
            continue
    
    raise DDLException("Try2Link enhanced bypass failed")


# Master bypass function mapping
INDIAN_SHORTENER_MAP = {
    # A
    r"https?:\/\/adrinolinks\.\S+": adrinolinks_bypass,
    r"https?:\/\/adsfly\.\S+": adsfly_bypass,
    r"https?:\/\/(.+\.)?anlinks\.\S+": anlinks_bypass,
    
    # B
    r"https?:\/\/bindaaslinks\.\S+": bindaaslinks_bypass,
    r"https?:\/\/bringlifes\.\S+": bringlifes_bypass,
    
    # D
    r"https?:\/\/dalink\.\S+": dalink_bypass,
    r"https?:\/\/droplink\.\S+": droplink_bypass,
    r"https?:\/\/.+\.dtglinks\.\S+": dtglinks_bypass,
    r"https?:\/\/(du-link|dulink)\.\S+": dulink_bypass,
    
    # E
    r"https?:\/\/.+\.earn2me\.\S+": earn2me_bypass,
    r"https?:\/\/earn2short\.\S+": earn2short_bypass,
    r"https?:\/\/earn4link\.\S+": earn4link_bypass,
    r"https?:\/\/earn\.moneykamalo\.\S+": earnmoneykamalo_bypass,
    r"https?:\/\/m\.easysky\.\S+": easysky_bypass,
    r"https?:\/\/.+\.evolinks\.\S+": evolinks_bypass,
    r"https?:\/\/ez4short\.\S+": ez4short_bypass,
    
    # G
    r"https?:\/\/(gyanilinks|gtlinks)\.\S+": gyanilinks_bypass,
    
    # I
    r"https?:\/\/indianshortner\.\S+": indianshortner_bypass,
    r"https?:\/\/indyshare\.\S+": indyshare_bypass,
    r"https?:\/\/instantearn\.\S+": instantearn_bypass,
    
    # K
    r"https?:\/\/(.+\.)?kpslink\.\S+": kpslink_bypass,
    r"https?:\/\/v2\.kpslink\.\S+": kpslink_v2_bypass,
    r"https?:\/\/krownlinks\.\S+": krownlinks_bypass,
    
    # L
    r"https?:\/\/link4earn\.\S+": link4earn_bypass,
    r"https?:\/\/.+\.linkfly\.\S+": linkfly_bypass,
    r"https?:\/\/linkjust\.\S+": linkjust_bypass,
    r"https?:\/\/linkpays\.\S+": linkpays_bypass,
    r"https?:\/\/link1s\.\S+": links1_bypass,
    r"https?:\/\/linkshortx\.\S+": linkshortx_bypass,
    r"https?:\/\/linksly\.\S+": linksly_bypass,
    r"https?:\/\/linksxyz\.\S+": linksxyz_bypass,
    r"https?:\/\/linkyearn\.\S+": linkyearn_bypass,
    
    # M
    r"https?:\/\/mdisk\.\S+": mdisk_bypass,
    r"https?:\/\/(.+\.)?mdiskshortner\.\S+": mdiskshortner_bypass,
    r"https?:\/\/modijiurl\.\S+": modijiurl_bypass,
    r"https?:\/\/moneycase\.\S+": moneycase_bypass,
    r"https?:\/\/mplaylink\.\S+": mplaylink_bypass,
    
    # N
    r"https?:\/\/.+\.narzolinks\.\S+": narzolinks_bypass,
    
    # O
    r"https?:\/\/.+\.omnifly\.\S+": omnifly_bypass,
    r"https?:\/\/onepagelink\.\S+": onepagelink_bypass,
    
    # P
    r"https?:\/\/(pkin|go\.paisakamalo)\.\S+": paisakamalo_bypass,
    r"https?:\/\/pandaznetwork\.\S+": pandaznetwork_bypass,
    r"https?:\/\/pdisk\.\S+": pdisk_bypass,
    r"https?:\/\/pdiskshortener\.\S+": pdiskshortener_bypass,
    r"https?:\/\/publicearn\.\S+": publicearn_bypass,
    
    # R
    r"https?://(?:\w+\.)?rocklinks\.\S+": rocklinks_bypass,
    r"https?:\/\/ronylink\.\S+": ronylink_bypass,
    
    # S
    r"https?:\/\/sheralinks\.\S+": sheralinks_bypass,
    r"https?:\/\/short2url\.\S+": short2url_bypass,
    r"https?:\/\/.+\.short2url\.\S+": short2url_bypass,
    r"https?:\/\/shortingly\.\S+": shortingly_bypass,
    r"https?:\/\/.+\.shorito\.\S+": shorito_bypass,
    r"https?:\/\/shrinke\.\S+": shrinke_bypass,
    r"https?:\/\/shrinkforearn\.\S+": shrinkforearn_bypass,
    r"https?:\/\/sklinks\.\S+": sklinks_bypass,
    r"https?:\/\/sxslink\.\S+": sxslink_bypass,
    
    # T
    r"https?:\/\/tamizhmasters\.\S+": tamizhmasters_bypass,
    r"https?:\/\/tglink\.\S+": tglink_bypass,
    r"https?:\/\/tinyfy\.\S+": tinyfy_bypass,
    r"https?:\/\/.+\.tnlink\.\S+": tnlink_bypass,
    r"https?:\/\/.+\.tnshort\.\S+": tnshort_bypass,
    r"https?:\/\/.+\.tnvalue\.\S+": tnvalue_bypass,
    r"https?:\/\/try2link\.\S+": try2link_enhanced_bypass,
    r"https?:\/\/tulinks\.\S+": tulinks_bypass,
    r"https?:\/\/.+\.tulinks\.\S+": tulinks_online_bypass,
    
    # U
    r"https?:\/\/url4earn\.\S+": url4earn_bypass,
    r"https?:\/\/urllinkshort\.\S+": urllinkshort_bypass,
    r"https?:\/\/urlsopen\.\S+": urlsopen_bypass,
    r"https?:\/\/urlspay\.\S+": urlspay_bypass,
    
    # V
    r"https?:\/\/v2links\.\S+": v2links_bypass,
    r"https?:\/\/viplinks\.\S+": viplinks_bypass,
    r"https?:\/\/(.+\.)?vipurl\.\S+": vipurl_bypass,
    r"https?:\/\/.+\.vplinks\.\S+": vplinks_bypass,
    
    # X
    r"https?:\/\/(xpshort|push\.bdnewsx|techymozo)\.\S+": xpshort_bypass,
    
    # Z
    r"https?:\/\/ziplinker\.\S+": ziplinker_bypass,
}


async def indian_shortener_bypass(url: str) -> str:
    """Master function to bypass Indian shorteners"""
    for pattern, bypass_func in INDIAN_SHORTENER_MAP.items():
        if match(pattern, url):
            try:
                result = await bypass_func(url)
                if result and result != url:
                    return result
            except Exception as e:
                LOGGER.error(f"Indian shortener bypass failed for {url}: {e}")
                raise DDLException(f"Bypass failed: {str(e)}")
    
    raise DDLException(f"No Indian shortener bypass found for: {urlparse(url).hostname}")