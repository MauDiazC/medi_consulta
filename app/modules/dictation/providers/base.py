from abc import ABC, abstractmethod


class SpeechProvider(ABC):

    @abstractmethod
    async def transcribe_chunk(
        self,
        audio: bytes,
    ) -> str:
        pass
