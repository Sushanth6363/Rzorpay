"""Every CSS class the dashboard uses must be defined in its stylesheet.

WHY THIS EXISTS
    Removing a superseded style block also removed `.case` and `.lad`, which the case
    board still used. The page rendered without raising, every existing test passed, and
    the board silently degraded into a wall of unstyled text - customer name, email and
    the four ladder rungs run together as "EMAILSMSWHATSAPPCALL".

    That is the worst shape of UI bug: no exception, no failing test, and nobody notices
    until someone looks. The render test cannot catch it, because unstyled HTML is still
    valid HTML.

    So this compares the two sets directly. It is not a design opinion - a class used in
    markup and absent from the stylesheet is simply a fact about the file being wrong.
"""

import re
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "app" / "ui" / "dashboard.py"


@pytest.fixture(scope="module")
def source() -> str:
    return SOURCE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def stylesheet(source: str) -> str:
    start = source.index("STYLES = ")
    return source[start:source.index('"""', start + 20)]


def _classes_used(source: str) -> set:
    """Class names appearing in markup, including those built by f-string interpolation.

    `class="step {state}"` and `class="chk{'' if ok else ' bad'}"` are both real usages, so
    the literal prefix is captured rather than requiring a closing quote. Missing those
    would make this test report live classes as dead - and deleting one is the exact
    mistake it exists to prevent.
    """
    used = set()
    for attr in re.findall(r'class="([a-z][a-z0-9 _-]*)', source):
        used.update(attr.split())
    return used


def _classes_defined(stylesheet: str) -> set:
    return set(re.findall(r"\.([a-z][a-z0-9-]*)", stylesheet))


def test_every_class_used_in_markup_is_defined(source, stylesheet):
    """The regression: `.case` and `.lad` were used by the board and defined nowhere."""
    missing = sorted(_classes_used(source) - _classes_defined(stylesheet))

    assert not missing, (
        f"markup uses classes with no style rule: {missing}. "
        f"The page will still render, and the affected section will look broken."
    )


def test_the_load_bearing_board_classes_are_present(stylesheet):
    """Named explicitly, because these carry meaning rather than decoration: the card, its
    status stripe, and the escalation ladder whose lit rung claims a message was sent."""
    for required in (".case", ".lad", ".tile", ".step", ".chk", ".ans"):
        assert required in stylesheet, f"{required} is missing from the stylesheet"


def test_the_ladder_distinguishes_a_sent_rung_from_a_planned_one(stylesheet):
    """A lit rung says a message went out; a dashed one says an action was decided and not
    yet dispatched. If those render identically the board makes a claim it cannot support."""
    assert ".lad .r.done" in stylesheet
    assert ".lad .r.next" in stylesheet
    assert "dashed" in stylesheet.split(".lad .r.next")[1][:200]


def test_no_style_rule_is_defined_for_a_class_nobody_uses(source, stylesheet):
    """Dead style rules are how a stylesheet grows until nobody dares delete from it -
    which is exactly the edit that broke the board. Allows the small set of structural
    helpers that are applied to Streamlit's own elements rather than ours."""
    framework_owned = {
        "block-container", "css", "stmetricvalue", "urx-card", "urx-head", "urx-banner",
        "urx-kv", "note", "pill", "ok", "warn", "stop", "mute", "acc", "v", "k", "b",
        "done", "next", "bad", "on", "hi", "sub", "big", "ci", "lab", "n", "t", "d",
        "e", "r", "m", "l", "h", "a", "w", "sep", "dot", "code", "bd", "row", "idc",
        "ladc", "amtc", "who", "con", "amt", "due", "stg", "meta", "formula", "action",
        "mono", "tint", "c",
    }
    unused = sorted(
        c for c in _classes_defined(stylesheet) - _classes_used(source)
        if c not in framework_owned
    )

    assert not unused, f"stylesheet defines rules nothing uses: {unused}"
