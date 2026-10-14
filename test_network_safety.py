import socket

from Backend.security.dns_checker import check_dns
from Backend.security.network_safety import NonPublicAddressError, resolve_public_addresses
from Backend.security.ssl_checker import check_ssl


def _address_result(address, port):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", (address, port))]


def test_resolver_rejects_loopback_and_private_addresses(monkeypatch):
    for address in ("127.0.0.1", "10.0.0.8", "169.254.10.2"):
        monkeypatch.setattr(socket, "getaddrinfo", lambda host, port, type, ip=address: _address_result(ip, port))
        try:
            resolve_public_addresses("internal.example", 443)
        except NonPublicAddressError:
            pass
        else:
            raise AssertionError(f"non-public address was accepted: {address}")


def test_dns_and_ssl_report_non_public_targets_unavailable(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port, type: _address_result("127.0.0.1", port))

    dns_result = check_dns("http://localhost")
    ssl_result = check_ssl("https://localhost")

    assert dns_result["resolves"] is False
    assert "non-public" in dns_result["error"].lower()
    assert ssl_result["valid"] is False
    assert "non-public" in ssl_result["error"].lower()


def test_resolver_accepts_public_address(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, port, type: _address_result("8.8.8.8", port))

    addresses = resolve_public_addresses("dns.example", 443)

    assert addresses == ((socket.AF_INET, ("8.8.8.8", 443)),)
