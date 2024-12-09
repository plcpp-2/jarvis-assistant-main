import asyncio
import aiohttp.web
from typing import List, Dict, Any

class Dashboard:
    def __init__(self, system):
        self.system = system
        self.metrics_history: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        
    async def start(self):
        """Start the dashboard"""
        app = self.create_dashboard_app()
        runner = aiohttp.web.AppRunner(app)
        await runner.setup()
        site = aiohttp.web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        
        # Start metrics collection
        asyncio.create_task(self.collect_metrics())
        asyncio.create_task(self.process_alerts())

    def create_dashboard_app(self):
        """Create the dashboard web application"""
        app = aiohttp.web.Application()
        app.router.add_get('/', self.handle_root)
        app.router.add_get('/ws', self.handle_websocket)
        app.router.add_static('/static', 'dashboard/static')
        return app

    async def handle_root(self, request):
        """Serve the dashboard HTML"""
        return aiohttp.web.FileResponse('dashboard/index.html')

    async def handle_websocket(self, request):
        """Handle WebSocket connections"""
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        
        # Send initial data
        await ws.send_json({
            'type': 'initial_data',
            'metrics': self.metrics_history[-100:],
            'alerts': self.alert_history[-100:]
        })
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self.handle_ws_message(ws, msg.data)
        finally:
            return ws

    async def collect_metrics(self):
        """Continuously collect and store system metrics"""
        while True:
            metrics = await self.system.get_system_metrics()
            self.metrics_history.append(metrics)
            
            # Keep last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
                
            await asyncio.sleep(1)

    async def process_alerts(self):
        """Process and distribute system alerts"""
        while True:
            alert = await self.system.alert_queue.get()
            self.alert_history.append(alert)
            
            # Distribute alert to connected clients
            await self.broadcast_alert(alert)

    async def broadcast_alert(self, alert: Dict[str, Any]):
        """Broadcast alert to all connected WebSocket clients"""
        # Implementation depends on how we track connected clients
        pass

    async def handle_ws_message(self, ws: aiohttp.web.WebSocketResponse, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = message.json()
            if data['type'] == 'get_metrics':
                await ws.send_json({
                    'type': 'metrics_update',
                    'metrics': self.metrics_history[-100:]
                })
        except Exception as e:
            await ws.send_json({
                'type': 'error',
                'message': str(e)
            })
