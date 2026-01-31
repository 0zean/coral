import threading
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ThreadConfig:
    """Shared configuration for worker threads."""

    trigger_key: str = "shift"
    rcs_amount: float = 0.0
    enable_trigger: bool = False
    enable_rcs: bool = False
    enable_esp: bool = False


class ThreadManager:
    """Manages specific threads with stop events."""

    def __init__(self) -> None:
        self.threads: dict[str, threading.Thread] = {}
        self.stop_events: dict[str, threading.Event] = {}
        self.config = ThreadConfig()

    def start_thread(self, name: str, target: Callable, args: tuple = ()) -> None:
        """Starts a thread if it's not already running."""
        if name in self.threads and self.threads[name].is_alive():
            return

        stop_event = threading.Event()
        self.stop_events[name] = stop_event

        # Pass stop_event and config to the target function
        # The target function must accept (stop_event, config, *other_args)
        thread = threading.Thread(target=target, args=(stop_event, self.config) + args, daemon=True)
        self.threads[name] = thread
        thread.start()

    def stop_thread(self, name: str) -> None:
        """Signals a thread to stop and waits for it to join."""
        if name in self.stop_events:
            self.stop_events[name].set()

        if name in self.threads:
            thread = self.threads[name]
            if thread.is_alive():
                # specific for ESP which might be in a render loop or something blocking
                thread.join(timeout=1.0)
            del self.threads[name]

        if name in self.stop_events:
            del self.stop_events[name]

    def stop_all(self) -> None:
        """Stops all managed threads."""
        for name in list(self.threads.keys()):
            self.stop_thread(name)

    def is_running(self, name: str) -> bool:
        return name in self.threads and self.threads[name].is_alive()
