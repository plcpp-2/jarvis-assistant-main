import asyncio
import aiohttp
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
import ssl
import json
import socket
from aiohttp import ClientTimeout
from prometheus_client import Counter, Histogram

class NetworkExecutor:
    def __init__(self):
        self.logger = logging.getLogger("NetworkExecutor")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Metrics
        self.request_counter = Counter(
            'network_requests_total',
            'Total number of network requests',
            ['method', 'status']
        )
        self.request_duration = Histogram(
            'network_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'status']
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = 30,
        verify_ssl: bool = True,
        allow_redirects: bool = True,
        proxy: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            start_time = datetime.now()
            
            # Configure SSL context
            ssl_context = None if verify_ssl else ssl.create_default_context()
            if not verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            # Configure timeout
            timeout_obj = ClientTimeout(total=timeout)

            async with self.session.request(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                json=json_data,
                timeout=timeout_obj,
                ssl=ssl_context,
                allow_redirects=allow_redirects,
                proxy=proxy
            ) as response:
                duration = (datetime.now() - start_time).total_seconds()
                
                # Update metrics
                self.request_counter.labels(
                    method=method,
                    status=response.status
                ).inc()
                self.request_duration.labels(
                    method=method,
                    status=response.status
                ).observe(duration)

                content_type = response.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    response_data = await response.json()
                else:
                    response_data = await response.text()

                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'data': response_data,
                    'duration': duration,
                    'url': str(response.url)
                }

        except Exception as e:
            self.logger.error(f"Request failed: {str(e)}")
            raise

    async def websocket_connect(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        ssl_context: Optional[ssl.SSLContext] = None
    ) -> aiohttp.ClientWebSocketResponse:
        """Establish a WebSocket connection"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            return await self.session.ws_connect(
                url,
                headers=headers,
                ssl=ssl_context
            )

        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            raise

    async def download_file(
        self,
        url: str,
        destination: str,
        chunk_size: int = 8192,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Union[str, int, float]]:
        """Download a file with progress tracking"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            start_time = datetime.now()
            total_size = 0
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                with open(destination, 'wb') as f:
                    while True:
                        chunk = await response.content.read(chunk_size)
                        if not chunk:
                            break
                            
                        f.write(chunk)
                        total_size += len(chunk)
                        
                        if progress_callback:
                            progress_callback(total_size)

                duration = (datetime.now() - start_time).total_seconds()
                
                return {
                    'destination': destination,
                    'size': total_size,
                    'duration': duration,
                    'speed': total_size / duration if duration > 0 else 0
                }

        except Exception as e:
            self.logger.error(f"File download failed: {str(e)}")
            raise

    async def scan_ports(
        self,
        host: str,
        ports: Union[List[int], range],
        timeout: float = 1.0
    ) -> List[Dict[str, Union[int, bool, float]]]:
        """Scan ports on a host"""
        async def check_port(port: int) -> Dict[str, Union[int, bool, float]]:
            try:
                start_time = datetime.now()
                
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=timeout
                )
                writer.close()
                await writer.wait_closed()
                
                duration = (datetime.now() - start_time).total_seconds()
                return {
                    'port': port,
                    'open': True,
                    'duration': duration
                }
            except (asyncio.TimeoutError, ConnectionRefusedError):
                return {
                    'port': port,
                    'open': False,
                    'duration': timeout
                }

        try:
            tasks = [check_port(port) for port in ports]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result['open']]

        except Exception as e:
            self.logger.error(f"Port scan failed: {str(e)}")
            raise

    async def dns_lookup(
        self,
        domain: str,
        record_type: str = 'A'
    ) -> Dict[str, Union[str, List[str]]]:
        """Perform DNS lookup"""
        try:
            if record_type == 'A':
                result = socket.gethostbyname_ex(domain)
                return {
                    'domain': domain,
                    'hostname': result[0],
                    'aliases': result[1],
                    'addresses': result[2]
                }
            else:
                # Add support for other record types using aiodns
                raise NotImplementedError(
                    f"Record type {record_type} not implemented"
                )

        except Exception as e:
            self.logger.error(f"DNS lookup failed: {str(e)}")
            raise

    async def test_connectivity(
        self,
        targets: List[str],
        timeout: float = 5.0
    ) -> List[Dict[str, Union[str, bool, float]]]:
        """Test connectivity to multiple targets"""
        async def check_target(target: str) -> Dict[str, Union[str, bool, float]]:
            try:
                start_time = datetime.now()
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        target,
                        timeout=ClientTimeout(total=timeout)
                    ) as response:
                        duration = (datetime.now() - start_time).total_seconds()
                        return {
                            'target': target,
                            'reachable': True,
                            'status': response.status,
                            'duration': duration
                        }
            except Exception as e:
                return {
                    'target': target,
                    'reachable': False,
                    'error': str(e),
                    'duration': timeout
                }

        try:
            tasks = [check_target(target) for target in targets]
            return await asyncio.gather(*tasks)

        except Exception as e:
            self.logger.error(f"Connectivity test failed: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        async with NetworkExecutor() as executor:
            # Make HTTP request
            result = await executor.make_request(
                'GET',
                'https://api.github.com/users/octocat'
            )
            print("API Response:", json.dumps(result, indent=2))

            # Scan ports
            open_ports = await executor.scan_ports(
                'localhost',
                range(8000, 8010)
            )
            print("Open ports:", open_ports)

            # Test connectivity
            connectivity = await executor.test_connectivity([
                'https://google.com',
                'https://github.com'
            ])
            print("Connectivity test:", json.dumps(connectivity, indent=2))

    asyncio.run(main())
