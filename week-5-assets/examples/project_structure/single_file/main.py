"""Single-file baseline for the project-structure workshop."""


def needs_review(amount_minor: int) -> bool:
    return amount_minor >= 100_000


def main():
    amounts = [500, 150_000]
    for amount in amounts:
        print(amount, needs_review(amount))


if __name__ == "__main__":
    main()
