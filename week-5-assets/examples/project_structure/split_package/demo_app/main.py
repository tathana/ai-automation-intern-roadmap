"""Run from split_package with: python -m demo_app.main"""
from demo_app.rules import needs_review


def main():
    amounts = [500, 150_000]
    for amount in amounts:
        print(amount, needs_review(amount))


if __name__ == "__main__":
    main()
