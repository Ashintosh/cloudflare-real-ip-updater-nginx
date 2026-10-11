# Cloudflare Nginx IP Updater

A Python utility that automatically updates Cloudflare's trusted
IPv4 and IPv6 IP ranges in Nginx for real IP resolution. It
generates the configuration, tests it, and reloads Nginx if
the test passes. If validation or reloading fails, it attempts
to restore the previous configuration.

> **Note:** This is an early version of the script. Bugs are
expected, and behaviour may change.

## Requirements

- Python 3.10+
- Nginx with `ngx_http_realip_module`
- systemd
- Root privileges or equivalent permissions
- urllib3

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/Ashintosh/cloudflare-ip-updater-nginx
cd cloudflare-ip-updater-nginx
pip install -r requirements.txt
```

## Usage

Run the updater:

```bash
sudo python3 cloudflare_nginx.py
```

By default, the script uses `/etc/nginx/conf.d`. To specify another directory:

```bash
sudo env NGINX_CONFIG_DIR=/path/to/conf.d python3 cloudflare_nginx.py
```

The target directory must exist, and `cloudflare-ips.conf` must already exist for
the initial backup.

## How It Works

1. Downloads the latest IPv4 and IPv6 ranges from official Cloudflare endpoints.
2. Generates `set_real_ip_from` directives in `cloudflare-ips.conf`.
3. Backs up the existing configuration and installs the new one.
4. Tests the configuration with Nginx.
5. Reloads Nginx if the test passes; otherwise, attempts to restore the previous configuration.

## Testing

Install development dependencies and run the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

Run Ruff:

```bash
ruff check .
```

## Important

The generated configuration trusts the IP ranges published by Cloudflare. To restore
visitor IP addresses, configure Nginx to use Cloudflare's CF-Connecting-IP header and
include the generated file in your existing `http` configuration.

The script's validation uses an isolated Nginx configuration containing files from `conf.d`;
it does not validate the entire production Nginx configuration. Rollback is best-effort.

Cloudflare IP ranges are retrieved from:

- https://www.cloudflare.com/ips-v4/
- https://www.cloudflare.com/ips-v6/
