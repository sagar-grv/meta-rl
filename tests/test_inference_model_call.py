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
