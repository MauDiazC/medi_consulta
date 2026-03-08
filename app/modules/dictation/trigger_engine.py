class TriggerEngine:

    MIN_CHARS = 40
    MAX_IDLE = 2.0

    def should_trigger(
        self,
        buffer,
    ):

        if len(buffer.buffer) > self.MIN_CHARS:
            return True

        if buffer.idle_time() > self.MAX_IDLE:
            return True

        return False
