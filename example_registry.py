"""
Ejemplo de uso del registro dinámico de agentes.

Demuestra cómo descubrir y cargar agentes automáticamente sin imports manuales.
"""

from minecraft_framework.registry import get_registry

def main():
    print("=" * 60)
    print("Sistema de Registro Dinámico de Agentes")
    print("=" * 60)
    
    # Obtener el registro global
    registry = get_registry()
    
    # Listar todos los agentes descubiertos
    print("\nAgentes registrados:")
    for agent_name in registry.list_agents():
        print(f"  • {agent_name}")
    
    # Listar todas las estrategias descubiertas (si existen)
    print("\nEstrategias registradas:")
    strategies = registry.list_strategies()
    if strategies:
        for strategy_name in strategies:
            print(f"  • {strategy_name}")
    else:
        print("  (ninguna estrategia encontrada)")
    
    # Ejemplo: obtener una clase de agente dinámicamente
    print("\n" + "=" * 60)
    print("Ejemplo: Obtener ExplorerBot dinámicamente")
    print("=" * 60)
    
    ExplorerBotClass = registry.get_agent("ExplorerBot")
    if ExplorerBotClass:
        print(f"  ✓ ExplorerBot encontrado: {ExplorerBotClass}")
        print(f"  Módulo: {ExplorerBotClass.__module__}")
        print(f"  Métodos disponibles:")
        for method in ['perceive', 'decide', 'act', 'iniciarAgente']:
            if hasattr(ExplorerBotClass, method):
                print(f"    • {method}()")
    else:
        print("  ✗ ExplorerBot no encontrado")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
