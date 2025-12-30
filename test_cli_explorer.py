"""Test para verificar que el parsing de comandos del ExplorerBot funciona correctamente."""
from minecraft_framework.cli import parse_command


def test_explorer_start_with_coords():
    """Test: $explorer start x=100 z=200"""
    result = parse_command("$explorer start x=100 z=200")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["start"]["x"] == 100
    assert result["payload"]["args"]["start"]["z"] == 200
    print("✓ explorer start x=100 z=200")


def test_explorer_start_with_range():
    """Test: $explorer start x=100 z=200 range=10"""
    result = parse_command("$explorer start x=100 z=200 range=10")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["start"]["x"] == 100
    assert result["payload"]["args"]["start"]["z"] == 200
    assert result["payload"]["args"]["start"]["range"] == 10
    print("✓ explorer start x=100 z=200 range=10")


def test_explorer_stop():
    """Test: $explorer stop"""
    result = parse_command("$explorer stop")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "stop"
    print("✓ explorer stop")


def test_explorer_set_range():
    """Test: $explorer set range 15"""
    result = parse_command("$explorer set range 15")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "update"
    assert result["payload"]["args"]["range"] == 15
    print("✓ explorer set range 15")


def test_explorer_status():
    """Test: $explorer status"""
    result = parse_command("$explorer status")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "status"
    print("✓ explorer status")


def test_explorer_pause():
    """Test: $explorer pause"""
    result = parse_command("$explorer pause")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "pause"
    print("✓ explorer pause")


def test_explorer_resume():
    """Test: $explorer resume"""
    result = parse_command("$explorer resume")
    assert result["type"] == "control"
    assert result["target"] == "ExplorerBot"
    assert result["payload"]["cmd"] == "resume"
    print("✓ explorer resume")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Testing ExplorerBot CLI Commands")
    print("="*60 + "\n")

    test_explorer_start_with_coords()
    test_explorer_start_with_range()
    test_explorer_stop()
    test_explorer_set_range()
    test_explorer_status()
    test_explorer_pause()
    test_explorer_resume()

    print("\n" + "="*60)
    print("✅ All ExplorerBot CLI tests passed!")
    print("="*60 + "\n")

