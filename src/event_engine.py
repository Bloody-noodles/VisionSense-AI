import csv
import os
import time
from datetime import datetime


class EventEngine:

    def __init__(self, log_file="logs/events.csv"):

        self.log_file = log_file

        os.makedirs(
            os.path.dirname(log_file),
            exist_ok=True
        )

        # ========================================================
        # TRACKING STATE
        # ========================================================

        # Confirmed people currently considered active.
        self.active_ids = set()

        # Movement state for each tracked person.
        self.movement_states = {}

        # Last known direction for each person.
        self.directions = {}

        # Last time a FAST_MOVEMENT event was generated.
        self.fast_event_times = {}

        # --------------------------------------------------------
        # TRACK LOSS GRACE PERIOD
        # --------------------------------------------------------
        #
        # ByteTrack can temporarily lose a person for a frame or
        # two. We do NOT immediately call that an exit.
        #
        # If the ID returns before this timeout, it continues as
        # the same active track.
        #
        self.pending_exits = {}

        self.TRACK_LOSS_GRACE_PERIOD = 1.5


        # ========================================================
        # EVENT HISTORY
        # ========================================================

        self.events = []

        self.MAX_MEMORY_EVENTS = 500

        # Global event sequence.
        #
        # The API uses this to determine which events are new.

        self.event_sequence = 0


        # ========================================================
        # EVENT SETTINGS
        # ========================================================

        self.FAST_EVENT_COOLDOWN = 2.0


        # ========================================================
        # CSV LOG
        # ========================================================

        if not os.path.exists(self.log_file):

            with open(
                self.log_file,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "event",
                    "person_id",
                    "value"
                ])


    # ============================================================
    # LOG EVENT
    # ============================================================

    def log_event(
        self,
        event,
        person_id="",
        value=""
    ):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )


        # --------------------------------------------------------
        # Generate human-readable message
        # --------------------------------------------------------

        message = self._create_message(
            event,
            person_id,
            value
        )


        # --------------------------------------------------------
        # Increment sequence
        # --------------------------------------------------------

        self.event_sequence += 1


        # --------------------------------------------------------
        # Structured event
        # --------------------------------------------------------

        structured_event = {

            "sequence":
                self.event_sequence,

            "timestamp":
                timestamp,

            "type":
                event,

            "person_id":
                (
                    person_id
                    if person_id != ""
                    else None
                ),

            "value":
                value,

            "message":
                message
        }


        # --------------------------------------------------------
        # Store in memory
        # --------------------------------------------------------

        self.events.append(
            structured_event
        )


        # Keep memory bounded.

        if len(self.events) > self.MAX_MEMORY_EVENTS:

            self.events = (
                self.events[
                    -self.MAX_MEMORY_EVENTS:
                ]
            )


        # --------------------------------------------------------
        # Save to CSV
        # --------------------------------------------------------

        with open(
            self.log_file,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                event,
                person_id,
                value
            ])


        # --------------------------------------------------------
        # Terminal output
        # --------------------------------------------------------

        print(
            f"[{timestamp}] "
            f"{event} "
            f"ID={person_id} "
            f"{value}"
        )


        return structured_event


    # ============================================================
    # MESSAGE GENERATOR
    # ============================================================

    def _create_message(
        self,
        event,
        person_id,
        value
    ):

        person = (
            f"Person {person_id}"
            if person_id != ""
            else "System"
        )


        if event == "PERSON_ENTERED":

            return (
                f"{person} entered the scene"
            )


        if event == "PERSON_EXITED":

            return (
                f"{person} left the scene"
            )


        if event == "TRACK_LOST":

            return (
                f"{person} track was lost"
            )


        if event == "OCCUPANCY_CHANGE":

            return (
                f"Occupancy changed: {value}"
            )


        if event == "MOVEMENT_STARTED":

            return (
                f"{person} started moving "
                f"toward {value}"
            )


        if event == "MOVEMENT_STOPPED":

            return (
                f"{person} stopped moving"
            )


        if event == "DIRECTION_CHANGED":

            return (
                f"{person} changed direction "
                f"{value}"
            )


        if event == "FAST_MOVEMENT":

            return (
                f"{person} moved quickly "
                f"({value})"
            )


        return (
            f"{event} "
            f"{person}"
        )


    # ============================================================
    # PEOPLE / ENTRY / EXIT
    # ============================================================

    def update_people(self, current_ids):

        current_ids = set(
            current_ids
        )

        now = time.time()


        # ========================================================
        # STEP 1 — CANCEL PENDING EXITS
        # ========================================================
        #
        # If a person disappeared briefly but has now returned,
        # cancel the pending exit.
        #

        for person_id in list(
            self.pending_exits.keys()
        ):

            if person_id in current_ids:

                del self.pending_exits[
                    person_id
                ]


        # ========================================================
        # STEP 2 — DETECT NEW PEOPLE
        # ========================================================

        entered = (
            current_ids
            - self.active_ids
        )


        # Only generate a real ENTER event for a person who
        # wasn't already active.

        for person_id in entered:

            self.log_event(
                "PERSON_ENTERED",
                person_id
            )


        # ========================================================
        # STEP 3 — START TRACK-LOSS GRACE PERIOD
        # ========================================================
        #
        # Do NOT immediately declare an exit.
        #

        potentially_exited = (
            self.active_ids
            - current_ids
        )


        for person_id in potentially_exited:

            if person_id not in self.pending_exits:

                self.pending_exits[
                    person_id
                ] = now


        # ========================================================
        # STEP 4 — CONFIRM REAL EXITS
        # ========================================================

        confirmed_exits = set()


        for person_id in list(
            self.pending_exits.keys()
        ):

            lost_time = (
                now
                - self.pending_exits[
                    person_id
                ]
            )


            # Person has returned before grace period expired.

            if person_id in current_ids:

                del self.pending_exits[
                    person_id
                ]

                continue


            # Person has genuinely been missing long enough.

            if (
                lost_time
                >= self.TRACK_LOSS_GRACE_PERIOD
            ):

                confirmed_exits.add(
                    person_id
                )


        # ========================================================
        # STEP 5 — PROCESS CONFIRMED EXITS
        # ========================================================

        for person_id in confirmed_exits:

            self.log_event(
                "PERSON_EXITED",
                person_id
            )


            self.log_event(
                "TRACK_LOST",
                person_id
            )


            self.pending_exits.pop(
                person_id,
                None
            )


            self.movement_states.pop(
                person_id,
                None
            )


            self.directions.pop(
                person_id,
                None
            )


            self.fast_event_times.pop(
                person_id,
                None
            )


        # ========================================================
        # STEP 6 — BUILD NEW ACTIVE SET
        # ========================================================
        #
        # People who are temporarily missing remain active during
        # the grace period.
        #

        new_active_ids = (
            self.active_ids
            | current_ids
        )


        # Remove people whose exits were confirmed.

        new_active_ids -= confirmed_exits


        # ========================================================
        # STEP 7 — OCCUPANCY CHANGE
        # ========================================================

        previous_count = (
            len(self.active_ids)
        )

        current_count = (
            len(new_active_ids)
        )


        if current_count != previous_count:

            self.log_event(
                "OCCUPANCY_CHANGE",
                value=(
                    f"{previous_count}"
                    f" -> "
                    f"{current_count}"
                )
            )


        # ========================================================
        # STEP 8 — SAVE ACTIVE STATE
        # ========================================================

        self.active_ids = (
            new_active_ids
        )


        return entered, confirmed_exits


    # ============================================================
    # MOVEMENT EVENTS
    # ============================================================

    def update_movement(
        self,
        person_id,
        state,
        direction,
        speed=0.0
    ):

        previous_state = (
            self.movement_states.get(
                person_id
            )
        )


        previous_direction = (
            self.directions.get(
                person_id
            )
        )


        valid_direction = (
            direction not in (
                None,
                "",
                "STATIONARY"
            )
        )


        # --------------------------------------------------------
        # MOVEMENT STARTED
        # --------------------------------------------------------

        if (
            state in (
                "MOVING",
                "FAST"
            )
            and
            previous_state == "STATIONARY"
            and
            valid_direction
        ):

            self.log_event(
                "MOVEMENT_STARTED",
                person_id,
                direction
            )


        # --------------------------------------------------------
        # MOVEMENT STOPPED
        # --------------------------------------------------------

        if (
            state == "STATIONARY"
            and
            previous_state in (
                "MOVING",
                "FAST"
            )
        ):

            self.log_event(
                "MOVEMENT_STOPPED",
                person_id
            )


        # --------------------------------------------------------
        # DIRECTION CHANGED
        # --------------------------------------------------------

        if (
            valid_direction
            and
            previous_direction not in (
                None,
                "",
                "STATIONARY"
            )
            and
            direction != previous_direction
            and
            state in (
                "MOVING",
                "FAST"
            )
        ):

            self.log_event(
                "DIRECTION_CHANGED",
                person_id,
                (
                    f"{previous_direction}"
                    f" -> "
                    f"{direction}"
                )
            )


        # --------------------------------------------------------
        # FAST MOVEMENT
        # --------------------------------------------------------

        if state == "FAST":

            now = time.time()


            last_fast_event = (
                self.fast_event_times.get(
                    person_id,
                    0
                )
            )


            if (
                now - last_fast_event
                >= self.FAST_EVENT_COOLDOWN
            ):

                self.log_event(
                    "FAST_MOVEMENT",
                    person_id,
                    f"{speed:.1f} px/s"
                )


                self.fast_event_times[
                    person_id
                ] = now


        # --------------------------------------------------------
        # SAVE STATE
        # --------------------------------------------------------

        self.movement_states[
            person_id
        ] = state


        if valid_direction:

            self.directions[
                person_id
            ] = direction


    # ============================================================
    # RECENT EVENTS
    # ============================================================

    def get_recent_events(
        self,
        limit=20
    ):

        if limit <= 0:

            return []

        return self.events[
            -limit:
        ]


    # ============================================================
    # EVENTS SINCE SEQUENCE
    # ============================================================

    def get_events_since(
        self,
        sequence
    ):

        return [

            event

            for event in self.events

            if event["sequence"] > sequence
        ]


    # ============================================================
    # LATEST EVENT
    # ============================================================

    def get_latest_event(self):

        if not self.events:

            return None

        return self.events[-1]


    # ============================================================
    # CLEAR MEMORY
    # ============================================================

    def clear_events(self):

        self.events.clear()

        self.event_sequence = 0

        self.pending_exits.clear()

        self.active_ids.clear()

        self.movement_states.clear()

        self.directions.clear()

        self.fast_event_times.clear()