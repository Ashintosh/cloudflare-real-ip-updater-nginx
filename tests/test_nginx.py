import subprocess

import pytest

from cloudflare_nginx import (
    NGINX_CONFIG,
    NGINX_TIMEOUT,
    TEST_NGINX_CONFIG,
    NginxReloadError,
    reload_nginx,
    validate_nginx_config,
)

# Nginx configuration validation


def test_validate_nginx_config_success(mocker):
    result = mocker.Mock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = "nginx: configuration file test is successful"

    mock_run = mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert validate_nginx_config() is True

    mock_run.assert_called_once_with(
        [
            "nginx",
            "-t",
            "-c",
            str(NGINX_CONFIG),
        ],
        capture_output=True,
        text=True,
        timeout=NGINX_TIMEOUT,
        check=False,
    )


def test_validate_nginx_config_custom_path(mocker, tmp_path):
    config_path = tmp_path / "test-nginx.conf"

    result = mocker.Mock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""

    mock_run = mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert validate_nginx_config(config_path) is True

    args, kwargs = mock_run.call_args
    assert args[0] == [
        "nginx",
        "-t",
        "-c",
        str(config_path),
    ]
    assert kwargs["timeout"] == NGINX_TIMEOUT


def test_validate_nginx_config_failure(mocker, capsys):
    result = mocker.Mock()
    result.returncode = 1
    result.stdout = ""
    result.stderr = "nginx: configuration file test failed"

    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert validate_nginx_config() is False

    captured = capsys.readouterr()
    assert "configuration file test failed" in captured.out


def test_validate_nginx_config_prints_stdout_and_stderr(
    mocker,
    capsys,
):
    result = mocker.Mock()
    result.returncode = 0
    result.stdout = "validation output\n"
    result.stderr = "configuration test successful\n"

    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    assert validate_nginx_config(TEST_NGINX_CONFIG) is True

    captured = capsys.readouterr()
    assert "validation output" in captured.out
    assert "configuration test successful" in captured.out


def test_validate_nginx_config_timeout(mocker, capsys):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd=["nginx", "-t"],
            timeout=NGINX_TIMEOUT,
        ),
    )

    assert validate_nginx_config() is False

    captured = capsys.readouterr()
    assert "Nginx validation timed out" in captured.out


def test_validate_nginx_config_os_error(mocker):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=OSError("nginx not found"),
    )

    with pytest.raises(OSError, match="nginx not found"):
        validate_nginx_config()


# Nginx service reload


def test_reload_nginx_success(mocker):
    result = mocker.Mock()
    result.returncode = 0
    result.stdout = ""
    result.stderr = ""

    mock_run = mocker.patch(
        "cloudflare_nginx.subprocess.run",
        return_value=result,
    )

    reload_nginx()

    mock_run.assert_called_once_with(
        ["systemctl", "reload", "nginx"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_reload_nginx_failure(mocker):
    result = mocker.Mock()
    result.returncode = 1
    result.stdout = ""
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


def test_reload_nginx_timeout(mocker):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=subprocess.TimeoutExpired(
            cmd=["systemctl", "reload", "nginx"],
            timeout=30,
        ),
    )

    with pytest.raises(
        NginxReloadError,
        match="reload timed out",
    ):
        reload_nginx()


def test_reload_nginx_os_error(mocker):
    mocker.patch(
        "cloudflare_nginx.subprocess.run",
        side_effect=OSError("systemctl not found"),
    )

    with pytest.raises(OSError, match="systemctl not found"):
        reload_nginx()
