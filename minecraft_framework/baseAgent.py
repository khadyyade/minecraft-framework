"""
Base Agent Module

This module provides a base class for all agents in the Minecraft framework.
It implements common functionality for agent communication, state management,
and the perception-decision-action cycle.

The BaseAgent class serves as a parent class that each specific agent extends.
It provides utility functions for:
- Message sending (enviarMensaje)
- Control command handling (gestionarControles)
- Message reading (leerMensaje)
- Agent initialization and execution (iniciarAgente)

Communication between processes is managed using multiprocessing.Queue.
"""

import asyncio
from enum import Enum
from multiprocessing import Queue
from typing import Dict, Any, Optional
import time
import json


class AgentState(Enum):
    """
    Enumeration of possible agent states.
    
    These states represent the different operational modes of an agent:
    - IDLE: Agent is initialized but not actively working
    - RUNNING: Agent is actively executing its tasks
    - PAUSED: Agent execution is temporarily suspended
    - WAITING: Agent is waiting for a condition or resource
    - STOPPED: Agent has been stopped and will not resume
    - ERROR: Agent encountered an error during execution
    """
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING = "WAITING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class BaseAgent:
    """
    Base class for all agents in the Minecraft framework.
    
    This class implements common functionality for agent communication,
    state management, and the perception-decision-action cycle.
    Specific agent types (Explorer, Miner, Builder) should inherit from
    this class and implement the perceive, decide, and act methods.
    """

    def __init__(self, name: str, in_queue: Queue, q_explorer: Queue, q_miner: Queue, q_builder: Queue):
        """
        Initialize a new agent with communication queues and default state.
        
        Args:
            name: Identifier for this agent
            in_queue: Queue for receiving messages
            q_explorer: Queue for sending messages to the explorer agent
            q_miner: Queue for sending messages to the miner agent
            q_builder: Queue for sending messages to the builder agent
        """
        # Agent identifier
        self.name = name
        # Queue for receiving messages
        self.in_queue = in_queue
        
        # Store references to each agent's queue
        self.q_explorer = q_explorer
        self.q_miner = q_miner
        self.q_builder = q_builder
        
        # Dictionary mapping agent names to their respective queues
        self.out_queues = {
            "ExplorerBot": q_explorer,
            "MinerBot": q_miner,
            "BuilderBot": q_builder
        }
        
        # Initial agent state
        self.state = AgentState.IDLE
        # Timestamp of the last state transition
        self._last_transition = time.time()
        # Flag to indicate if the agent should stop execution
        self._stop_requested = False


    # Utility Methods

    def estadoActual(self, msg: str):
        """
        Print a message with timestamp, agent name, and current state.
        
        This method formats and prints log messages with consistent formatting,
        including the current timestamp, agent name, and state.
        
        Args:
            msg: The message to log
        """
        # Format current time as a readable timestamp
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # Print formatted message with timestamp, agent name, and state
        print(f"[{ts}] [{self.name}] [{self.state.value}] {msg}")


    def enviarMensaje(self, target: str, message: Dict[str, Any]):
        """
        Send a message to a target agent.
        
        This method looks up the appropriate queue for the target agent
        and sends the message as JSON. If the target is not found or
        JSON conversion fails, appropriate error handling is performed.
        
        Args:
            target: Name of the target agent (e.g., "ExplorerBot")
            message: Dictionary containing the message to send
        """
        # Get the queue for the target agent
        q = self.out_queues.get(target)
        if q is None:
            # Log warning if target agent's queue is not found
            self.estadoActual(f"Warning: out_queue for '{target}' not found. Message dropped.")
            return
            
        # Try to convert message to JSON before sending
        try:
            q.put_nowait(json.dumps(message))
        except Exception:
            # If JSON conversion fails, send the raw message
            q.put_nowait(message)

    def cambiarEstadoAgente(self, new_state: AgentState, reason: str = ""):
        """
        Change the agent's state and log the transition.
        
        This method updates the agent's state, records the transition time,
        and logs the state change with the provided reason.
        
        Args:
            new_state: The new state to transition to
            reason: Optional explanation for the state change
        """
        # Store the previous state for logging
        prev = self.state
        # Update to the new state
        self.state = new_state
        # Record the transition time
        self._last_transition = time.time()
        # Log the state transition with reason
        self.estadoActual(f"State transition {prev.value} -> {new_state.value}. {reason}")

    def gestionarControles(self, control: Dict[str, Any]):
        """
        Process control commands and change the agent's state accordingly.
        
        This method handles standard control commands:
        - pause: Pause a running agent
        - resume: Resume a paused agent
        - stop: Stop the agent completely
        - update: Update agent parameters
        
        Args:
            control: Dictionary with structure { 'cmd': 'pause'|'resume'|'stop'|'update', 'args': {...} }
        """
        # Extract the command from the control message
        cmd = control.get("cmd")
        
        # Handle pause command - only if agent is currently running
        if cmd == "pause":
            if self.state == AgentState.RUNNING:
                self.cambiarEstadoAgente(AgentState.PAUSED, reason="paused by control")
        
        # Handle resume command - only if agent is currently paused
        elif cmd == "resume":
            if self.state == AgentState.PAUSED:
                self.cambiarEstadoAgente(AgentState.RUNNING, reason="resumed by control")
        
        # Handle stop command - always stops the agent
        elif cmd == "stop":
            self.estadoActual("Stop requested")
            self._stop_requested = True
            self.cambiarEstadoAgente(AgentState.STOPPED, reason="stopped by control")
        
        # Handle update command - for updating agent parameters
        elif cmd == "update":
            # TODO: procesar actualizaciones de parámetros
            self.estadoActual(f"Received update: {control.get('args')}")
        
        # Handle unknown commands
        else:
            self.estadoActual(f"Unknown control command: {cmd}")

    async def leerMensaje(self):
        """
        Read a message from the input queue without blocking the asyncio loop.
        
        This method uses asyncio's run_in_executor to read from the queue
        in a non-blocking way. It also attempts to parse JSON messages.
        
        Returns:
            The parsed message (as a dict if JSON), or None if no message is available
        """
        # Get the current asyncio event loop
        loop = asyncio.get_running_loop()
        
        # Try to get a message from the queue without blocking
        try:
            raw = await loop.run_in_executor(None, self.obtenerMensajeNoWait)
        except asyncio.CancelledError:
            # Re-raise CancelledError to allow proper asyncio cancellation
            raise
        except Exception:
            # Handle any other exceptions by returning None
            raw = None
            
        # If no message was received, return None
        if raw is None:
            return None
            
        # Try to parse the message as JSON
        try:
            msg = json.loads(raw)
        except Exception:
            # If JSON parsing fails, return the raw message
            msg = raw
            
        return msg


    def obtenerMensajeNoWait(self):
        """
        Try to get a message from the input queue without waiting.
        
        This is a non-blocking method that attempts to retrieve a message
        from the queue immediately, returning None if the queue is empty.
        
        Returns:
            The message from the queue, or None if the queue is empty
        """
        try:
            # Try to get a message without waiting
            return self.in_queue.get_nowait()
        except Exception:
            # Return None if the queue is empty or any other error occurs
            return None

    async def iniciarAgente(self):
        """
        Initialize the agent, change state to RUNNING, and execute the main task.
        
        This method starts the agent's main execution loop by:
        1. Changing the agent's state to RUNNING
        2. Executing the perception-decision-action cycle
        3. Handling any exceptions that occur during execution
        
        Any unhandled exceptions will change the agent's state to ERROR.
        """
        # Change state to RUNNING and log the transition
        self.cambiarEstadoAgente(AgentState.RUNNING, reason="Iniciando bucle principal")
        
        try:
            # Execute the main task loop
            await self._run_task()
        except Exception as e:
            # Log any unhandled exceptions
            self.estadoActual(f"Unhandled error in run: {e}")
            # Change state to ERROR
            self.cambiarEstadoAgente(AgentState.ERROR, reason=str(e))

    async def _run_task(self):
        """
        Implement the perception-decision-action cycle.
        
        This method runs the main agent loop that:
        1. Perceives the environment
        2. Makes decisions based on perceptions
        3. Acts on those decisions
        
        Subclasses can override this completely or implement the
        perceive/decide/act methods.
        """
        # Continue running until stop is requested
        while not self._stop_requested:
            # Execute the perception-decision-action cycle
            perception = await self.perceive()
            decision = await self.decide(perception)
            await self.act(decision)
            # Small delay to prevent busy-waiting
            await asyncio.sleep(0.1)

    async def perceive(self) -> Dict[str, Any]:
        """
        PERCEPTION phase: Read incoming messages and environment state.
        
        This method should be implemented by subclasses to gather information
        from the environment, including messages from other agents and
        observations of the world state.
        
        Returns:
            Dictionary containing the current perception (messages, state, etc.)
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement perceive()")

    async def decide(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """
        DECISION phase: Process perception and determine what to do.
        
        This method should be implemented by subclasses to analyze the
        current perception and make decisions about what actions to take.
        
        Args:
            perception: Data returned by the perceive() method
            
        Returns:
            Dictionary containing the decision/action to take
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement decide()")

    async def act(self, decision: Dict[str, Any]):
        """
        ACTION phase: Execute the decision made.
        
        This method should be implemented by subclasses to carry out
        the actions determined in the decide phase, affecting the
        environment or communicating with other agents.
        
        Args:
            decision: Data returned by the decide() method
            
        Raises:
            NotImplementedError: This method must be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement act()")
