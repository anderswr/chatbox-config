#!/usr/bin/env python3
"""Check web configuration and Realtime credentials without opening audio."""

from __future__ import annotations

import sys

import requests

from raspberry.config import Config


def main() -> int:
    config = Config.load()
    print(f"OK: konfigurasjon lastet (modell={config.model}, stemme={config.voice})")

    if config.token_url and config.device_token:
        response = requests.post(
            config.token_url,
            json={"model": config.model, "voice": config.voice},
            headers={"Authorization": f"Bearer {config.device_token}"},
            timeout=10,
        )
        if "DEPLOYMENT_NOT_FOUND" in response.text:
            print(
                "FEIL: Vercel sier DEPLOYMENT_NOT_FOUND. Domenet i REALTIME_TOKEN_URL "
                "er ikke koblet til en aktiv deployment. Kopier Production Domain fra "
                "Vercel → Project → Settings → Domains og deploy main.",
                file=sys.stderr,
            )
            return 2
        if response.status_code == 404:
            print(
                f"FEIL: {config.token_url} finnes ikke i aktiv Vercel-deployment. "
                "Redeploy main-branchen i det eksisterende Vercel-prosjektet.",
                file=sys.stderr,
            )
            return 2
        if not response.ok:
            print(
                f"FEIL: token-endepunktet svarte HTTP {response.status_code}: "
                f"{response.text[:500]}",
                file=sys.stderr,
            )
            return 3
        if not response.json().get("value"):
            print("FEIL: token-endepunktet returnerte ingen client secret.", file=sys.stderr)
            return 4
        print(f"OK: Realtime client secret mottatt fra {config.token_url}")
        return 0

    if config.api_key:
        print("ADVARSEL: bruker lokal OPENAI_API_KEY; Vercel token-proxy er ikke konfigurert.")
        return 0
    print("FEIL: mangler både token-proxy og lokal OPENAI_API_KEY.", file=sys.stderr)
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
