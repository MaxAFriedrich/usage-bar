"""State machine for tracking typing activity and break status."""
import time
from dataclasses import dataclass
from enum import Enum


class NotificationState(int, Enum):
    """Visual notification states."""
    BREAK_OVER = 0
    BREAK = 1
    TYPING = 2
    OVERSPEED = 3
    BREAK_DUE = 4


@dataclass
class TypingState:
    """Tracks the current typing state and break requirements."""

    # last time the keystroke count was zero
    last_zero: float = -1
    # number of seconds to add to break threshold for too fast typing
    overspeed_penalty: float = 0
    # currently in overspeed state
    in_overspeed: bool = False
    # time the break will finish
    break_finish: float = -1
    # start of typing session
    typing_start: float = -1

    def __init__(self, config):
        self.config = config
        self.last_zero = -1
        self.overspeed_penalty = 0
        self.in_overspeed = False
        self.break_finish = -1
        self.typing_start = -1

    def update(self, event_count):
        """Update state based on current event count."""
        if event_count == 0:
            if self.last_zero == -1:
                # entered break state
                self.last_zero = time.time()
                self.typing_start = -1
                self.break_finish = (
                        time.time() +
                        self.config.break_threshold +
                        self.overspeed_penalty
                )
                return
            if time.time() > self.break_finish:
                # break is over, so reset
                self.overspeed_penalty = 0
                self.in_overspeed = False
                self.break_finish = -1
            return

        if event_count != 0 and self.last_zero != -1:
            # just started typing
            self.last_zero = -1
            self.break_finish = -1
            self.typing_start = time.time()

        if event_count > self.config.overspeed_threshold:
            self.in_overspeed = True
            new_penalty = event_count * self.config.overspeed_count_multiplier
            if new_penalty > self.overspeed_penalty:
                # don't let penalty drop
                self.overspeed_penalty = new_penalty
        else:
            self.in_overspeed = False

        if self.overspeed_penalty > self.config.max_overspeed_penalty:
            self.overspeed_penalty = self.config.max_overspeed_penalty

    def get_notification_state(self):
        """Determine which notification state to display."""
        break_due = (self.typing_start + self.config.break_length +
                     self.overspeed_penalty)

        if self.in_overspeed:
            return NotificationState.OVERSPEED
        elif self.break_finish != -1:
            return NotificationState.BREAK
        elif self.last_zero != -1:
            return NotificationState.BREAK_OVER
        elif self.typing_start != -1 and time.time() > break_due:
            return NotificationState.BREAK_DUE
        elif self.typing_start != -1:
            return NotificationState.TYPING

        return NotificationState.BREAK
