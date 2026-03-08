from .providers.groq import GroqSpeechProvider
from .semantic_buffer import SemanticBuffer
from .soap_classifier import SOAPClassifier
from .soap_streamer import SOAPStreamer
from .trigger_engine import TriggerEngine


class DictationManager:

    def __init__(self):

        self.stt = GroqSpeechProvider()
        self.classifier = SOAPClassifier()
        self.streamer = SOAPStreamer()

        self.buffer = SemanticBuffer()
        self.trigger = TriggerEngine()

    async def process_audio(
        self,
        audio: bytes,
    ):

        text = await self.stt.transcribe_chunk(audio)

        if not text:
            return {}

        self.buffer.append(text)

        if not self.trigger.should_trigger(
            self.buffer
        ):
            return {
                "transcript_partial": text
            }

        sentence = self.buffer.flush()

        classified = await self.classifier.classify(
            sentence
        )

        soap = self.streamer.update(
            classified["section"],
            classified["content"],
        )

        return {
            "transcript": sentence,
            "soap": soap,
        }
