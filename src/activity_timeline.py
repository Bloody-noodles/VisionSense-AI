from datetime import datetime


class ActivityTimeline:

    def __init__(self, max_events=100):

        # ========================================================
        # TIMELINE STORAGE
        # ========================================================

        self.events = []

        # Maximum events kept in memory
        self.max_events = max_events


    # ============================================================
    # ADD EVENT
    # ============================================================

    def add_event(self, event):

        if not event:
            return

        timeline_event = {

            "sequence": event.get(
                "sequence"
            ),

            "timestamp": event.get(
                "timestamp",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),

            "type": event.get(
                "type",
                "UNKNOWN"
            ),

            "person_id": event.get(
                "person_id"
            ),

            "value": event.get(
                "value",
                ""
            ),

            "message": event.get(
                "message",
                ""
            )
        }

        # Add event
        self.events.append(
            timeline_event
        )

        # Keep memory bounded
        if len(self.events) > self.max_events:

            self.events = self.events[
                -self.max_events:
            ]


    # ============================================================
    # ADD MULTIPLE EVENTS
    # ============================================================

    def add_events(self, events):

        if not events:
            return

        for event in events:

            self.add_event(
                event
            )


    # ============================================================
    # GET RECENT EVENTS
    # ============================================================

    def get_recent(
        self,
        limit=20
    ):

        if limit <= 0:
            return []

        return self.events[
            -limit:
        ]


    # ============================================================
    # GET EVENTS BY TYPE
    # ============================================================

    def get_by_type(
        self,
        event_type
    ):

        return [
            event
            for event in self.events
            if event["type"] == event_type
        ]


    # ============================================================
    # GET EVENTS FOR PERSON
    # ============================================================

    def get_by_person(
        self,
        person_id
    ):

        return [
            event
            for event in self.events
            if event["person_id"] == person_id
        ]


    # ============================================================
    # GET LATEST EVENT
    # ============================================================

    def get_latest(self):

        if not self.events:
            return None

        return self.events[-1]


    # ============================================================
    # TIMELINE COUNT
    # ============================================================

    def count(self):

        return len(
            self.events
        )


    # ============================================================
    # CLEAR TIMELINE
    # ============================================================

    def clear(self):

        self.events.clear()