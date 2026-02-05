from typing import Protocol, Optional, Sequence


class ChatInterface(Protocol):
    def next_message(self) -> Optional[str]:
        """Return next user message, or None if the stream is finished."""

    def read_message(self, message: str):
        """Read a message"""


class ListChatInterface:
    messages: Sequence[str]
    _i: int = 0

    def next_message(self) -> Optional[str]:
        if self._i >= len(self.messages):
            return None
        msg = self.messages[self._i]
        self._i += 1
        return msg

    def read_message(self, message: str):
        print(message)


class ConsoleChatInterface:
    def next_message(self) -> str | None:
        msg = input("> ").strip()
        if msg.lower() in {"exit", "quit"}:
            return None
        return msg

    def read_message(self, message: str):
        print(message)
