"""Test para verificar que el parsing de comandos del BuilderBot funciona correctamente."""
from minecraft_framework.cli import parse_command


def test_builder_plan_list():
    """Test: \builder plan list"""
    result = parse_command("!builder plan list")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["list"] is True
    print("✓ builder plan list")


def test_builder_plan_set():
    """Test: \builder plan set little_house.csv"""
    result = parse_command("!builder plan set little_house.csv")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["plan set"] is True
    assert result["payload"]["args"][1] == "little_house.csv"
    print("✓ builder plan set little_house.csv")


def test_builder_bom():
    """Test: \builder bom"""
    result = parse_command("!builder bom")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["bom"] is True
    print("✓ builder bom")


def test_builder_build():
    """Test: \builder build"""
    result = parse_command("!builder build")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["build"] is True
    print("✓ builder build")


def test_builder_pause():
    """Test: \builder pause"""
    result = parse_command("!builder pause")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "pause"
    print("✓ builder pause")


def test_builder_resume():
    """Test: \builder resume"""
    result = parse_command("!builder resume")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "resume"
    print("✓ builder resume")


def test_builder_status():
    """Test: \builder status"""
    result = parse_command("!builder status")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "status"
    print("✓ builder status")


def test_builder_stop():
    """Test: \builder stop"""
    result = parse_command("!builder stop")
    assert result["type"] == "control"
    assert result["target"] == "BuilderBot"
    assert result["payload"]["cmd"] == "stop"
    print("✓ builder stop")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing BuilderBot CLI Commands")
    print("="*60 + "\n")

    test_builder_plan_list()
    test_builder_plan_set()
    test_builder_bom()
    test_builder_build()
    test_builder_pause()
    test_builder_resume()
    test_builder_status()
    test_builder_stop()

    print("\n" + "="*60)
    print("✅ All BuilderBot CLI tests passed!")
    print("="*60 + "\n")

