# En cada carpeta de un proyecto python hay que crear este archivo
# El archivo __init__ convierte la carpeta agents en un paquete de Python
# Y esto nos permite hacer imports, como los que hacemos desde main.py
# Paquete de agentes en esta carpeta: ExplorerBot, MinerBot, BuilderBot

# Importante, una decisión de diseño que hemos tomado es definir una función "generica"
# que permita inicializar todos los agentes con los mismos parámetros
# No es una interfaz ni una clase abstracta, solo hemos forzado que todas sean iguales

# agent_process_main(in_queue, q_explorer, q_miner, q_builder, **kwargs)

__all__ = ["explorer", "miner", "builder"]
