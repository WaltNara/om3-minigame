"""Executable playback contract for the future native worker.

Commands are reservations, not sound output. The backend must acknowledge STOP
only after DMA has stopped reading; both STOP and PLAY carry generation IDs.
This reference is tested on the host and is not installed on the camera.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    op: str
    generation: int
    offset_frames: int = 0


class Retrigger:
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.sequence = 0
        self.active = None
        self.pending = None
        self.stopping = False

    def shot(self):
        """Accepted, permitted exposure; newest request replaces any pending one."""
        if not self.enabled:
            return []
        self.sequence += 1
        generation = self.sequence
        if self.active is None:
            self.active = generation
            return [Command('play', generation)]
        self.pending = generation
        if self.stopping:
            return []
        self.stopping = True
        return [Command('stop', self.active)]

    def set_enabled(self, enabled):
        """Silent is the default; turning Off also cancels a pending restart."""
        self.enabled = bool(enabled)
        return [] if self.enabled else self.cancel()

    def ended(self, generation):
        """Native end/stop completion: this generation no longer owns DMA."""
        if generation != self.active:
            return []
        self.active = self.pending
        self.pending = None
        self.stopping = False
        return [] if self.active is None else [Command('play', self.active)]

    def cancel(self):
        """Off, shutdown, movie entry: clear retriggers and stop current playback."""
        self.pending = None
        if self.active is None or self.stopping:
            return []
        self.stopping = True
        return [Command('stop', self.active)]
