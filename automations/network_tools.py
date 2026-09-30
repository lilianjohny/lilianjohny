"""06 Network Automation: check host reachability, open ports, and DNS resolution.

Only scan hosts you own or are authorized to test.
"""
import argparse
import socket
from concurrent.futures import ThreadPoolExecutor

COMMON_PORTS = [22, 25, 53, 80, 110, 143, 443, 3306, 5432, 6379, 8080]


def resolve(host: str) -> str | None:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def scan_ports(host: str, ports: list[int], timeout: float = 1.0) -> list[int]:
    with ThreadPoolExecutor(max_workers=50) as pool:
        results = pool.map(lambda p: (p, is_port_open(host, p, timeout)), ports)
    return sorted(p for p, ok in results if ok)


def parse_ports(spec: str) -> list[int]:
    """Parse '22,80,8000-8010' into a list of ints."""
    ports: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            lo, hi = map(int, part.split("-"))
            ports.update(range(lo, hi + 1))
        elif part:
            ports.add(int(part))
    return sorted(ports)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("hosts", nargs="+")
    parser.add_argument("--ports", help="e.g. 22,80,443 or 8000-8100 (default: common ports)")
    parser.add_argument("--timeout", type=float, default=1.0)
    args = parser.parse_args()

    ports = parse_ports(args.ports) if args.ports else COMMON_PORTS
    for host in args.hosts:
        ip = resolve(host)
        if not ip:
            print(f"{host}: DNS resolution failed")
            continue
        open_ports = scan_ports(ip, ports, args.timeout)
        print(f"{host} ({ip}): open ports -> {open_ports or 'none'}")


if __name__ == "__main__":
    main()
