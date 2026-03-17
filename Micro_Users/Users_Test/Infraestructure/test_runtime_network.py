import pytest

from Users_Infrastruture import runtime_network


def test_normalize_local_url_for_container_keeps_url_when_not_in_docker(monkeypatch) -> None:
    monkeypatch.setattr(runtime_network, "running_in_docker", lambda: False)

    raw = "http://localhost:8200/v1/secret"
    assert runtime_network.normalize_local_url_for_container(raw) == raw


@pytest.mark.parametrize(
    ("raw_url", "expected_url"),
    [
        (
            "http://localhost:8200/v1/secret",
            "http://host.docker.internal:8200/v1/secret",
        ),
        (
            "https://127.0.0.1:9443/api/health",
            "https://host.docker.internal:9443/api/health",
        ),
    ],
)
def test_normalize_local_url_for_container_replaces_local_hosts(monkeypatch, raw_url, expected_url) -> None:
    monkeypatch.setattr(runtime_network, "running_in_docker", lambda: True)

    normalized = runtime_network.normalize_local_url_for_container(raw_url)

    assert normalized == expected_url


def test_normalize_local_url_for_container_keeps_remote_host_in_docker(monkeypatch) -> None:
    monkeypatch.setattr(runtime_network, "running_in_docker", lambda: True)

    raw = "https://10.0.0.20:8200/v1/secret"
    assert runtime_network.normalize_local_url_for_container(raw) == raw
