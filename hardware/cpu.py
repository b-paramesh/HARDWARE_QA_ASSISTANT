import platform
import psutil
from core.executor import is_windows, run_powershell_json, run_tool

def get_cpu_info():
    if is_windows():
        query = r"""$ErrorActionPreference='Stop'; Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,Manufacturer | ConvertTo-Json -Compress"""
        result = run_powershell_json(query)
        if result["ok"]:
            rows = result["data"] if isinstance(result["data"], list) else [result["data"]]
            rows = [r for r in rows if r]
            if rows:
                return {
                    "available": True,
                    "processor": rows[0].get("Name") or "Unknown",
                    "architecture": platform.machine() or "Unknown",
                    "physical_cores": sum(int(r.get("NumberOfCores") or 0) for r in rows),
                    "logical_threads": sum(int(r.get("NumberOfLogicalProcessors") or 0) for r in rows),
                    "vendor": rows[0].get("Manufacturer") or "Unknown",
                    "source": "Windows Win32_Processor (CIM)",
                    "note": None
                }

    result = run_tool("cpu")
    fields = {}
    if result["ok"]:
        for line in result["stdout"].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip()] = value.strip()
    physical = psutil.cpu_count(logical=False)
    logical = psutil.cpu_count(logical=True)
    if fields.get("Core(s) per socket", "").isdigit() and fields.get("Socket(s)", "").isdigit():
        physical = int(fields["Core(s) per socket"]) * int(fields["Socket(s)"])
    return {
        "available": True,
        "processor": fields.get("Model name") or fields.get("Processor") or platform.processor() or "Unknown",
        "architecture": fields.get("Architecture", platform.machine() or "Unknown"),
        "physical_cores": physical,
        "logical_threads": int(fields["CPU(s)"]) if fields.get("CPU(s)", "").isdigit() else logical,
        "vendor": fields.get("Vendor ID", "Unavailable"),
        "source": "lscpu" if result["ok"] else "Python fallback",
        "note": result.get("error")
    }
