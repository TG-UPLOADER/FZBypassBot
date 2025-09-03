"""
Health check and monitoring utilities
"""
from time import time
from asyncio import create_task, gather, timeout, TimeoutError
from typing import Dict, Any
import psutil
from os import getpid

from FZBypass import Config, LOGGER
from FZBypass.core.bypass_enhanced import direct_link_checker_enhanced


class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.last_check = 0
        self.check_interval = 300  # 5 minutes
        self.health_status = {}
    
    async def full_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        checks = {}
        
        # System resources
        try:
            process = psutil.Process(getpid())
            checks['memory_usage'] = {
                'status': 'healthy',
                'value': f"{process.memory_info().rss / 1024 / 1024:.1f} MB",
                'percentage': process.memory_percent()
            }
            
            checks['cpu_usage'] = {
                'status': 'healthy',
                'value': f"{process.cpu_percent():.1f}%"
            }
        except Exception as e:
            checks['system'] = {'status': 'error', 'error': str(e)}
        
        # Configuration check
        checks['config'] = await self._check_config()
        
        # Bypass functionality check
        checks['bypass'] = await self._check_bypass_functionality()
        
        # Database connectivity (if applicable)
        checks['storage'] = await self._check_storage()
        
        self.health_status = checks
        self.last_check = time()
        
        return checks
    
    async def _check_config(self) -> Dict[str, Any]:
        """Check configuration completeness"""
        required_configs = ['BOT_TOKEN', 'API_ID', 'API_HASH']
        optional_configs = [
            'GDTOT_CRYPT', 'HUBDRIVE_CRYPT', 'DRIVEFIRE_CRYPT',
            'KATDRIVE_CRYPT', 'TERA_COOKIE', 'DIRECT_INDEX'
        ]
        
        missing_required = []
        for config in required_configs:
            if not getattr(Config, config, None):
                missing_required.append(config)
        
        configured_optional = sum(
            1 for config in optional_configs 
            if getattr(Config, config, None)
        )
        
        if missing_required:
            return {
                'status': 'error',
                'missing_required': missing_required,
                'optional_configured': f"{configured_optional}/{len(optional_configs)}"
            }
        
        return {
            'status': 'healthy',
            'optional_configured': f"{configured_optional}/{len(optional_configs)}"
        }
    
    async def _check_bypass_functionality(self) -> Dict[str, Any]:
        """Test bypass functionality with sample URLs"""
        test_urls = [
            "https://bit.ly/test",  # Simple redirect
            "https://tinyurl.com/test"  # Another simple redirect
        ]
        
        working_bypasses = 0
        total_tests = len(test_urls)
        
        for test_url in test_urls:
            try:
                async with timeout(10):
                    await direct_link_checker_enhanced(test_url)
                working_bypasses += 1
            except (TimeoutError, Exception):
                pass
        
        success_rate = (working_bypasses / total_tests) * 100
        
        if success_rate >= 50:
            status = 'healthy'
        elif success_rate >= 25:
            status = 'warning'
        else:
            status = 'error'
        
        return {
            'status': status,
            'success_rate': f"{success_rate:.1f}%",
            'working_bypasses': f"{working_bypasses}/{total_tests}"
        }
    
    async def _check_storage(self) -> Dict[str, Any]:
        """Check storage and logging functionality"""
        try:
            # Check if log file is writable
            with open("log.txt", "a") as f:
                f.write(f"Health check: {time()}\n")
            
            return {'status': 'healthy', 'logging': 'functional'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_status_summary(self) -> str:
        """Get overall health status"""
        if not self.health_status:
            return 'unknown'
        
        error_count = sum(
            1 for check in self.health_status.values() 
            if isinstance(check, dict) and check.get('status') == 'error'
        )
        
        warning_count = sum(
            1 for check in self.health_status.values() 
            if isinstance(check, dict) and check.get('status') == 'warning'
        )
        
        if error_count > 0:
            return 'unhealthy'
        elif warning_count > 0:
            return 'warning'
        else:
            return 'healthy'


# Global health checker instance
health_checker = HealthChecker()