from inference import run_support_queue_baseline

from support_queue_env.tasks import TASK_SPECS


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
        self.count = 0

    def create(self, **kwargs):
        self.count += 1
        return DummyResponse("route=support; reply=Please reset your password.")


class DummyChat:
    def __init__(self) -> None:
        self.completions = DummyCompletions()


class DummyClient:
    def __init__(self) -> None:
        self.chat = DummyChat()


def test_run_support_queue_baseline_returns_scores():
    client = DummyClient()

    result = run_support_queue_baseline(client=client, task_specs=TASK_SPECS)

    assert len(result.scores) == 3
    assert all(0.0 < score < 1.0 for score in result.scores)
    assert 0.0 < result.total_score < 1.0
    assert client.chat.completions.count >= 3
