import pytest

from cloudflare_nginx import (
    NginxReloadError,
    reload_nginx,
    check_nginx_config,
)


def test_nginx_config_success(mocker):
    result = mocker.Mock()
    result.returncode = 0
    result.stderr = ""

    mock_run = mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert check_nginx_config() is True

    mock_run.assert_called_once_with(
        [
            "nginx",
            "-t",
            "-c",
            "/etc/nginx/conf.d/.nginx-cloudflare-test.conf.tmp",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_nginx_config_failure(mocker, capsys):
    result = mocker.Mock()
    result.returncode = 1
    result.stderr = "nginx: configuration file test failed"

    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert check_nginx_config() is False

    captured = capsys.readouterr()

    assert "configuration file test failed" in captured.out


def test_nginx_config_subprocess_error(mocker):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=OSError("nginx not found"),
    )

    with pytest.raises(OSError, match="nginx not found"):
        check_nginx_config()


def test_reload_nginx_success(mocker):
    result = mocker.Mock()
    result.returncode = 0
    result.stderr = ""

    mock_run = mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    reload_nginx()

    mock_run.assert_called_once_with(
        [
            "systemctl",
            "reload",
            "nginx",
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_reload_nginx_failure(mocker):
    result = mocker.Mock()
    result.returncode = 1
    result.stderr = "Failed to reload nginx"

    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    with pytest.raises(
        NginxReloadError,
        match="Failed to reload nginx",
    ):
        reload_nginx()


def test_reload_nginx_subprocess_error(mocker):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=OSError("systemctl not found"),
    )

    with pytest.raises(OSError, match="systemctl not found"):
        reload_nginx()
