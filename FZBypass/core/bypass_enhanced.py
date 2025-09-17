"""
Enhanced bypass functions with better error handling and performance
"""
from asyncio import create_task, gather, sleep as asleep, timeout, TimeoutError
from re import match, search
from urllib.parse import urlparse
from json import loads

from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientTimeout

from FZBypass import Config, LOGGER
from FZBypass.core.exceptions import DDLException
from FZBypass.core.recaptcha import recaptchaV3
from FZBypass.core.bypass_truelink import get_truelink_bypass, TRUELINK_PATTERNS


class BypassSession:
    """Enhanced session management for bypass operations"""
    
    def __init__(self):
        self.timeout = ClientTimeout(total=30)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }
    
    async def get_with_retry(self, url, retries=3, **kwargs):
        """Get request with retry mechanism"""
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.get(url, **kwargs) as response:
                        return await response.text(), response.cookies, response.status
            except Exception as e:
                if attempt == retries - 1:
                    raise DDLException(f"Failed after {retries} attempts: {str(e)}")
                await asleep(1)
    
    async def post_with_retry(self, url, data=None, json=None, retries=3, **kwargs):
        """Post request with retry mechanism"""
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=self.timeout, headers=self.headers) as session:
                    async with session.post(url, data=data, json=json, **kwargs) as response:
                        return await response.text(), response.cookies, response.status
            except Exception as e:
                if attempt == retries - 1:
                    raise DDLException(f"Failed after {retries} attempts: {str(e)}")
                await asleep(1)


async def enhanced_transcript(url: str, domain: str, referer: str, sleep_time: float) -> str:
    """Enhanced transcript function with better error handling"""
    session = BypassSession()
    code = url.rstrip("/").split("/")[-1]
    
    try:
        # Get initial page
        html, cookies, status = await session.get_with_retry(
            f"{domain}/{code}",
            headers={'Referer': referer}
        )
        
        if status != 200:
            raise DDLException(f"HTTP {status} error")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for Cloudflare protection
        if soup.find('title') and 'Just a moment' in soup.find('title').text:
            raise DDLException("Cloudflare protection detected")
        
        # Extract form data
        form_data = {}
        for inp in soup.find_all('input'):
            name = inp.get('name')
            value = inp.get('value')
            if name and value:
                form_data[name] = value
        
        if not form_data:
            raise DDLException("No form data found")
        
        # Wait before submitting
        await asleep(sleep_time)
        
        # Submit form
        response_text, _, status = await session.post_with_retry(
            f"{domain}/links/go",
            data=form_data,
            headers={
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{domain}/{code}"
            },
            cookies=cookies
        )
        
        if status != 200:
            raise DDLException(f"Form submission failed with HTTP {status}")
        
        try:
            result = loads(response_text)
            if 'url' in result:
                return result['url']
            else:
                raise DDLException("No URL in response")
        except Exception:
            raise DDLException("Invalid JSON response")
            
    except TimeoutError:
        raise DDLException("Request timeout")
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Unexpected error: {str(e)}")


async def enhanced_ouo(url: str) -> str:
    """Enhanced OUO bypass with better handling"""
    session = BypassSession()
    
    try:
        # Convert to ouo.press for better compatibility
        url = url.replace("ouo.io", "ouo.press")
        parsed = urlparse(url)
        link_id = url.split("/")[-1]
        
        # Get initial page
        html, cookies, _ = await session.get_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find form and extract token
        form = soup.find('form')
        if not form:
            raise DDLException("No form found")
        
        token_input = form.find('input', {'name': lambda x: x and x.endswith('token')})
        if not token_input:
            raise DDLException("No token found")
        
        # Get reCAPTCHA token
        recaptcha_token = await recaptchaV3()
        
        # Prepare form data
        form_data = {
            token_input.get('name'): token_input.get('value'),
            'x-token': recaptcha_token
        }
        
        # Submit form
        next_url = f"{parsed.scheme}://{parsed.hostname}/go/{link_id}"
        response_text, response_cookies, _ = await session.post_with_retry(
            next_url,
            data=form_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False,
            cookies=cookies
        )
        
        # Check for redirect
        if 'Location' in response_text:
            return response_text['Location']
        
        # Try second step if needed
        next_url = f"{parsed.scheme}://{parsed.hostname}/xreallcygo/{link_id}"
        response_text, _, _ = await session.post_with_retry(
            next_url,
            data=form_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False,
            cookies=response_cookies
        )
        
        if 'Location' in response_text:
            return response_text['Location']
        
        raise DDLException("No redirect found")
        
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"OUO bypass failed: {str(e)}")


