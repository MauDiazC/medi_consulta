class SOAPStreamer:

    def __init__(self):
        self.soap = {
            "subjective": "",
            "objective": "",
            "assessment": "",
            "plan": "",
        }

    def update(self, section, content):

        self.soap[section.lower()] += (
            " " + content
        )

        return self.soap
