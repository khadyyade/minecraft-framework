import os
import csv
import time
from mcpi.minecraft import Minecraft
from mcpi import block

BLOCK_MAP = {
    "air": block.AIR.id, "stone": block.STONE.id, "grass": block.GRASS.id,
    "dirt": block.DIRT.id, "cobblestone": block.COBBLESTONE.id, "bedrock": block.BEDROCK.id,
    "sand": block.SAND.id, "gravel": block.GRAVEL.id, "moss_stone": block.MOSS_STONE.id,
    "clay": block.CLAY.id, "farmland": block.FARMLAND.id,
    "wood_planks": block.WOOD_PLANKS.id, "planks": block.WOOD_PLANKS.id,
    "sapling": block.SAPLING.id, "wood": block.WOOD.id, "leaves": block.LEAVES.id,
    "grass_tall": block.GRASS_TALL.id, "cobweb": block.COBWEB.id,
    "coal_ore": block.COAL_ORE.id, "iron_ore": block.IRON_ORE.id,
    "gold_ore": block.GOLD_ORE.id, "diamond_ore": block.DIAMOND_ORE.id,
    "redstone_ore": block.REDSTONE_ORE.id, "lapis_ore": block.LAPIS_LAZULI_ORE.id,
    "iron_block": block.IRON_BLOCK.id, "gold_block": block.GOLD_BLOCK.id,
    "diamond_block": block.DIAMOND_BLOCK.id, "lapis_block": block.LAPIS_LAZULI_BLOCK.id,
    "bricks": block.BRICK_BLOCK.id, "brick_block": block.BRICK_BLOCK.id,
    "stone_bricks": block.STONE_BRICK.id, "stone_brick": block.STONE_BRICK.id,
    "sandstone": block.SANDSTONE.id, "stone_slab": block.STONE_SLAB.id,
    "stone_slab_double": block.STONE_SLAB_DOUBLE.id, "glass": block.GLASS.id,
    "glass_pane": block.GLASS_PANE.id, "wool": block.WOOL.id,
    "bookshelf": block.BOOKSHELF.id, "tnt": block.TNT.id,
    "chest": block.CHEST.id, "crafting_table": block.CRAFTING_TABLE.id,
    "furnace": block.FURNACE_INACTIVE.id, "furnace_active": block.FURNACE_ACTIVE.id,
    "ladder": block.LADDER.id, "torch": block.TORCH.id, "fire": block.FIRE.id, "bed": block.BED.id,
    "fence": block.FENCE.id, "fence_gate": block.FENCE_GATE.id,
    "wood_door": block.DOOR_WOOD.id, "iron_door": block.DOOR_IRON.id,
    "stairs_wood": block.STAIRS_WOOD.id, "stairs_cobblestone": block.STAIRS_COBBLESTONE.id,
    "glowstone": block.GLOWSTONE_BLOCK.id, "obsidian": block.OBSIDIAN.id,
    "glowing_obsidian": block.GLOWING_OBSIDIAN.id,
    "nether_reactor_core": block.NETHER_REACTOR_CORE.id,
    "bedrock_invisible": block.BEDROCK_INVISIBLE.id,
    "water": block.WATER.id, "water_flowing": block.WATER_FLOWING.id,
    "water_stationary": block.WATER_STATIONARY.id, "lava": block.LAVA.id,
    "lava_flowing": block.LAVA_FLOWING.id, "lava_stationary": block.LAVA_STATIONARY.id,
    "ice": block.ICE.id, "snow": block.SNOW.id, "snow_block": block.SNOW_BLOCK.id,
    "cactus": block.CACTUS.id, "sugar_cane": block.SUGAR_CANE.id, "melon": block.MELON.id,
    "flower_yellow": block.FLOWER_YELLOW.id, "flower_cyan": block.FLOWER_CYAN.id,
    "mushroom_brown": block.MUSHROOM_BROWN.id, "mushroom_red": block.MUSHROOM_RED.id,
}


def material_to_block_id(name):
    return BLOCK_MAP.get(name.lower(), block.STONE.id)


def load_csv_template(path):
    blocks = []
    with open(path, 'r') as f:
        for row in csv.DictReader(f):
            blocks.append({
                'x': int(row['x']), 'z': int(row['z']),
                'layer': int(row['layer']), 'block_type': row['block_type']
            })
    return blocks


def get_structure_width(blocks):
    if not blocks:
        return 0
    return max(b['x'] for b in blocks) - min(b['x'] for b in blocks) + 1


def build_structure(mc, blocks, sx, sy, sz):
    for b in sorted(blocks, key=lambda x: x['layer']):
        mc.setBlock(sx + b['x'], sy + b['layer'], sz + b['z'], material_to_block_id(b['block_type']))
        time.sleep(0.01)


def main():
    try:
        mc = Minecraft.create()
    except Exception as e:
        print(f"Error: {e}")
        return

    pos = mc.player.getTilePos()
    structures_dir = "minecraft_framework/estructurasTests"

    if not os.path.exists(structures_dir):
        print(f"Carpeta no existe: {structures_dir}")
        return

    csv_files = [f for f in os.listdir(structures_dir) if f.endswith('.csv')]
    if not csv_files:
        print("No hay archivos CSV")
        return

    current_x = pos.x - 16
    spacing = 10

    for csv_file in csv_files:
        try:
            blocks = load_csv_template(os.path.join(structures_dir, csv_file))
            build_structure(mc, blocks, current_x, pos.y, pos.z + 1)
            current_x += get_structure_width(blocks) + spacing
            print(f"OK: {csv_file}")
        except Exception as e:
            print(f"Error {csv_file}: {e}")

    print("Completado")


if __name__ == "__main__":
    main()
