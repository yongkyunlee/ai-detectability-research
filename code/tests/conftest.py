import pytest
from ai_text_quality.models import Task, GoldFact, ContextSources, GeneratedText, LinguisticFeatures

@pytest.fixture
def sample_task():
    return Task(
        task_id="test_001",
        project="test_project",
        topic="Getting started with TestLib",
        word_target="300-500",
        gold_facts=[
            GoldFact(field="install_cmd", value="pip install testlib", match_type="literal"),
            GoldFact(field="version", value=r"v?\d+\.\d+", match_type="regex"),
            GoldFact(field="purpose", value="data processing library", match_type="semantic"),
        ],
        context_sources=ContextSources(
            code_only=["data/context/test/code/readme.md"],
            additional=["data/context/test/issues/setup.md"],
        ),
    )

@pytest.fixture
def sample_text():
    return """Getting started with TestLib is straightforward. First, you'll need to install it with pip install testlib. The library requires Python 3.10 or newer.

TestLib is a powerful data processing library that simplifies ETL workflows. We've been using it in production for about six months now, and it's handled everything we've thrown at it.

The current version is v2.3.1, released last month. It brought some significant performance improvements — batch processing is roughly 40% faster than v2.2.

To get started, create a new project directory and initialize it. The configuration lives in a config.yaml file at the project root. You don't need much to get going — just specify your data sources and output format.

One thing I'd note: the default settings work well for most cases, but if you're processing more than a million rows, you'll want to bump up the worker count in the config. We learned that the hard way."""

@pytest.fixture
def sample_generated_text(sample_text):
    return GeneratedText(
        task_id="test_001",
        condition="code_only",
        run_id="run_01",
        text=sample_text,
        model="claude-sonnet-4-20250514",
        timestamp="2025-01-01T00:00:00",
        token_usage={"input_tokens": 500, "output_tokens": 300},
    )

@pytest.fixture
def ai_style_text():
    """Text with typical AI writing patterns."""
    return """In the world of modern software development, testing frameworks play a crucial role. Furthermore, it's worth noting that automated testing has become an essential part of the development lifecycle.

When it comes to choosing a testing framework, there are several important factors to consider. Moreover, the framework should integrate seamlessly with your existing workflow. It should be noted that compatibility is key.

Additionally, performance is arguably one of the most critical aspects. In conclusion, selecting the right framework requires careful evaluation of your specific needs and requirements.

Let's dive in and explore the key features:
- Feature one is important
- Feature two is essential
- Feature three is critical
- Feature four is fundamental
- Feature five is noteworthy"""

@pytest.fixture
def human_style_text():
    """Text that reads more naturally/human-like."""
    return """I've been using pytest for about three years now, and it's completely changed how I think about testing. Before that, I was stuck with unittest — which works, but feels clunky.

So here's the thing. Pytest discovers your tests automatically. You don't need to subclass anything or follow rigid naming conventions beyond prefixing with test_. That alone saves time.

We switched our team over last quarter. The migration wasn't painless — we had about 200 tests to convert — but it took less than a week. Most of it was just removing boilerplate.

One gotcha: fixtures can get confusing if you nest them too deep. I'd recommend keeping your conftest.py files shallow and well-documented. We burned a few hours debugging a fixture scope issue that would've been obvious with better organization."""
