import asyncio
import websockets
import socket
import os
from getmac import get_mac_address
import json
import subprocess
from websockets.exceptions import InvalidMessage
import logging
from logging.handlers import RotatingFileHandler

# Инициализация логгера
logger = logging.getLogger("client")
logger.setLevel(logging.DEBUG)

# Создание обработчика для ротации логов при достижении 10 МБ
log_handler = RotatingFileHandler("strikeclient.log", maxBytes=10 * 1024 * 1024, backupCount=5)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)

# Добавление обработчика к логгеру
logger.addHandler(log_handler)

async def send_ip_and_mac_address():
    uri = "ws://192.168.88.252:8000/ws/"  # Замените на фактический URI WebSocket
    ip_address = get_ip_address()
    mac_address = get_mac_address(ip=ip_address)
    data = {"mac": mac_address}
    
    while True:
        try:
            async with websockets.connect(f"{uri}{ip_address}") as websocket:
                await websocket.send(json.dumps(data))
                # Ждем сообщений от сервера
                while True:
                    data = None
                    message_text = await websocket.recv()
                    message = json.loads(message_text)
                    command_type = message.get("type")
                    command_data = message.get("command")
                    command_log = message.get("log", False)
                    if command_type == "cmd":
                        try:
                            result = subprocess.check_output(command_data, shell=True, text=True, encoding='cp866')
                        except subprocess.CalledProcessError as err:
                            logger.error(f"Error executing command: {command_data}. Error: {err}")
                            result = str(err)
                    elif command_type == "ps":
                        try:
                            result = subprocess.check_output(["powershell", command_data], shell=True, text=True, encoding='cp866')
                        except subprocess.CalledProcessError as err:
                            logger.error(f"Error executing PowerShell command: {command_data}. Error: {err}")
                            result = str(err)
                    logger.error(f"Выполнена {command_type} : {command_data} \n Результат: {result}")
                    if command_log == True:
                        data = {'log': result}
                        await websocket.send(json.dumps(data))
                    
        except (ConnectionRefusedError, InvalidMessage, TimeoutError, websockets.exceptions.ConnectionClosed) as err:
            #logger.error(f"Error: {ex}. Reconnecting in 10 seconds...")
            await websocket.close()  
            await asyncio.sleep(10)
        except Exception as err:
            logger.error(err)
            await websocket.close()  
            break
        finally:
            await websocket.close()  

def get_ip_address():
    # Получаем локальный IP-адрес машины
    ip_address = socket.gethostbyname(socket.gethostname())
    return ip_address

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(send_ip_and_mac_address())
