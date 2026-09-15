import time
from collections import Counter


class SessionAnalytics:

    def __init__(self):

        self.start_time = time.time()

        self.current_people = 0

        self.peak_occupancy = 0

        self.unique_people = set()

        self.entries = 0

        self.exits = 0

        self.moving_frames = 0

        self.stationary_frames = 0

        self.fast_movements = 0

        self.direction_history = []

        self.tracking_times = {}

        self.active_tracking = {}


    # ============================================================
    # PEOPLE
    # ============================================================

    def update_people(self, current_ids):

        current_ids = set(
            current_ids
        )


        self.current_people = len(
            current_ids
        )


        self.peak_occupancy = max(
            self.peak_occupancy,
            self.current_people
        )


        self.unique_people.update(
            current_ids
        )


    # ============================================================
    # ENTRY
    # ============================================================

    def record_entry(
        self,
        person_id
    ):

        self.entries += 1

        self.active_tracking[
            person_id
        ] = time.time()


    # ============================================================
    # EXIT
    # ============================================================

    def record_exit(
        self,
        person_id
    ):

        self.exits += 1


        if person_id in self.active_tracking:

            duration = (
                time.time()
                - self.active_tracking[
                    person_id
                ]
            )


            self.tracking_times[
                person_id
            ] = duration


            del self.active_tracking[
                person_id
            ]


    # ============================================================
    # MOVEMENT
    # ============================================================

    def record_movement(
        self,
        state,
        direction
    ):

        if state == "MOVING":

            self.moving_frames += 1


        elif state == "STATIONARY":

            self.stationary_frames += 1


        elif state == "FAST":

            self.fast_movements += 1

            self.moving_frames += 1


        if direction not in (
            "STATIONARY",
            None
        ):

            self.direction_history.append(
                direction
            )


    # ============================================================
    # AVERAGE TRACKING TIME
    # ============================================================

    def get_average_tracking_time(self):

        durations = list(
            self.tracking_times.values()
        )


        # Include people still being tracked

        now = time.time()


        for person_id, start_time in (
            self.active_tracking.items()
        ):

            durations.append(
                now - start_time
            )


        if not durations:

            return 0.0


        return (
            sum(durations)
            / len(durations)
        )


    # ============================================================
    # MOST COMMON DIRECTION
    # ============================================================

    def get_most_common_direction(self):

        if not self.direction_history:

            return "N/A"


        return (
            Counter(
                self.direction_history
            )
            .most_common(1)[0][0]
        )


    # ============================================================
    # MOVEMENT PERCENTAGES
    # ============================================================

    def get_movement_percentages(self):

        total = (
            self.moving_frames
            + self.stationary_frames
        )


        if total == 0:

            return 0.0, 0.0


        moving = (
            self.moving_frames
            / total
        ) * 100


        stationary = (
            self.stationary_frames
            / total
        ) * 100


        return moving, stationary


    # ============================================================
    # COMPLETE STATS
    # ============================================================

    def get_stats(self):

        moving, stationary = (
            self.get_movement_percentages()
        )


        return {

            "duration":
                round(
                    time.time()
                    - self.start_time,
                    1
                ),

            "current_people":
                self.current_people,

            "peak_occupancy":
                self.peak_occupancy,

            "unique_people":
                len(
                    self.unique_people
                ),

            "entries":
                self.entries,

            "exits":
                self.exits,

            "moving_percent":
                round(
                    moving,
                    1
                ),

            "stationary_percent":
                round(
                    stationary,
                    1
                ),

            "fast_movements":
                self.fast_movements,

            "average_tracking_time":
                round(
                    self.get_average_tracking_time(),
                    1
                ),

            "most_common_direction":
                self.get_most_common_direction()
        }