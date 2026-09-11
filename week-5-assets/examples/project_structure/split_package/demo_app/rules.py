"""Pure demonstration rule; input is assumed to be validated integer minor units."""


def needs_review(amount_minor: int) -> bool:
    return amount_minor >= 100_000
