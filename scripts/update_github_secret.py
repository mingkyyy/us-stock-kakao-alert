"""Update a GitHub Actions repo secret via the GitHub API.

Used to persist a rotated Kakao refresh_token between workflow runs:
each run may receive a new refresh_token from Kakao, and the next run
needs that new value, so it's written back as a repo secret here.
"""
import base64
import os

import requests
from nacl import encoding, public


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key_b64.encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()


def update_secret(owner: str, repo: str, secret_name: str, secret_value: str, github_token: str) -> None:
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
    }

    key_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key",
        headers=headers,
        timeout=10,
    )
    key_resp.raise_for_status()
    key_data = key_resp.json()

    encrypted_value = encrypt_secret(key_data["key"], secret_value)

    put_resp = requests.put(
        f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        json={"encrypted_value": encrypted_value, "key_id": key_data["key_id"]},
        timeout=10,
    )
    put_resp.raise_for_status()


def update_refresh_token_secret(new_refresh_token: str) -> None:
    repo_full = os.environ["GITHUB_REPOSITORY"]  # e.g. "user/us-stock-kakao-alert"
    owner, repo = repo_full.split("/", 1)
    github_token = os.environ["GH_PAT"]
    update_secret(owner, repo, "KAKAO_REFRESH_TOKEN", new_refresh_token, github_token)
