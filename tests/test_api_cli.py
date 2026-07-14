from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from protocol_fuzzer.api import create_app
from protocol_fuzzer.cli import main


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_healthz(client: TestClient) -> None:
    assert client.get("/healthz").json()["status"] == "ok"


def test_protocols(client: TestClient) -> None:
    assert set(client.get("/protocols").json()["protocols"]) == {"http", "tlv", "jsonrpc"}


def test_campaign_endpoint(client: TestClient) -> None:
    response = client.post(
        "/campaign", json={"protocol": "tlv", "iterations": 500, "seed": 1337}
    ).json()
    assert response["result"]["unique_crashes"] >= 2
    assert response["regressions_reproduced"] is True


def test_dashboard(client: TestClient) -> None:
    assert client.get("/").status_code == 200


def _capture(capsys: pytest.CaptureFixture[str]) -> object:
    return json.loads(capsys.readouterr().out)


def test_cli_fuzz(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["fuzz", "--protocol", "http", "--iterations", "500"]) == 0
    assert _capture(capsys)["protocol"] == "http"


def test_cli_regress(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["regress", "--protocol", "tlv", "--iterations", "500"]) == 0
    payload = _capture(capsys)
    assert payload["reproduced"] == payload["unique_crashes"]


def test_cli_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(["report", "--protocol", "jsonrpc", "--iterations", "500", "--out", str(tmp_path)])
        == 0
    )
    assert Path(_capture(capsys)["json"]).exists()


def test_cli_benchmark(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["benchmark", "--iterations", "2", "--out", str(tmp_path)]) == 0
    assert _capture(capsys)["deterministic"] is True
