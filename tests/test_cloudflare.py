import pytest

from cloudflare_nginx import (
    CloudflareDownloadError,
    download,
    get_cloudflare_ranges,
)


def test_download_success(mocker):
    response = mocker.Mock()
    response.status = 200
    response.data = b"192.0.2.0/24\n"

    mock_request = mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=response,
    )

    result = download("https://example.com/test")

    assert result == b"192.0.2.0/24\n"

    mock_request.assert_called_once_with(
        "GET",
        "https://example.com/test",
        timeout=10,
    )


def test_download_http_error(mocker):
    response = mocker.Mock()
    response.status = 500

    mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=response,
    )

    with pytest.raises(
        CloudflareDownloadError,
        match="Returned HTTP 500",
    ):
        download("https://example.com/test")


def test_download_404(mocker):
    response = mocker.Mock()
    response.status = 404

    mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=response,
    )

    with pytest.raises(CloudflareDownloadError):
        download("https://example.com/test")


def test_download_request_failure(mocker):
    mocker.patch(
        "cloudflare_nginx.http.request",
        side_effect=OSError("connection failed"),
    )

    with pytest.raises(OSError, match="connection failed"):
        download("https://example.com/test")


def test_get_cloudflare_ipv4_ranges(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=(
            b"192.0.2.0/24\n"
            b"198.51.100.0/24\n"
        ),
    )

    result = get_cloudflare_ranges(4)

    assert result == [
        "192.0.2.0/24",
        "198.51.100.0/24",
    ]


def test_get_cloudflare_ipv6_ranges(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=(
            b"2001:db8::/32\n"
            b"2001:db8:1::/48\n"
        ),
    )

    result = get_cloudflare_ranges(6)

    assert result == [
        "2001:db8::/32",
        "2001:db8:1::/48",
    ]
