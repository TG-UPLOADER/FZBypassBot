"""
TrueLink Integration for Enhanced File Hosting Bypass
Supports: BuzzHeavier, 1Fichier, FuckingFast, GoFile, LinkBox, LulaCloud, 
MediaFile, MediaFire, PixelDrain, StreamTape, TeraBox, TmpSend, UploadEE, YandexLink, Ranoz
"""
from typing import Dict, Any
from urllib.parse import urlparse

from FZBypass import LOGGER
from FZBypass.core.exceptions import DDLException

try:
    from truelink import TrueLinkResolver
    TRUELINK_AVAILABLE = True
except ImportError:
    TRUELINK_AVAILABLE = False
    LOGGER.warning("TrueLink library not available. Install with: pip install truelink")


class TrueLinkBypass:
    """Enhanced bypass using TrueLink library"""
    
    def __init__(self):
        if not TRUELINK_AVAILABLE:
            raise DDLException("TrueLink library not installed")
        self.resolver = TrueLinkResolver()
        
        # Supported domains mapping
        self.supported_domains = {
            'buzzheavier.com': 'BuzzHeavier',
            '1fichier.com': '1Fichier',
            'fuckingfast.co': 'FuckingFast',
            'gofile.io': 'GoFile',
            'linkbox.to': 'LinkBox',
            'lulacloud.com': 'LulaCloud',
            'mediafile.org': 'MediaFile',
            'mediafire.com': 'MediaFire',
            'pixeldrain.com': 'PixelDrain',
            'streamtape.com': 'StreamTape',
            'terabox.com': 'TeraBox',
            'teraboxapp.com': 'TeraBox',
            '1024tera.com': 'TeraBox',
            'nephobox.com': 'TeraBox',
            '4funbox.com': 'TeraBox',
            'mirrobox.com': 'TeraBox',
            'momerybox.com': 'TeraBox',
            'tmpsend.com': 'TmpSend',
            'uploadee.com': 'UploadEE',
            'yadi.sk': 'YandexLink',
            'disk.yandex.com': 'YandexLink',
            'ranoz.com': 'Ranoz'
        }
    
    def is_supported(self, url: str) -> bool:
        """Check if URL is supported by TrueLink"""
        try:
            if not TRUELINK_AVAILABLE:
                return False
            
            domain = urlparse(url).hostname
            if not domain:
                return False
            
            # Remove www. prefix
            domain = domain.replace('www.', '')
            
            # Check if domain is in our supported list
            if domain in self.supported_domains:
                return TrueLinkResolver.is_supported(url)
            
            # Fallback to TrueLink's own check
            return TrueLinkResolver.is_supported(url)
        except Exception as e:
            LOGGER.error(f"Error checking TrueLink support for {url}: {e}")
            return False
    
    async def resolve(self, url: str) -> Dict[str, Any]:
        """Resolve URL using TrueLink and return structured data"""
        try:
            if not self.is_supported(url):
                raise DDLException(f"URL not supported by TrueLink: {url}")
            
            LOGGER.info(f"Resolving with TrueLink: {url}")
            result = await self.resolver.resolve(url)
            
            if not result:
                raise DDLException("TrueLink returned empty result")
            
            # Structure the result for consistent output
            return self._format_result(url, result)
            
        except Exception as e:
            LOGGER.error(f"TrueLink resolution failed for {url}: {e}")
            raise DDLException(f"TrueLink bypass failed: {str(e)}")
    
    def _format_result(self, original_url: str, result: Any) -> Dict[str, Any]:
        """Format TrueLink result into structured data"""
        domain = urlparse(original_url).hostname.replace('www.', '')
        service_name = self.supported_domains.get(domain, 'Unknown')
        
        # Handle different result types
        if isinstance(result, str):
            # Simple URL result
            return {
                'service': service_name,
                'original_url': original_url,
                'download_url': result,
                'file_name': 'Unknown',
                'file_size': 'Unknown',
                'formatted_output': self._create_formatted_output(service_name, original_url, result)
            }
        elif isinstance(result, dict):
            # Structured result with metadata
            download_url = result.get('url', result.get('download_url', ''))
            file_name = result.get('name', result.get('filename', 'Unknown'))
            file_size = result.get('size', result.get('filesize', 'Unknown'))
            
            return {
                'service': service_name,
                'original_url': original_url,
                'download_url': download_url,
                'file_name': file_name,
                'file_size': file_size,
                'metadata': result,
                'formatted_output': self._create_formatted_output(
                    service_name, original_url, download_url, file_name, file_size
                )
            }
        else:
            # Fallback for unknown result types
            return {
                'service': service_name,
                'original_url': original_url,
                'raw_result': str(result),
                'formatted_output': f"┎ <b>{service_name}:</b> <a href='{original_url}'>Click Here</a>\n┗ <b>Result:</b> {str(result)}"
            }
    
    def _create_formatted_output(self, service: str, original_url: str, download_url: str, 
                                file_name: str = 'Unknown', file_size: str = 'Unknown') -> str:
        """Create formatted output for display"""
        output = f"┎ <b>{service}:</b> <a href='{original_url}'>Click Here</a>\n"
        
        if file_name != 'Unknown':
            output += f"┠ <b>Name:</b> <code>{file_name}</code>\n"
        
        if file_size != 'Unknown':
            output += f"┠ <b>Size:</b> <code>{file_size}</code>\n"
        
        if download_url:
            output += f"┗ <b>Download:</b> <a href='{download_url}'>Direct Link</a>"
        else:
            output += "┗ <b>Status:</b> Processing..."
        
        return output