async def enhanced_terabox(url: str) -> str:
    """Enhanced Terabox bypass with better cookie handling"""
    if not Config.TERA_COOKIE:
        raise DDLException("TERA_COOKIE not configured")
    
    session = BypassSession()
    
    try:
        # Get redirect URL
        html, cookies, _ = await session.get_with_retry(url)
        final_url = url  # In real implementation, extract from response
        
        key = final_url.split("?surl=")[-1]
        api_url = f"http://www.terabox.com/wap/share/filelist?surl={key}"
        
        # Set cookies
        cookies_dict = {"ndus": Config.TERA_COOKIE}
        
        # Get file list
        html, _, _ = await session.get_with_retry(api_url, cookies=cookies_dict)
        soup = BeautifulSoup(html, "lxml")
        
        # Extract JS token
        js_token = None
        for script in soup.find_all("script"):
            if script.string and script.string.startswith("try {eval(decodeURIComponent"):
                js_token = script.string.split("%22")[1]
                break
        
        if not js_token:
            raise DDLException("JS token not found")
        
        # Get download link
        api_url = f"https://www.terabox.com/share/list?app_id=250528&jsToken={js_token}&shorturl={key}&root=1"
        response_text, _, _ = await session.get_with_retry(api_url, cookies=cookies_dict)
        
        result = loads(response_text)
        if result["errno"] != 0:
            raise DDLException(f"API Error: {result.get('errmsg', 'Unknown error')}")
        
        file_list = result["list"]
        if len(file_list) > 1:
            raise DDLException("Multiple files not supported")
        
        file_info = file_list[0]
        if file_info["isdir"] != "0":
            raise DDLException("Folders not supported")
        
        if "dlink" not in file_info:
            raise DDLException("Download link not available")
        
        return file_info["dlink"]
        
    except Exception as e:
        if isinstance(e, DDLException):
            raise
        raise DDLException(f"Terabox bypass failed: {str(e)}")


async def batch_bypass(urls: list, max_concurrent=5) -> list:
    """Process multiple URLs concurrently with rate limiting"""
    results = []
    
    # Process URLs in batches to avoid overwhelming servers
    for i in range(0, len(urls), max_concurrent):
        batch = urls[i:i + max_concurrent]
        tasks = [create_task(single_bypass(url)) for url in batch]
        
        try:
            batch_results = await gather(*tasks, return_exceptions=True)
            results.extend(batch_results)
        except Exception as e:
            LOGGER.error(f"Batch processing error: {e}")
            results.extend([DDLException(f"Batch error: {e}") for _ in batch])
        
        # Small delay between batches
        if i + max_concurrent < len(urls):
            await asleep(1)
    
    return results


async def single_bypass(url: str) -> str:
    """Single URL bypass with timeout protection"""
    try:
        async with timeout(60):  # 60 second timeout
            return await direct_link_checker_enhanced(url)
    except TimeoutError:
        raise DDLException("Bypass timeout (60s)")
    except Exception as e:
        raise DDLException(f"Bypass failed: {str(e)}")


