"""Utilidades compartidas para interpretar bloques de Minecraft (mcpi).

Actualmente:
- `block_to_material(block_id)`: traducción de block_id (mcpi) a nombre lógico
  de material usado en requirements/BOM.

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

    Basado en las constantes disponibles en tu `mcpi.block` (108 constantes, ver
    `list_mcpi_blocks.py`).
    """

    return {
        # Terreno base
        block.STONE.id: "stone",
        block.COBBLESTONE.id: "cobblestone",
        block.DIRT.id: "dirt",
        block.GRASS.id: "grass",
        block.SAND.id: "sand",
        block.GRAVEL.id: "gravel",
        block.MOSS_STONE.id: "moss_stone",

        # Madera / árbol
        block.WOOD.id: "wood",
        block.WOOD_PLANKS.id: "planks",
        block.LEAVES.id: "leaves",
        block.LEAVES2.id: "leaves",
        block.SAPLING.id: "sapling",

        # Minerales (mena + bloques)
        block.COAL_ORE.id: "coal_ore",
        block.IRON_ORE.id: "iron_ore",
        block.GOLD_ORE.id: "gold_ore",
        block.DIAMOND_ORE.id: "diamond_ore",
        block.REDSTONE_ORE.id: "redstone_ore",
        block.LAPIS_LAZULI_ORE.id: "lapis_ore",
        block.EMERALD_ORE.id: "emerald_ore",

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
        block.WOODEN_SLAB.id: "wood_slab",
        block.CLAY.id: "clay",
        block.GLASS.id: "glass",
        block.GLASS_PANE.id: "glass_pane",
        block.WOOL.id: "wool",
        block.BOOKSHELF.id: "bookshelf",
        block.TNT.id: "tnt",

        # Utilidad
        block.CHEST.id: "chest",
        block.CRAFTING_TABLE.id: "crafting_table",
        block.FURNACE_INACTIVE.id: "furnace",
        block.FURNACE_ACTIVE.id: "furnace",
        block.LADDER.id: "ladder",

        # Vallas/puertas
        block.FENCE.id: "fence",
        block.FENCE_ACACIA.id: "fence_acacia",
        block.FENCE_BIRCH.id: "fence_birch",
        block.FENCE_SPRUCE.id: "fence_spruce",
        block.FENCE_JUNGLE.id: "fence_jungle",
        block.FENCE_DARK_OAK.id: "fence_dark_oak",
        block.FENCE_GATE.id: "fence_gate",
        block.TRAPDOOR.id: "trapdoor",
        block.TRAPDOOR_IRON.id: "iron_trapdoor",
        block.DOOR_WOOD.id: "wood_door",
        block.DOOR_IRON.id: "iron_door",
        block.DOOR_ACACIA.id: "acacia_door",
        block.DOOR_BIRCH.id: "birch_door",
        block.DOOR_SPRUCE.id: "spruce_door",
        block.DOOR_JUNGLE.id: "jungle_door",
        block.DOOR_DARK_OAK.id: "dark_oak_door",

        # Escaleras
        block.STAIRS_WOOD.id: "stairs_wood",
        block.STAIRS_COBBLESTONE.id: "stairs_cobblestone",
        block.STAIRS_BRICK.id: "stairs_brick",
        block.STAIRS_STONE_BRICK.id: "stairs_stone_brick",
        block.STAIRS_SANDSTONE.id: "stairs_sandstone",

        # Nether / End
        block.NETHERRACK.id: "netherrack",
        block.SOUL_SAND.id: "soul_sand",
        block.NETHER_BRICK.id: "nether_brick",
        block.FENCE_NETHER_BRICK.id: "nether_brick_fence",
        block.STAIRS_NETHER_BRICK.id: "stairs_nether_brick",
        block.GLOWSTONE_BLOCK.id: "glowstone",
        block.OBSIDIAN.id: "obsidian",
        block.GLOWING_OBSIDIAN.id: "glowing_obsidian",
        block.END_STONE.id: "end_stone",

        # Agua/lava/hielo/nieve
        block.WATER.id: "water",
        block.WATER_FLOWING.id: "water",
        block.WATER_STATIONARY.id: "water",
        block.LAVA.id: "lava",
        block.LAVA_FLOWING.id: "lava",
        block.LAVA_STATIONARY.id: "lava",
        block.ICE.id: "ice",
        block.SNOW.id: "snow",
        block.SNOW_BLOCK.id: "snow_block",

        # Vegetación
        block.CACTUS.id: "cactus",
        block.SUGAR_CANE.id: "sugar_cane",
        block.MELON.id: "melon",
        block.PUMPKIN.id: "pumpkin",
        block.LIT_PUMPKIN.id: "lit_pumpkin",
        block.MUSHROOM_BROWN.id: "mushroom_brown",
        block.MUSHROOM_RED.id: "mushroom_red",
        block.MYCELIUM.id: "mycelium",

        # Otros
        block.BEDROCK.id: "bedrock",
    }


_DEFAULT_MAPPING: Dict[int, str] = get_default_block_mapping()


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

