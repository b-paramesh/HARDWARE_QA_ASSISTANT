from core.executor import is_windows, run_powershell_json, run_tool

def get_gpu_info():
    if is_windows():
        query = r"""$ErrorActionPreference='Stop'; Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion,VideoProcessor | ConvertTo-Json -Compress"""
        result = run_powershell_json(query)
        if result["ok"]:
            rows = result["data"] if isinstance(result["data"], list) else [result["data"]]
            devices = [r.get("Name") for r in rows if r and r.get("Name")]
            return {"available": bool(devices), "devices": devices,
                    "details": rows, "source": "Windows CIM Win32_VideoController",
                    "note": None if devices else "No video controller was reported."}
        return {"available": False, "devices": [], "note": result.get("error")}
    result = run_tool("gpu")
    if not result["ok"]:
        return {"available": False, "devices": [], "note": result["error"]}
    devices = []
    for line in result["stdout"].splitlines():
        low = line.lower()
        if any(term in low for term in ("vga compatible controller", "3d controller", "display controller")):
            devices.append(line.split(": ", 1)[-1].strip())
    return {"available": bool(devices), "devices": devices, "source": "lspci",
            "note": None if devices else "No display controller was found in lspci output."}
