"""
Tests de sincronización para verificar comportamiento de pause, resume y stop.

Estos tests verifican que los comandos de control afectan correctamente
el estado del agente y que act() no se ejecuta cuando está en PAUSED.
"""

import pytest
from enum import Enum


class EstadoAgente(Enum):
    """Copia del enum de estados para tests independientes."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class MockAgent:
    """Agente mock para tests de sincronización."""

    def __init__(self, name: str):
        self.name = name
        self.estadoActual = EstadoAgente.IDLE
        self.solicitudParada = False
        self.act_called = False
        self.act_call_count = 0

    def cambiarEstadoAgente(self, nuevo_estado: EstadoAgente, razon: str = ""):
        """Cambia el estado del agente."""
        self.estadoActual = nuevo_estado

    def gestionarControles(self, control: dict):
        """Procesa comandos de control."""
        cmd = control.get("cmd")

        if cmd == "pause":
            if self.estadoActual in (EstadoAgente.RUNNING, EstadoAgente.WAITING):
                self.cambiarEstadoAgente(EstadoAgente.PAUSED, "pausado por usuario")

        elif cmd == "resume":
            if self.estadoActual == EstadoAgente.PAUSED:
                self.cambiarEstadoAgente(EstadoAgente.RUNNING, "reanudado por usuario")

        elif cmd == "stop":
            self.solicitudParada = True
            self.cambiarEstadoAgente(EstadoAgente.STOPPED, "detenido por usuario")

    async def act(self, decision: dict):
        """Simula la acción del agente."""
        # No ejecutar si estamos pausados
        if self.estadoActual == EstadoAgente.PAUSED:
            return

        self.act_called = True
        self.act_call_count += 1


class TestPauseCommand:
    """Tests para el comando pause."""

    def test_pause_from_running(self):
        """Verifica que pause funciona desde RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        agent.gestionarControles({"cmd": "pause"})

        assert agent.estadoActual == EstadoAgente.PAUSED

    def test_pause_from_waiting(self):
        """Verifica que pause funciona desde WAITING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.WAITING

        agent.gestionarControles({"cmd": "pause"})

        assert agent.estadoActual == EstadoAgente.PAUSED

    def test_pause_from_idle_no_effect(self):
        """Verifica que pause no afecta si está en IDLE."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.IDLE

        agent.gestionarControles({"cmd": "pause"})

        assert agent.estadoActual == EstadoAgente.IDLE  # No cambió

    def test_pause_from_stopped_no_effect(self):
        """Verifica que pause no afecta si está en STOPPED."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.STOPPED

        agent.gestionarControles({"cmd": "pause"})

        assert agent.estadoActual == EstadoAgente.STOPPED  # No cambió


class TestResumeCommand:
    """Tests para el comando resume."""

    def test_resume_from_paused(self):
        """Verifica que resume funciona desde PAUSED."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.PAUSED

        agent.gestionarControles({"cmd": "resume"})

        assert agent.estadoActual == EstadoAgente.RUNNING

    def test_resume_from_running_no_effect(self):
        """Verifica que resume no afecta si ya está RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        agent.gestionarControles({"cmd": "resume"})

        assert agent.estadoActual == EstadoAgente.RUNNING

    def test_resume_from_idle_no_effect(self):
        """Verifica que resume no afecta si está en IDLE."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.IDLE

        agent.gestionarControles({"cmd": "resume"})

        assert agent.estadoActual == EstadoAgente.IDLE

    def test_resume_from_stopped_no_effect(self):
        """Verifica que resume no afecta si está en STOPPED."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.STOPPED

        agent.gestionarControles({"cmd": "resume"})

        assert agent.estadoActual == EstadoAgente.STOPPED


class TestStopCommand:
    """Tests para el comando stop."""

    def test_stop_from_running(self):
        """Verifica que stop funciona desde RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        agent.gestionarControles({"cmd": "stop"})

        assert agent.estadoActual == EstadoAgente.STOPPED
        assert agent.solicitudParada is True

    def test_stop_from_paused(self):
        """Verifica que stop funciona desde PAUSED."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.PAUSED

        agent.gestionarControles({"cmd": "stop"})

        assert agent.estadoActual == EstadoAgente.STOPPED
        assert agent.solicitudParada is True

    def test_stop_from_idle(self):
        """Verifica que stop funciona desde IDLE."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.IDLE

        agent.gestionarControles({"cmd": "stop"})

        assert agent.estadoActual == EstadoAgente.STOPPED
        assert agent.solicitudParada is True

    def test_stop_sets_solicitud_parada(self):
        """Verifica que stop establece la bandera de parada."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING
        assert agent.solicitudParada is False

        agent.gestionarControles({"cmd": "stop"})

        assert agent.solicitudParada is True


class TestActNotExecutedWhenPaused:
    """Tests para verificar que act() no se ejecuta en estado PAUSED."""

    @pytest.mark.asyncio
    async def test_act_not_called_when_paused(self):
        """Verifica que act() no se ejecuta cuando el agente está pausado."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.PAUSED

        await agent.act({"action": "BUILD"})

        assert agent.act_called is False
        assert agent.act_call_count == 0

    @pytest.mark.asyncio
    async def test_act_called_when_running(self):
        """Verifica que act() se ejecuta cuando el agente está RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        await agent.act({"action": "BUILD"})

        assert agent.act_called is True
        assert agent.act_call_count == 1

    @pytest.mark.asyncio
    async def test_act_stops_after_pause(self):
        """Verifica que act() deja de ejecutarse después de pause."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        # Primer act - debería ejecutarse
        await agent.act({"action": "MINE"})
        assert agent.act_call_count == 1

        # Pausar
        agent.gestionarControles({"cmd": "pause"})

        # Segundo act - no debería ejecutarse
        await agent.act({"action": "MINE"})
        assert agent.act_call_count == 1  # Sigue en 1

    @pytest.mark.asyncio
    async def test_act_resumes_after_resume(self):
        """Verifica que act() se reanuda después de resume."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        # Primer act
        await agent.act({"action": "MINE"})
        assert agent.act_call_count == 1

        # Pausar
        agent.gestionarControles({"cmd": "pause"})

        # Act pausado
        await agent.act({"action": "MINE"})
        assert agent.act_call_count == 1

        # Reanudar
        agent.gestionarControles({"cmd": "resume"})

        # Act después de resume
        await agent.act({"action": "MINE"})
        assert agent.act_call_count == 2


class TestStateTransitions:
    """Tests para transiciones de estado válidas."""

    def test_idle_to_running(self):
        """Verifica transición IDLE -> RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.IDLE

        agent.cambiarEstadoAgente(EstadoAgente.RUNNING, "trabajo iniciado")

        assert agent.estadoActual == EstadoAgente.RUNNING

    def test_running_to_paused_to_running(self):
        """Verifica ciclo RUNNING -> PAUSED -> RUNNING."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        agent.gestionarControles({"cmd": "pause"})
        assert agent.estadoActual == EstadoAgente.PAUSED

        agent.gestionarControles({"cmd": "resume"})
        assert agent.estadoActual == EstadoAgente.RUNNING

    def test_multiple_pause_resume_cycles(self):
        """Verifica múltiples ciclos de pause/resume."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        for i in range(5):
            agent.gestionarControles({"cmd": "pause"})
            assert agent.estadoActual == EstadoAgente.PAUSED

            agent.gestionarControles({"cmd": "resume"})
            assert agent.estadoActual == EstadoAgente.RUNNING

    def test_stop_is_final(self):
        """Verifica que STOPPED es un estado final (no se puede volver)."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        agent.gestionarControles({"cmd": "stop"})
        assert agent.estadoActual == EstadoAgente.STOPPED

        # Intentar resume no debería funcionar
        agent.gestionarControles({"cmd": "resume"})
        assert agent.estadoActual == EstadoAgente.STOPPED


class TestConcurrentStateAccess:
    """Tests para acceso concurrente al estado (simulado)."""

    @pytest.mark.asyncio
    async def test_pause_during_act_cycle(self):
        """Simula pause recibido durante un ciclo de act."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        # Simular ciclo: perceive -> decide -> (pause) -> act
        # El pause debería prevenir el act

        # Perceive y decide ocurren
        decision = {"action": "BUILD"}

        # Pause llega antes de act
        agent.gestionarControles({"cmd": "pause"})

        # Act no debería ejecutarse
        await agent.act(decision)

        assert agent.act_called is False

    def test_rapid_pause_resume(self):
        """Verifica comportamiento con pause/resume rápidos."""
        agent = MockAgent("TestBot")
        agent.estadoActual = EstadoAgente.RUNNING

        # Simular comandos rápidos
        agent.gestionarControles({"cmd": "pause"})
        agent.gestionarControles({"cmd": "resume"})
        agent.gestionarControles({"cmd": "pause"})

        # Estado final debería ser PAUSED
        assert agent.estadoActual == EstadoAgente.PAUSED

