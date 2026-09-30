"""04 System Monitoring: report CPU, RAM, disk and top processes; alert on thresholds."""
import argparse
import logging
import time

import psutil


def snapshot(disk_path: str = "/") -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage(disk_path).percent,
    }


def top_processes(n: int = 5) -> list[dict]:
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_percent"]):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda i: i["memory_percent"] or 0, reverse=True)
    return procs[:n]


def check_thresholds(stats: dict, limits: dict) -> list[str]:
    """Return a warning for every metric above its limit."""
    return [
        f"{metric} at {stats[metric]:.1f}% (limit {limit}%)"
        for metric, limit in limits.items()
        if stats.get(metric, 0) > limit
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=0, help="seconds between checks (0 = run once)")
    parser.add_argument("--cpu", type=float, default=85)
    parser.add_argument("--ram", type=float, default=85)
    parser.add_argument("--disk", type=float, default=90)
    parser.add_argument("--log", default="system_monitor.log")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(args.log), logging.StreamHandler()],
    )
    limits = {"cpu_percent": args.cpu, "ram_percent": args.ram, "disk_percent": args.disk}
    while True:
        stats = snapshot()
        logging.info("CPU %(cpu_percent).1f%% | RAM %(ram_percent).1f%% | Disk %(disk_percent).1f%%", stats)
        for warning in check_thresholds(stats, limits):
            logging.warning(warning)
        for p in top_processes():
            logging.info("  pid=%-7s %-25s mem=%.1f%%", p["pid"], p["name"], p["memory_percent"] or 0)
        if not args.interval:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
