#!/usr/bin/env python3
# ...existing code...
from urllib.parse import urlparse
import socket
import argparse
import os
import sys
import json
from typing import List, Optional

import requests


def resolve_ips(hostname: str, prefer_ipv4: bool = True) -> List[str]:
    """Resolve a hostname to a list of IP addresses (IPv4 and IPv6).

    Returns a list of string IP addresses. IPv4 addresses are preferred when prefer_ipv4 is True.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise RuntimeError(f"DNS resolution failed for {hostname}: {e}")

    ips = []
    for info in infos:
        addr = info[4][0]
        if addr not in ips:
            ips.append(addr)

    if prefer_ipv4:
        # sort to put IPv4 addresses first
        ips.sort(key=lambda ip: 0 if ':' not in ip else 1)
    return ips


def query_ipqualityscore(api_key: str, ip: str, strict: bool = False, timeout: int = 8) -> dict:
    """Call the IPQualityScore API for the given IP and return parsed JSON.

    API docs: https://www.ipqualityscore.com/documentation/ip-reputation-api/overview
    Endpoint: https://ipqualityscore.com/api/json/ip/{API_KEY}/{ip_address}
    """
    if not api_key:
        raise ValueError("API key is required")
    url = f"https://ipqualityscore.com/api/json/ip/{api_key}/{ip}"
    params = {}
    if strict:
        params['strictness'] = 1
    try:
        resp = requests.get(url, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error while contacting IPQualityScore: {e}")

    if resp.status_code != 200:
        # try to include body for debugging
        text = resp.text.strip()
        raise RuntimeError(f"IPQualityScore API returned {resp.status_code}: {text}")

    try:
        return resp.json()
    except ValueError as e:
        raise RuntimeError(f"Failed to parse JSON response from IPQualityScore: {e}")


def reputation_summary(api_key: str, ip: str, strict: bool = False, timeout: int = 8) -> Optional[dict]:
    """Return a compact reputation summary for an IP by querying IPQualityScore.

    The summary contains only a few useful fields:
      - fraud_score
      - fraudulent
      - country_code
      - ISP
      - ASN
    Returns None on error or if API response doesn't include these fields.
    """
    try:
        full = query_ipqualityscore(api_key, ip, strict=strict, timeout=timeout)
    except Exception as e:
        # bubble up None to indicate not available
        return None

    # Map fields (some keys may not be present depending on subscription/tier)
    if not isinstance(full, dict):
        return None

    summary_keys = ['fraud_score', 'fraudulent', 'country_code', 'ISP', 'ASN']
    summary = {}
    for k in summary_keys:
        # IPQS uses lower-case keys for some (fraud_score, country_code, fraudulent)
        # but ISP/ASN might appear as 'ISP'/'ASN' or 'isp'/'asn' depending on response; handle both.
        if k in full:
            summary[k] = full.get(k)
            continue
        alt = k.lower()
        if alt in full:
            summary[k] = full.get(alt)
            continue
        # Some providers use different keys, attempt common alternatives
        if alt == 'isp' and 'ISP' in full:
            summary[k] = full.get('ISP')
        elif alt == 'asn' and 'ASN' in full:
            summary[k] = full.get('ASN')
        else:
            summary[k] = None

    # attach the ip for context
    summary['_ip'] = ip
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve URL to IP and check reputation via IPQualityScore API")
    parser.add_argument('url', help='URL to check (e.g. https://example.com/path)')
    parser.add_argument('--api-key', '-k', help='IPQualityScore API key (or set IPQS_API_KEY env var)')
    parser.add_argument('--all', action='store_true', help='Query IPQS for all resolved IPs instead of the first')
    parser.add_argument('--no-prefer-ipv4', dest='prefer_ipv4', action='store_false', help='Do not prefer IPv4 in resolution order')
    parser.add_argument('--strict', action='store_true', help='Enable strictness parameter for IPQS')
    parser.add_argument('--timeout', type=int, default=8, help='HTTP timeout seconds for API calls')

    args = parser.parse_args(argv)

    api_key = args.api_key or os.environ.get('IPQS_API_KEY')
    if not api_key:
        print('Error: IPQualityScore API key must be provided via --api-key or IPQS_API_KEY env var', file=sys.stderr)
        return 2

    # parse host from URL
    parsed = urlparse(args.url)
    host = parsed.hostname
    if not host:
        print(f"Error: couldn't parse hostname from URL: {args.url}", file=sys.stderr)
        return 2

    try:
        ips = resolve_ips(host, prefer_ipv4=args.prefer_ipv4)
    except Exception as e:
        print(f"Error resolving hostname: {e}", file=sys.stderr)
        return 3

    if not ips:
        print(f"No IPs resolved for {host}")
        return 3

    to_check = ips if args.all else [ips[0]]

    for ip in to_check:
        print(f"Resolved {host} -> {ip}")
        try:
            result = query_ipqualityscore(api_key, ip, strict=args.strict, timeout=args.timeout)
        except Exception as e:
            print(f"Error querying IPQualityScore for {ip}: {e}", file=sys.stderr)
            continue

        # pretty-print key fields and the full JSON
        # Show a small summary
        summary_keys = ['success','fraud_score','fraudulent','recent_abuse','country_code','region','city','ISP','ASN','bot_status']
        print("--- IPQS summary ---")
        for k in summary_keys:
            if k in result:
                print(f"{k}: {result.get(k)}")
        print("--- Full JSON response ---")
        print(json.dumps(result, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
