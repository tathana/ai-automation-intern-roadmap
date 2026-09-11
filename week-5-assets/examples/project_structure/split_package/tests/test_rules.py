from demo_app.rules import needs_review


def test_below_threshold():
    assert needs_review(500) is False


def test_exact_threshold():
    assert needs_review(100_000) is True


def test_above_threshold():
    assert needs_review(150_000) is True