async def direct_link_checker_enhanced(url: str) -> str:
    """Enhanced direct link checker with improved pattern matching"""
    
    # Priority 1: Try TrueLink for supported file hosting services
    truelink = get_truelink_bypass()
    if truelink:
        # Check TrueLink patterns first
        for pattern, service in TRUELINK_PATTERNS.items():
            if match(pattern, url):
                try:
                    LOGGER.info(f"Attempting TrueLink bypass for {service}: {url}")
                    result = await truelink.resolve(url)
                    if result and result.get('download_url'):
                        return result['formatted_output']
                except Exception as e:
                    LOGGER.warning(f"TrueLink {service} bypass failed: {e}")
                    break  # Try other methods
    
    domain = urlparse(url).hostname.lower()
    
    # Enhanced pattern matching with better error handling
    bypass_map = {
        # File hosting services
        r"https?:\/\/(yadi|disk\.yandex)\.\S+": lambda u: yandex_disk(u),
        r"https?:\/\/.+\.mediafire\.\S+": lambda u: mediafire(u),
        r"https?:\/\/shrdsk\.\S+": lambda u: shrdsk(u),
        
        # Terabox variants
        r"https?:\/\/.*(1024tera|terabox|nephobox|4funbox|mirrobox|momerybox|teraboxapp)\.\S+": lambda u: enhanced_terabox(u),
        
        # Shortener services with enhanced handling
        r"https?:\/\/try2link\.\S+": lambda u: try2link(u),
        r"https?:\/\/(gyanilinks|gtlinks)\.\S+": lambda u: gyanilinks(u),
        r"https?:\/\/ouo\.\S+": lambda u: enhanced_ouo(u),
        
        # Enhanced transcript-based bypasses
        r"https?:\/\/adrinolinks\.\S+": lambda u: enhanced_transcript(u, "https://adrinolinks.in", "https://bhojpuritop.in/", 8),
        r"https?:\/\/adsfly\.\S+": lambda u: enhanced_transcript(u, "https://go.adsfly.in/", "https://letest25.co/", 3),
        r"https?:\/\/(.+\.)?anlinks\.\S+": lambda u: enhanced_transcript(u, "https://anlinks.in/", "https://dsblogs.fun/", 8),
        r"https?:\/\/ronylink\.\S+": lambda u: enhanced_transcript(u, "https://go.ronylink.com/", "https://livejankari.com/", 3),
        r"https?:\/\/.+\.evolinks\.\S+": lambda u: enhanced_transcript(u, "https://ads.evolinks.in/", u, 3),
        
        # Additional shorteners
        r"https?:\/\/linkshortx\.\S+": lambda u: enhanced_transcript(u, "https://linkshortx.in/", "https://nanotech.org.in/", 4.9),
        r"https?:\/\/ziplinker\.\S+": lambda u: enhanced_transcript(u, "https://ziplinker.net", "https://fintech.techweeky.com/", 1),
        r"https?:\/\/earn4link\.\S+": lambda u: enhanced_transcript(u, "https://m.open2get.in/", "https://ezeviral.com/", 8),
        
        # Simple redirects
        r"https?:\/\/(bit|tinyurl|(.+\.)short|shorturl|t)\.\S+": lambda u: shorter(u),
        r"https?:\/\/(.+\.)?dropbox\.\S+": lambda u: dropbox(u),
    }
    
    # Try to match URL pattern and execute corresponding bypass
    for pattern, bypass_func in bypass_map.items():
        if match(pattern, url):
            try:
                result = await bypass_func(url)
                if result:
                    return result
            except Exception as e:
                LOGGER.error(f"Bypass failed for {url}: {e}")
                raise DDLException(f"Bypass error: {str(e)}")
    
    # If no pattern matches
    raise DDLException(f"No bypass method available for: {domain}")


async def smart_loop_bypass(url: str, max_depth=5) -> list:
    """Smart loop bypass that detects and handles nested shorteners"""
    results = []
    current_url = url
    depth = 0
    
    while depth < max_depth:
        try:
            bypassed_url = await direct_link_checker_enhanced(current_url)
            results.append(bypassed_url)
            
            # Check if the result is another shortener
            if is_shortener(bypassed_url):
                current_url = bypassed_url
                depth += 1
                await asleep(0.5)  # Small delay between iterations
            else:
                break
                
        except Exception:
            if depth == 0:
                raise  # Re-raise if first bypass fails
            break  # Stop loop if subsequent bypass fails
    
    return results if results else [url]


def is_shortener(url: str) -> bool:
    """Check if URL is a known shortener"""
    shortener_domains = [
        'bit.ly', 'tinyurl.com', 'short.gy', 'shorturl.ac', 't.ly',
        'ouo.io', 'ouo.press', 'try2link.com', 'gyanilinks.com',
        'gtlinks.me', 'adrinolinks.com', 'adsfly.in', 'anlinks.in',
        'ronylink.com', 'evolinks.in', 'linkshortx.in', 'ziplinker.net'
    ]
    
    domain = urlparse(url).hostname
    return any(shortener in domain for shortener in shortener_domains)


async def validate_bypass_result(original_url: str, bypassed_url: str) -> bool:
    """Validate that bypass result is legitimate"""
    try:
        # Basic validation checks
        if not bypassed_url or bypassed_url == original_url:
            return False
        
        # Check if it's a valid URL
        parsed = urlparse(bypassed_url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            'javascript:', 'data:', 'about:', 'file:',
            'localhost', '127.0.0.1', '0.0.0.0'
        ]
        
        if any(pattern in bypassed_url.lower() for pattern in invalid_patterns):
            return False
        
        return True
        
    except Exception:
        return False


async def get_file_info(url: str) -> dict:
    """Extract file information from various sources"""
    try:
        session = BypassSession()
        html, _, _ = await session.get_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        info = {
            'title': 'Unknown',
            'size': 'Unknown',
            'type': 'Unknown'
        }
        
        # Try to extract title
        if soup.title:
            info['title'] = soup.title.string.strip()
        
        # Try to extract size from meta tags
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if 'size' in content.lower():
                size_match = search(r'(\d+(?:\.\d+)?\s*[KMGT]?B)', content)
                if size_match:
                    info['size'] = size_match.group(1)
        
        return info
        
    except Exception:
        return {'title': 'Unknown', 'size': 'Unknown', 'type': 'Unknown'}