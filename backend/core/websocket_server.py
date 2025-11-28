"""
Servidor WebSocket para notificaciones en tiempo real
"""
import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
import sqlite3
import threading
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.user_clients: Dict[int, Set[websockets.WebSocketServerProtocol]] = {}
        self.running = False
        
    async def register_client(self, websocket, path):
        """Registrar nuevo cliente WebSocket"""
        self.clients.add(websocket)
        logger.info(f"Cliente conectado: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    await self.send_error(websocket, "Mensaje JSON inválido")
                except Exception as e:
                    logger.error(f"Error procesando mensaje: {e}")
                    await self.send_error(websocket, "Error interno del servidor")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def handle_message(self, websocket, data):
        """Manejar mensajes del cliente"""
        message_type = data.get('type')
        
        if message_type == 'auth':
            user_id = data.get('user_id')
            if user_id:
                if user_id not in self.user_clients:
                    self.user_clients[user_id] = set()
                self.user_clients[user_id].add(websocket)
                await self.send_success(websocket, "Autenticado correctamente")
        
        elif message_type == 'ping':
            await self.send_pong(websocket)
        
        else:
            await self.send_error(websocket, f"Tipo de mensaje desconocido: {message_type}")
    
    async def unregister_client(self, websocket):
        """Desregistrar cliente"""
        self.clients.discard(websocket)
        
        # Remover de user_clients
        for user_id, clients in self.user_clients.items():
            clients.discard(websocket)
            if not clients:
                del self.user_clients[user_id]
        
        logger.info(f"Cliente desconectado: {websocket.remote_address}")
    
    async def send_error(self, websocket, message):
        """Enviar mensaje de error"""
        await websocket.send(json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_success(self, websocket, message):
        """Enviar mensaje de éxito"""
        await websocket.send(json.dumps({
            'type': 'success',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_pong(self, websocket):
        """Responder ping con pong"""
        await websocket.send(json.dumps({
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Enviar mensaje a todos los clientes conectados"""
        if self.clients:
            message['timestamp'] = datetime.now().isoformat()
            message_str = json.dumps(message)
            
            # Enviar a todos los clientes
            disconnected = set()
            for client in self.clients.copy():
                try:
                    await client.send(message_str)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Limpiar clientes desconectados
            for client in disconnected:
                await self.unregister_client(client)
    
    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]):
        """Enviar mensaje a un usuario específico"""
        if user_id in self.user_clients:
            message['timestamp'] = datetime.now().isoformat()
            message_str = json.dumps(message)
            
            # Enviar a todos los clientes del usuario
            disconnected = set()
            for client in self.user_clients[user_id].copy():
                try:
                    await client.send(message_str)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Limpiar clientes desconectados
            for client in disconnected:
                await self.unregister_client(client)
    
    async def broadcast_to_admins(self, message: Dict[str, Any]):
        """Enviar mensaje solo a administradores"""
        # Obtener IDs de administradores desde la base de datos
        try:
            conn = sqlite3.connect('auth_database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1")
            admin_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for admin_id in admin_ids:
                await self.broadcast_to_user(admin_id, message)
        except Exception as e:
            logger.error(f"Error obteniendo administradores: {e}")
    
    def start_server(self):
        """Iniciar servidor WebSocket"""
        self.running = True
        logger.info(f"Iniciando servidor WebSocket en {self.host}:{self.port}")
        
        # Iniciar servidor en hilo separado
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_server = websockets.serve(self.register_client, self.host, self.port)
            loop.run_until_complete(start_server)
            loop.run_forever()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        return server_thread
    
    def stop_server(self):
        """Detener servidor WebSocket"""
        self.running = False
        logger.info("Servidor WebSocket detenido")

# Instancia global del servidor
websocket_server = WebSocketServer()

# Funciones de utilidad para enviar notificaciones
def send_scraping_notification(message: str, status: str = "info"):
    """Enviar notificación sobre scraping"""
    asyncio.create_task(websocket_server.broadcast_to_all({
        'type': 'scraping_update',
        'message': message,
        'status': status
    }))

def send_payment_notification(user_id: int, message: str, status: str = "info"):
    """Enviar notificación de pago a usuario específico"""
    asyncio.create_task(websocket_server.broadcast_to_user(user_id, {
        'type': 'payment_update',
        'message': message,
        'status': status
    }))

def send_admin_notification(message: str, status: str = "info"):
    """Enviar notificación solo a administradores"""
    asyncio.create_task(websocket_server.broadcast_to_admins({
        'type': 'admin_notification',
        'message': message,
        'status': status
    }))

def send_system_notification(message: str, status: str = "info"):
    """Enviar notificación del sistema a todos"""
    asyncio.create_task(websocket_server.broadcast_to_all({
        'type': 'system_notification',
        'message': message,
        'status': status
    }))

if __name__ == "__main__":
    # Iniciar servidor WebSocket
    server_thread = websocket_server.start_server()
    
    try:
        # Mantener el servidor corriendo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        websocket_server.stop_server()
        print("Servidor WebSocket detenido")


