# Global TrueLink instance
truelink_bypass = None

def get_truelink_bypass():
    """Get or create TrueLink bypass instance"""
    global truelink_bypass
    if truelink_bypass is None and TRUELINK_AVAILABLE:
        try:
            truelink_bypass = TrueLinkBypass()
        except Exception as e:
            LOGGER.error(f"Failed to initialize TrueLink: {e}")
    return truelink_bypass


async def truelink_resolver(url: str) -> str:
    """Simple TrueLink resolver function for backward compatibility"""
    bypass = get_truelink_bypass()
    if not bypass:
        raise DDLException("TrueLink not available")
    
    result = await bypass.resolve(url)
    return result.get('formatted_output', str(result))


# Supported domain patterns for integration
TRUELINK_PATTERNS = {
    r"https?:\/\/(www\.)?buzzheavier\.\S+": "BuzzHeavier",
    r"https?:\/\/(www\.)?1fichier\.\S+": "1Fichier", 
    r"https?:\/\/(www\.)?fuckingfast\.\S+": "FuckingFast",
    r"https?:\/\/(www\.)?gofile\.\S+": "GoFile",
    r"https?:\/\/(www\.)?linkbox\.\S+": "LinkBox",
    r"https?:\/\/(www\.)?lulacloud\.\S+": "LulaCloud",
    r"https?:\/\/(www\.)?mediafile\.\S+": "MediaFile",
    r"https?:\/\/(www\.)?pixeldrain\.\S+": "PixelDrain",
    r"https?:\/\/(www\.)?streamtape\.\S+": "StreamTape",
    r"https?:\/\/(www\.)?tmpsend\.\S+": "TmpSend",
    r"https?:\/\/(www\.)?uploadee\.\S+": "UploadEE",
    r"https?:\/\/(www\.)?ranoz\.\S+": "Ranoz",
    # TeraBox variants
    r"https?:\/\/(www\.)?(terabox|teraboxapp|1024tera|nephobox|4funbox|mirrobox|momerybox)\.\S+": "TeraBox",
    # Yandex variants  
    r"https?:\/\/(www\.)?(yadi\.sk|disk\.yandex)\.\S+": "YandexLink"
}