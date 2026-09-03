"""Jede `.env.example` des Agenten ist die Konfiguration, die kopiert wird.

Review finding G-090. `workforce-agent.env.example` setzte `AGENT_PROVIDER=echo`
neben `AGENT_MODEL=claude-opus-5`. Unveraendert kopiert - so, wie der Kopf der
Datei es vorsieht - verweigerte `build_provider()` den Start mit
`AGENT_MODEL_PROVIDER_MISMATCH`: Die Allowlist bindet ein Modell an seinen
Provider, und ein Claude-Modell gehoert nicht zu Echo. Fail-closed, aber der
erste dokumentierte Trockenlauf endete mit einer Kennung, die auf das Falsche
zeigt. `agent.chain.env.example` setzte kein Modell und lief.

Deshalb wird jede Vorlage hier durch dieselbe Funktion geschickt, die auch der
Worker beim Start ruft. Eine Vorlage, die nicht startet, ist keine.
"""

from __future__ import annotations

import pathlib
import unittest

import providers

ROOT = pathlib.Path(__file__).resolve().parents[2]
NAS = ROOT / "nas-startup"
VORLAGEN = sorted(NAS.glob("workforce-agent/*.env.example")) + sorted(NAS.glob("chain-test/agent*.env.example"))


def lesen(pfad: pathlib.Path) -> dict[str, str]:
    werte: dict[str, str] = {}
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if zeile and not zeile.startswith("#") and "=" in zeile:
            schluessel, _, wert = zeile.partition("=")
            werte[schluessel.strip()] = wert.strip()
    return werte


class EnvExampleTest(unittest.TestCase):
    def test_the_templates_are_found(self) -> None:
        namen = [p.name for p in VORLAGEN]
        self.assertIn("workforce-agent.env.example", namen)
        self.assertIn("agent.chain.env.example", namen)

    def test_every_template_builds_its_provider(self) -> None:
        for pfad in VORLAGEN:
            env = lesen(pfad)
            if "AGENT_PROVIDER" not in env:
                continue
            with self.subTest(vorlage=pfad.name):
                provider = providers.build_provider(env)
                self.assertEqual(env["AGENT_PROVIDER"], provider.name)

    def test_the_echo_templates_name_no_claude_model(self) -> None:
        # Die Bindung selbst: ein Modell gehoert zu seinem Provider.
        for pfad in VORLAGEN:
            env = lesen(pfad)
            if env.get("AGENT_PROVIDER") == "echo":
                with self.subTest(vorlage=pfad.name):
                    self.assertNotIn("AGENT_MODEL", env,
                                     "ein Modellwert neben Echo ist der Befund G-090")

    def test_the_historical_template_would_be_caught(self) -> None:
        env = lesen(NAS / "workforce-agent" / "workforce-agent.env.example")
        env["AGENT_MODEL"] = "claude-opus-5"
        with self.assertRaises(providers.ProviderError) as fehler:
            providers.build_provider(env)
        self.assertIn("AGENT_MODEL_PROVIDER_MISMATCH", str(fehler.exception))


if __name__ == "__main__":
    unittest.main()
