"""System metrics collection for the UI."""

from __future__ import annotations

import re
import subprocess
import threading
import time

import psutil

from jarvis.ui.constants import OS


class SystemMetrics:
    """Collect CPU, memory, network, GPU, and temperature metrics."""

    def __init__(self):
        self.cpu = 0.0
        self.memory = 0.0
        self.network = 0.0
        self.gpu = -1.0
        self.temperature = -1.0
        self._lock = threading.Lock()
        self._last_net = psutil.net_io_counters()
        self._last_net_time = time.time()
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self) -> None:
        while self._running:
            try:
                self._update()
            except Exception:
                pass
            time.sleep(1.5)

    def stop(self) -> None:
        """Stop the metrics collection thread."""
        self._running = False

    def snapshot(self) -> dict[str, float]:
        """Return a thread-safe snapshot of current metrics."""
        with self._lock:
            return {
                "cpu": self.cpu,
                "memory": self.memory,
                "network": self.network,
                "gpu": self.gpu,
                "temperature": self.temperature,
            }

    def _update(self) -> None:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent

        nc = psutil.net_io_counters()
        now = time.time()
        dt = now - self._last_net_time
        if dt > 0:
            sent = (nc.bytes_sent - self._last_net.bytes_sent) / dt
            recv = (nc.bytes_recv - self._last_net.bytes_recv) / dt
            network = (sent + recv) / (1024 * 1024)
        else:
            network = 0.0
        self._last_net = nc
        self._last_net_time = now

        gpu = self._get_gpu()
        temperature = self._get_temperature()

        with self._lock:
            self.cpu = cpu
            self.memory = memory
            self.network = network
            self.gpu = gpu
            self.temperature = temperature

    def _get_gpu(self) -> float:
        return _query_gpu_utilization(OS)

    def _get_temperature(self) -> float:
        return _query_cpu_temperature()


def _query_gpu_utilization(os_name: str) -> float:
    # NVIDIA
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            vals = [float(v.strip()) for v in result.stdout.strip().split("\n") if v.strip()]
            if vals:
                return sum(vals) / len(vals)
    except Exception:
        pass

    # AMD (Linux)
    if os_name == "Linux":
        try:
            result = subprocess.run(
                ["rocm-smi", "--showuse", "--csv"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(",")
                    if len(parts) >= 2:
                        try:
                            return float(parts[1].strip().replace("%", ""))
                        except ValueError:
                            pass
        except Exception:
            pass

        # Intel GPU
        try:
            result = subprocess.run(
                ["intel_gpu_top", "-J", "-s", "500"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if result.returncode == 0 and "Render/3D" in result.stdout:
                match = re.search(r'"busy":\s*([\d.]+)', result.stdout)
                if match:
                    return float(match.group(1))
        except Exception:
            pass

    # macOS
    if os_name == "Darwin":
        try:
            result = subprocess.run(
                ["sudo", "-n", "powermetrics", "-n", "1", "-i", "500", "--samplers", "gpu_power"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and "GPU" in result.stdout:
                match = re.search(r"GPU\s+Active:\s+([\d.]+)%", result.stdout)
                if match:
                    return float(match.group(1))
        except Exception:
            pass

    return -1.0


def _query_cpu_temperature() -> float:
    try:
        temps = psutil.sensors_temperatures()
        candidates = [
            "coretemp",
            "k10temp",
            "cpu_thermal",
            "acpitz",
            "cpu-thermal",
            "zenpower",
            "it8688",
        ]
        for name in candidates:
            if name in temps:
                entries = temps[name]
                if entries:
                    return entries[0].current
        for entries in temps.values():
            if entries:
                return entries[0].current
    except Exception:
        pass
    return -1.0
