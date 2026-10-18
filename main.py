"""Entry point run by the GitHub Actions workflow."""
from scripts.fetch_and_calc import get_report
from scripts.telegram_send import send_report


def main() -> None:
    report = get_report()
    print(report)
    send_report(report)


if __name__ == "__main__":
    main()
