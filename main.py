"""Entry point run by the GitHub Actions workflow."""
from scripts.fetch_and_calc import get_report
from scripts.kakao_send import send_report
from scripts.update_github_secret import update_refresh_token_secret


def main() -> None:
    report = get_report()
    print(report)

    new_refresh_token = send_report(report)
    if new_refresh_token:
        update_refresh_token_secret(new_refresh_token)
        print("refresh_token이 갱신되어 GitHub Secret을 업데이트했습니다.")


if __name__ == "__main__":
    main()
