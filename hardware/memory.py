import re
import psutil
from core.executor import is_windows, run_powershell_json, run_tool

def get_memory_info():
    mem = psutil.virtual_memory()
    if is_windows():
        query = r"""$ErrorActionPreference='Stop'; $cs=Get-CimInstance Win32_ComputerSystem; $modules=@(Get-CimInstance Win32_PhysicalMemory); $installed=($modules | Measure-Object -Property Capacity -Sum).Sum; [pscustomobject]@{InstalledBytes=[int64]$installed; UsableBytes=[int64]$cs.TotalPhysicalMemory; ModuleCount=$modules.Count} | ConvertTo-Json -Compress"""
        result = run_powershell_json(query)
        if result["ok"] and result["data"]:
            d = result["data"]
            installed = int(d.get("InstalledBytes") or d.get("UsableBytes") or mem.total)
            usable = int(d.get("UsableBytes") or mem.total)
            return {
                "available": True,
                "total_bytes": installed,
                "available_bytes": mem.available,
                "used_bytes": max(usable - mem.available, 0),
                "total_gb": round(installed / (1024 ** 3), 2),
                "installed_gb": round(installed / (1024 ** 3), 2),
                "usable_total_gb": round(usable / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "used_percent": mem.percent,
                "module_count": int(d.get("ModuleCount") or 0),
                "source": "Windows CIM Win32_PhysicalMemory",
                "note": "Installed module capacity and Windows-usable memory can differ because of hardware-reserved memory."
            }

    result = {
        "available": True, "total_bytes": mem.total, "available_bytes": mem.available,
        "used_bytes": mem.used, "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "used_percent": mem.percent, "source": "psutil"
    }
    free_cmd = run_tool("memory")
    result["free_command_available"] = free_cmd["ok"]
    try:
        values = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as file:
            for line in file:
                match = re.match(r"([^:]+):\s+(\d+)\s+kB", line)
                if match:
                    values[match.group(1)] = int(match.group(2))
        if values.get("MemTotal"):
            result["source"] = "/proc/meminfo"
            result["total_gb"] = round(values["MemTotal"] / (1024 ** 2), 2)
            result["available_gb"] = round(values.get("MemAvailable", 0) / (1024 ** 2), 2)
    except (OSError, ValueError):
        result["proc_meminfo_available"] = False
    return result
