"""Cross-platform system and network probe utilities."""

import platform
import shutil
import socket


def is_port_in_use(port: int, host: str = "127.0.0.1", timeout: float = 0.3) -> bool:
    """Check if a network port is actively bound/listening on the host."""
    if port <= 0 or port > 65535:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            res = s.connect_ex((host, port))
            return res == 0
    except OSError:
        return False


def get_os_info() -> dict[str, str]:
    """Retrieve host operating system and machine architecture metadata safely."""
    system_name = platform.system()
    release = platform.release()
    arch = platform.machine() or platform.processor() or "unknown"

    return {
        "os_name": system_name,
        "os_version": release,
        "architecture": arch,
    }


def find_executable(name: str) -> str | None:
    """Look up the path to an executable in a cross-platform manner."""
    return shutil.which(name)
