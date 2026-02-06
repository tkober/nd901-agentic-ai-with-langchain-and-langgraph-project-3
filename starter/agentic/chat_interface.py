from typing import Any, Callable, Optional, Protocol, Sequence
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class ChatInterface(Protocol):
    def next_message(self) -> Optional[str]:
        """Return next user message, or None if the stream is finished."""

    def read_message(self, message: str):
        """Read a message"""


class ListChatInterface:
    messages: Sequence[str]
    _i: int = 0

    def __init__(self, messages: Sequence[str]):
        self.messages = messages
        self._i = 0

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


class LlmChatInterface:
    def __init__(
        self,
        llm: Any,
        instructions: str,
        *,
        max_turns: int = 25,
        end_token: str = "",
        on_generated: Callable[[str], None] | None = None,
    ):
        self._llm = llm
        self._turns_left = max_turns
        self._end_token = end_token
        self._on_generated = on_generated

        self._AIMessage = AIMessage
        self._HumanMessage = HumanMessage

        system = (
            f"{instructions.strip()}\n\n"
            "You are simulating the USER in a chat with an assistant.\n"
            "Rules:\n"
            "- Output ONLY the user's next message as plain text.\n"
            f"- If the conversation should end, output exactly: {end_token}\n"
        )
        self._history = [SystemMessage(content=system)]

    def next_message(self) -> Optional[str]:
        if self._turns_left <= 0:
            return None

        self._turns_left -= 1

        result = self._llm.invoke(self._history)
        content = getattr(result, "content", None)
        if content is None:
            # Some models return a dict-like result
            content = result.get("content") if hasattr(result, "get") else str(result)

        user_text = str(content).strip()
        if not user_text:
            return None
        if user_text == self._end_token:
            return None
        if user_text.lower() in {"exit", "quit"}:
            return None

        # Keep the generated user message in history for subsequent turns.
        self._history.append(self._HumanMessage(content=user_text))
        if self._on_generated:
            self._on_generated(user_text)
        return user_text

    def read_message(self, message: str):
        # Assistant messages (from the real agent) get appended to the history.
        msg = str(message)
        if msg.strip():
            self._history.append(self._AIMessage(content=msg))
