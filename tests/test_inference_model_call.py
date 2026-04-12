import pytest

from inference import build_user_prompt, get_model_message


class DummyMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class DummyChoice:
    def __init__(self, content: str) -> None:
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content: str) -> None:
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return DummyResponse("route=support; reply=Please reset your password.")


class DummyChat:
    def __init__(self) -> None:
        self.completions = DummyCompletions()


class DummyClient:
    def __init__(self) -> None:
        self.chat = DummyChat()


def test_build_user_prompt_includes_context():
    prompt = build_user_prompt(
        step=2,
        last_echoed="Customer needs help",
        last_reward=0.25,
        history=["Step 1: initial triage"],
    )

    assert "Customer needs help" in prompt
    assert "Step 1: initial triage" in prompt


def test_get_model_message_uses_openai_client():
    client = DummyClient()

    message = get_model_message(
        client,
        step=1,
        last_echoed="Ticket open",
        last_reward=0.0,
        history=[],
    )

    assert message == "route=support; reply=Please reset your password."
    assert client.chat.completions.calls[0]["model"] == "gpt-test"
    assert client.chat.completions.calls[0]["timeout"] == 20


class FlakyCompletions:
    def __init__(self) -> None:
        self.calls = []
        self._attempt = 0

    def create(self, **kwargs):
        self.calls.append(kwargs)
        self._attempt += 1
        if self._attempt == 1:
            raise TimeoutError("transient timeout")
        return DummyResponse("route=support; reply=Retry succeeded.")


class FlakyClient:
    def __init__(self) -> None:
        self.chat = type("Chat", (), {"completions": FlakyCompletions()})()


def test_get_model_message_retries_once_on_transient_error():
    client = FlakyClient()

    message = get_model_message(
        client,
        step=1,
        last_echoed="Ticket open",
        last_reward=0.0,
        history=[],
    )

    assert message == "route=support; reply=Retry succeeded."
    assert len(client.chat.completions.calls) == 2


class AlwaysFailCompletions:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        raise TimeoutError("persistent timeout")


class AlwaysFailClient:
    def __init__(self) -> None:
        self.chat = type("Chat", (), {"completions": AlwaysFailCompletions()})()


def test_get_model_message_raises_after_retry_budget_exhausted():
    client = AlwaysFailClient()

    with pytest.raises(TimeoutError):
        get_model_message(
            client,
            step=1,
            last_echoed="Ticket open",
            last_reward=0.0,
            history=[],
        )

    assert len(client.chat.completions.calls) == 2
