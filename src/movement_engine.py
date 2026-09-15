import math
import time
from collections import deque


class MovementEngine:

    def __init__(self):

        self.tracks = {}

        # ========================================================
        # MOVEMENT THRESHOLDS
        # ========================================================

        self.MOVEMENT_ENTER = 14
        self.MOVEMENT_EXIT = 7

        self.FAST_ENTER = 80
        self.FAST_EXIT = 55

        # ========================================================
        # SPEED SMOOTHING
        # ========================================================

        self.SMOOTHING = 0.35

        # ========================================================
        # DIRECTION ANALYSIS
        # ========================================================

        # Number of recent positions used to determine direction
        self.POSITION_HISTORY = 8


    # ============================================================
    # UPDATE
    # ============================================================

    def update(self, person_id, center):

        now = time.time()


        # ========================================================
        # FIRST OBSERVATION
        # ========================================================

        if person_id not in self.tracks:

            history = deque(
                maxlen=self.POSITION_HISTORY
            )

            history.append(
                (center, now)
            )

            self.tracks[person_id] = {

                "previous_center": center,

                "last_seen": now,

                "distance": 0.0,

                "speed": 0.0,

                "smoothed_speed": 0.0,

                "direction": "STATIONARY",

                "state": "STATIONARY",

                "history": history
            }

            return self.tracks[person_id]


        track = self.tracks[person_id]

        previous = track["previous_center"]


        # ========================================================
        # FRAME-TO-FRAME DISTANCE
        # ========================================================

        dx = center[0] - previous[0]
        dy = center[1] - previous[1]

        distance = math.sqrt(
            dx ** 2 + dy ** 2
        )


        # ========================================================
        # TIME DELTA
        # ========================================================

        elapsed = max(
            now - track["last_seen"],
            0.001
        )


        # ========================================================
        # RAW SPEED
        # ========================================================

        raw_speed = distance / elapsed


        # ========================================================
        # SMOOTH SPEED
        # ========================================================

        previous_speed = track[
            "smoothed_speed"
        ]

        smoothed_speed = (
            previous_speed * (1 - self.SMOOTHING)
            +
            raw_speed * self.SMOOTHING
        )


        # ========================================================
        # SAVE POSITION HISTORY
        # ========================================================

        history = track["history"]

        history.append(
            (center, now)
        )


        # ========================================================
        # TEMPORAL DIRECTION
        # ========================================================

        direction = self._calculate_direction(
            history
        )


        # ========================================================
        # PREVIOUS STATE
        # ========================================================

        previous_state = track["state"]


        # ========================================================
        # MOVEMENT STATE
        # ========================================================

        state = previous_state


        # --------------------------------------------------------
        # STATIONARY → MOVING
        # --------------------------------------------------------

        if previous_state == "STATIONARY":

            if smoothed_speed >= self.MOVEMENT_ENTER:

                state = "MOVING"


        # --------------------------------------------------------
        # MOVING
        # --------------------------------------------------------

        elif previous_state == "MOVING":

            if smoothed_speed <= self.MOVEMENT_EXIT:

                state = "STATIONARY"

            elif smoothed_speed >= self.FAST_ENTER:

                state = "FAST"


        # --------------------------------------------------------
        # FAST
        # --------------------------------------------------------

        elif previous_state == "FAST":

            if smoothed_speed <= self.MOVEMENT_EXIT:

                state = "STATIONARY"

            elif smoothed_speed <= self.FAST_EXIT:

                state = "MOVING"


        # ========================================================
        # SAFETY
        # ========================================================

        if state == "STATIONARY":

            direction = "STATIONARY"

        elif direction == "STATIONARY":

            # Keep the previous known direction while
            # the temporal window is still stabilizing.

            direction = track["direction"]


        # ========================================================
        # UPDATE TRACK
        # ========================================================

        track["previous_center"] = center

        track["last_seen"] = now

        track["distance"] += distance

        # IMPORTANT:
        # expose the smoothed speed as the public speed value

        track["speed"] = smoothed_speed

        track["smoothed_speed"] = smoothed_speed

        track["direction"] = direction

        track["state"] = state


        return track


    # ============================================================
    # TEMPORAL DIRECTION CALCULATION
    # ============================================================

    def _calculate_direction(
        self,
        history
    ):

        if len(history) < 4:

            return "STATIONARY"


        # Use an older position and the newest position.
        # This removes much of the frame-to-frame jitter.

        old_position, old_time = history[0]

        new_position, new_time = history[-1]


        dx = (
            new_position[0]
            - old_position[0]
        )

        dy = (
            new_position[1]
            - old_position[1]
        )


        distance = math.sqrt(
            dx ** 2 + dy ** 2
        )


        # Not enough displacement to determine
        # a reliable direction.

        if distance < self.MOVEMENT_EXIT:

            return "STATIONARY"


        # ========================================================
        # DIRECTION DOMINANCE
        # ========================================================

        # Require one axis to clearly dominate.
        # This prevents tiny diagonal/jitter movements from
        # constantly switching between UP/DOWN/LEFT/RIGHT.

        horizontal = abs(dx)
        vertical = abs(dy)


        if horizontal > vertical * 1.25:

            if dx > 0:

                return "RIGHT"

            return "LEFT"


        if vertical > horizontal * 1.25:

            if dy > 0:

                return "DOWN"

            return "UP"


        # Diagonal / ambiguous movement

        return "STATIONARY"


    # ============================================================
    # REMOVE OLD TRACKS
    # ============================================================

    def remove_old_tracks(
        self,
        timeout=3
    ):

        now = time.time()

        expired = []


        for person_id, track in self.tracks.items():

            if (
                now - track["last_seen"]
                > timeout
            ):

                expired.append(
                    person_id
                )


        for person_id in expired:

            del self.tracks[
                person_id
            ]