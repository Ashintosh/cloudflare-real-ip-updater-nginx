
import pytest
import urllib3

from cloudflare_nginx import (
    EmptyResponseError,
    HTTPDownloadError,
    IPValidationError,
    download,
    get_cloudflare_ranges,
)


def mock_response(mocker, status=200, data=b""):
    response = mocker.Mock()
    response.status = status
    response.data = data
    return response


def test_download_success(mocker):
    url = "https://example.com/test"
    response = mock_response(
        mocker,
        data=b"192.0.2.0/24\n",
    )

    mock_request = mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=response,
    )

    result = download(url)

    assert result == b"192.0.2.0/24\n"

    mock_request.assert_called_once()
    method, requested_url = mock_request.call_args.args
    timeout = mock_request.call_args.kwargs["timeout"]

    assert method == "GET"
    assert requested_url == url
    assert isinstance(timeout, urllib3.Timeout)
    assert timeout.total == 10


@pytest.mark.parametrize("status", [404, 500, 503])
def test_download_http_error(mocker, status):
    mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=mock_response(mocker, status=status),
    )

    with pytest.raises(
        HTTPDownloadError,
        match=f"Returned HTTP {status}",
    ):
        download("https://example.com/test")


def test_download_request_failure(mocker):
    mocker.patch(
        "cloudflare_nginx.http.request",
        side_effect=urllib3.exceptions.HTTPError(
            "connection failed"
        ),
    )

    with pytest.raises(
        HTTPDownloadError,
        match="connection failed",
    ):
        download("https://example.com/test")


def test_download_empty_body(mocker):
    mocker.patch(
        "cloudflare_nginx.http.request",
        return_value=mock_response(mocker, data=b""),
    )

    with pytest.raises(ValueError, match="Empty HTTP response"):
        download("https://example.com/test")


def test_get_cloudflare_ipv4_ranges(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=(
            b"192.0.2.0/24\n"
            b"198.51.100.0/24\n"
        ),
    )

    assert get_cloudflare_ranges(4) == [
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

    assert get_cloudflare_ranges(6) == [
        "2001:db8::/32",
        "2001:db8:1::/48",
    ]


def test_get_cloudflare_ranges_removes_duplicates(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=(
            b"192.0.2.0/24\n"
            b"198.51.100.0/24\n"
            b"192.0.2.0/24\n"
        ),
    )

    assert get_cloudflare_ranges(4) == [
        "192.0.2.0/24",
        "198.51.100.0/24",
    ]


def test_get_cloudflare_ranges_invalid_cidr(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=b"not-a-cidr\n",
    )

    with pytest.raises(IPValidationError):
        get_cloudflare_ranges(4)


def test_get_cloudflare_ranges_wrong_ip_version(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=b"2001:db8::/32\n",
    )

    with pytest.raises(IPValidationError, match="Unexpected IP version"):
        get_cloudflare_ranges(4)


def test_get_cloudflare_ranges_whitespace_only(mocker):
    mocker.patch(
        "cloudflare_nginx.download",
        return_value=b"  \n\n",
    )

    with pytest.raises(EmptyResponseError):
        get_cloudflare_ranges(4)
