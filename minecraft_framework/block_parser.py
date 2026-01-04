"""Utilidades compartidas para interpretar bloques de Minecraft (mcpi).

Actualmente:
- `block_to_material(block_id)`: traducción de block_id (mcpi) a nombre lógico
  de material usado en requirements/BOM.
- `material_to_block(material_name)`: traducción inversa de nombre de material
  a block_id (mcpi) para construcción.

La lógica está externalizada para que la puedan reutilizar todos los bots.
"""

from __future__ import annotations

from typing import Dict, Optional

import mcpi.block as block


# IDs ambiguos en tu mcpi:
# - 95 aparece como STAINED_GLASS y también como BEDROCK_INVISIBLE.
# Para evitar confusiones, no lo mapeamos aquí.


def get_default_block_mapping() -> Dict[int, str]:
    """Devuelve el mapping por defecto block_id -> material.

    Basado en las definiciones reales de mcpi.block disponibles en Minecraft Pi Edition.
    Solo incluye bloques que realmente existen en la librería.
    """

    return {
        # Aire y terreno base
        block.AIR.id: "air",
        block.STONE.id: "stone",
        block.GRASS.id: "grass",
        block.DIRT.id: "dirt",
        block.COBBLESTONE.id: "cobblestone",
        block.BEDROCK.id: "bedrock",
        block.SAND.id: "sand",
        block.GRAVEL.id: "gravel",
        block.MOSS_STONE.id: "moss_stone",
        block.CLAY.id: "clay",
        block.FARMLAND.id: "farmland",

        # Madera y vegetación
        block.WOOD_PLANKS.id: "wood_planks",
        block.SAPLING.id: "sapling",
        block.WOOD.id: "wood",
        block.LEAVES.id: "leaves",
        block.GRASS_TALL.id: "grass_tall",
        block.COBWEB.id: "cobweb",

        # Minerales (mena)
        block.COAL_ORE.id: "coal_ore",
        block.IRON_ORE.id: "iron_ore",
        block.GOLD_ORE.id: "gold_ore",
        block.DIAMOND_ORE.id: "diamond_ore",
        block.REDSTONE_ORE.id: "redstone_ore",
        block.LAPIS_LAZULI_ORE.id: "lapis_ore",

        # Bloques de minerales
        block.IRON_BLOCK.id: "iron_block",
        block.GOLD_BLOCK.id: "gold_block",
        block.DIAMOND_BLOCK.id: "diamond_block",
        block.LAPIS_LAZULI_BLOCK.id: "lapis_block",

        # Construcción común
        block.BRICK_BLOCK.id: "bricks",
        block.STONE_BRICK.id: "stone_bricks",
        block.SANDSTONE.id: "sandstone",
        block.STONE_SLAB.id: "stone_slab",
        block.STONE_SLAB_DOUBLE.id: "stone_slab_double",
        block.GLASS.id: "glass",
        block.GLASS_PANE.id: "glass_pane",
        block.WOOL.id: "wool",
        block.BOOKSHELF.id: "bookshelf",
        block.TNT.id: "tnt",

        # Utilidad
        block.CHEST.id: "chest",
        block.CRAFTING_TABLE.id: "crafting_table",
        block.FURNACE_INACTIVE.id: "furnace",
        block.FURNACE_ACTIVE.id: "furnace_active",
        block.LADDER.id: "ladder",
        block.TORCH.id: "torch",
        block.FIRE.id: "fire",
        block.BED.id: "bed",

        # Vallas y puertas
        block.FENCE.id: "fence",
        block.FENCE_GATE.id: "fence_gate",
        block.DOOR_WOOD.id: "wood_door",
        block.DOOR_IRON.id: "iron_door",

        # Escaleras
        block.STAIRS_WOOD.id: "stairs_wood",
        block.STAIRS_COBBLESTONE.id: "stairs_cobblestone",

        # Bloques especiales
        block.GLOWSTONE_BLOCK.id: "glowstone",
        block.OBSIDIAN.id: "obsidian",
        block.GLOWING_OBSIDIAN.id: "glowing_obsidian",
        block.NETHER_REACTOR_CORE.id: "nether_reactor_core",
        block.BEDROCK_INVISIBLE.id: "bedrock_invisible",

        # Agua y lava
        block.WATER.id: "water",
        block.WATER_FLOWING.id: "water_flowing",
        block.WATER_STATIONARY.id: "water_stationary",
        block.LAVA.id: "lava",
        block.LAVA_FLOWING.id: "lava_flowing",
        block.LAVA_STATIONARY.id: "lava_stationary",

        # Hielo y nieve
        block.ICE.id: "ice",
        block.SNOW.id: "snow",
        block.SNOW_BLOCK.id: "snow_block",

        # Vegetación y flores
        block.CACTUS.id: "cactus",
        block.SUGAR_CANE.id: "sugar_cane",
        block.MELON.id: "melon",
        block.FLOWER_YELLOW.id: "flower_yellow",
        block.FLOWER_CYAN.id: "flower_cyan",
        block.MUSHROOM_BROWN.id: "mushroom_brown",
        block.MUSHROOM_RED.id: "mushroom_red",
    }


_DEFAULT_MAPPING: Dict[int, str] = get_default_block_mapping()

# Crear el mapping inverso: material -> block_id
_INVERSE_MAPPING: Dict[str, int] = {v: k for k, v in _DEFAULT_MAPPING.items()}

# Aliases comunes para materiales
_MATERIAL_ALIASES: Dict[str, str] = {
    "wood_planks": "planks",
    "brick_block": "bricks",
    "stone_brick": "stone_bricks",
}


def block_to_material(block_id: int, mapping: Optional[Dict[int, str]] = None) -> Optional[str]:
    """Convierte un `block_id` (mcpi) a un nombre lógico de material.

    Args:
        block_id: id numérica del bloque (mc.getBlock(...))
        mapping: mapping alternativo (por ejemplo, para tests)

    Returns:
        Nombre lógico (str) o None si no está mapeado.
    """
    m = _DEFAULT_MAPPING if mapping is None else mapping
    return m.get(block_id)


def material_to_block(material_name: str, mapping: Optional[Dict[str, int]] = None) -> Optional[int]:
    """Convierte un nombre de material a `block_id` (mcpi).

    Args:
        material_name: Nombre lógico del material (ej: "stone", "planks", "gold_block")
        mapping: mapping alternativo (por ejemplo, para tests)

    Returns:
        Block ID (int) o None si no está mapeado.
    """
    m = _INVERSE_MAPPING if mapping is None else mapping

    # Intentar obtener directamente
    block_id = m.get(material_name)
    if block_id is not None:
        return block_id

    # Intentar con aliases
    alias = _MATERIAL_ALIASES.get(material_name)
    if alias:
        return m.get(alias)

    # No encontrado
    return None


