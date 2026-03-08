import time


class SemanticBuffer:

    def __init__(self):

        self.buffer = ""
        self.last_update = time.time()

    def append(self, text: str):

        self.buffer += " " + text
        self.last_update = time.time()

    def flush(self):

        text = self.buffer.strip()
        self.buffer = ""

        return text

    def idle_time(self):

        return time.time() - self.last_update
