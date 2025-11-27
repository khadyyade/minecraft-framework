# En cada carpeta de un proyecto python hay que crear este archivo
# El archivo __init__ convierte la carpeta minecraft_framework en un paquete de Python
# Y esto nos permite hacer imports como los que hacemos desde los agentes
# Paquetes en esta carpeta: baseAgent, messages, cli, registry y la carpeta agents

__all__ = ["baseAgent", "messages", "agents", "cli", "registry"]