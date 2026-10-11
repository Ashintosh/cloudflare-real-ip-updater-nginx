# Cloudflare Nginx IP Updater

A Python utility that downloads Cloudflare's published IPv4
and IPv6 ranges and generates an Nginx include file for
real-IP resolution. It validates the generated include,
installs it, tests the full Nginx configuration, and reloads
Nginx only if that production configuration test passes. If
installation validation or reloading fails, it attempts to
restore the previous include.

> **Note:** This is an early version of the script. Bugs are
expected, and behaviour may change.

## Requirements

- Python 3.10+
- Nginx with `ngx_http_realip_module`
- systemd, with the Nginx service manages as `nginx`
- Root privileges or equivalent permissions to write the configuration files, run Nginx validation, and reload the service
- `urllib3`

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

`NGINX_CONFIG_DIR` changes the directory used for the generated include
and temporary files. The main Nginx configuration used for the production
test remains `/etc/nginx/nginx.conf`.

The target directory must already exist and be writable by the updater.
The managed include is named `cf-ips.conf`. It may already exist, but it
does not have to exist on the first run. If it exists, the updater
preserves a backup before replacing it.

If `.cf-ips.conf.backup` is already present, the updater stops without 
making changes. Inspect the backup and recover or remove it deliberately
before running the updater again; it may be the only remaining copy of
the previous configuration after an interrupted or unsuccessful recovery.

## Nginx Configuration

The updater does not edit `nginx.conf` or add an include directive for
you. Configure Nginx so that the generated `cf-ips.conf` is included
inside the `http` context. For example, a typical configuration may
already include `/etc/nginx/conf.d/*.conf` from within `http`.

The generated file sets:

- `real_ip_header CF-Connecting-IP;`
- `real_ip_recursive on;`
- One `set_real_ip_from` directive for each validated Cloudflare CIDR range.

Only trust these published ranges when requests reaching Nginx are
actually coming through Cloudflare. Do not use this configuration as
a reason to trust client-supplied `CF-Connecting-IP` headers from 
untrusted sources.

## How It Works

1. Downloads Cloudflare's IPv4 and IPv6 range lists from the official endpoints.
2. Parses each non-empty line as a CIDR, checks that the address family matches the requested list, and removes duplicate ranges.
3. Writes a temporary candidate include and a minimal temporary Nginx configuration, then runs `nginx -t` against that isolated configuration.
4. Backs up the existing `cf-ips.conf`, if present, an atomically replaces it with the candidate file.
5. Runs `nginx -t` against `/etc/nginx/nginx.conf` to validate the full production configuration with the new include in place.
6. Reloads Nginx only if the production configuration test passes.
7. If the production test fails, attempts to restore the previous include. If reloading fails, it attempts to restore the previous include, validate the restored production configuration, and reload Nginx again.

The isolated test checks the generated candidate in a minimal Nginx configuration; it does not load the files from `conf.d` or reproduce the full production setup. The full production configuration test is therefore an additional and authoritative check before the updater attempts a reload.

Rollback is best-effort, not guaranteed. If restoration, validation, or the recovery reload fails, the updater reports an error and may retain `.cf-ips.conf.backup` for manual recovery. The updater returns a non-zero exit status when an update fails, even if it successfully restores the previous configuration.

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

## Limitations and Recovery Notes

- The updater validates CIDR syntax and address families, but does not compare the downloaded ranges against and expected count or other completeness baseline. Syntactically valid but incomplete upstream data could pass parsing.
- The updater does not lock against concurrent runs. Avoid running multiple instances at the same time.
- A reload timeout leaves the actual reload outcome uncertain; the updater follows its recovery path, but cannot guarantee the service state if recovery also fails.
- Temporary candidate, test, and restore files are cleaned up when the process exits. The backup is handled separately and is deliberately retained when recovery may be incomplete.

## Cloudflare Endpoints

- IPv4: https://www.cloudflare.com/ips-v4/
- IPv6: https://www.cloudflare.com/ips-v6/

## Planned

- Add tests for rollback and recovery failure scenarios.
- Prevent multiple updater instances from running simultaneously.
- Detect incomplete Cloudflare IP range responses.
- Improve recovery handling when an Nginx reload times out.
