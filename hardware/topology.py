import re
from core.executor import is_windows, run_powershell_json, run_tool

def get_memory_topology():
    if is_windows():
        query = r"""$ErrorActionPreference='Stop'; $arrays=@(Get-CimInstance Win32_PhysicalMemoryArray); $modules=@(Get-CimInstance Win32_PhysicalMemory | Select-Object DeviceLocator,Capacity,Speed,Manufacturer,PartNumber); $max=0; $slots=0; foreach($a in $arrays){$slots += [int]$a.MemoryDevices; if($a.MaxCapacity -gt $max){$max=[int64]$a.MaxCapacity}}; [pscustomobject]@{TotalSlots=$slots; MaximumCapacityBytes=([int64]$max * 1024); Modules=$modules} | ConvertTo-Json -Depth 5 -Compress"""
        result = run_powershell_json(query)
        if result["ok"] and result["data"]:
            d = result["data"]
            modules = d.get("Modules") or []
            if isinstance(modules, dict):
                modules = [modules]
            installed = []
            for m in modules:
                cap = int(m.get("Capacity") or 0)
                if cap > 0:
                    installed.append({
                        "size": f"{round(cap / (1024 ** 3), 2)} GB",
                        "speed": f"{m.get('Speed') or 'Unknown'} MT/s",
                        "locator": m.get("DeviceLocator") or "Unknown",
                        "manufacturer": m.get("Manufacturer") or "Unknown",
                        "part_number": m.get("PartNumber") or "Unknown"
                    })
            total_slots = int(d.get("TotalSlots") or 0)
            max_bytes = int(d.get("MaximumCapacityBytes") or 0)
            return {
                "available": bool(total_slots or installed),
                "maximum_capacity": f"{round(max_bytes / (1024 ** 3), 2)} GB" if max_bytes else None,
                "maximum_capacity_gb": round(max_bytes / (1024 ** 3), 2) if max_bytes else None,
                "total_slots": total_slots or None,
                "used_slots": len(installed),
                "free_slots": max(total_slots - len(installed), 0) if total_slots else None,
                "installed_modules": installed,
                "source": "Windows CIM Win32_PhysicalMemoryArray/Win32_PhysicalMemory",
                "note": "Windows reports firmware memory-device entries. These do not prove that modules are physically removable or upgradeable; confirm the exact laptop model specifications."
            }
        return {"available": False, "maximum_capacity": None, "total_slots": None,
                "used_slots": None, "free_slots": None, "installed_modules": [],
                "note": result.get("error") or "Windows firmware memory information is unavailable."}

    result = run_tool("memory_topology")
    if not result["ok"]:
        return {"available": False, "maximum_capacity": None, "total_slots": None,
                "used_slots": None, "free_slots": None, "installed_modules": [],
                "note": result["error"]}
    output = result["stdout"]
    max_match = re.search(r"Maximum Capacity:\s*(.+)", output, re.IGNORECASE)
    blocks = re.split(r"(?m)^\s*Memory Device\s*$", output)
    slots, installed = 0, []
    for block in blocks[1:]:
        size = re.search(r"(?m)^\s*Size:\s*(.+)$", block)
        if not size:
            continue
        slots += 1
        value = size.group(1).strip()
        if "no module installed" in value.lower() or value.lower() == "unknown":
            continue
        speed = re.search(r"(?m)^\s*(?:Configured Memory Speed|Speed):\s*(.+)$", block)
        locator = re.search(r"(?m)^\s*Locator:\s*(.+)$", block)
        installed.append({"size": value, "speed": speed.group(1).strip() if speed else "Unknown",
                          "locator": locator.group(1).strip() if locator else "Unknown"})
    return {"available": True, "maximum_capacity": max_match.group(1).strip() if max_match else None,
            "total_slots": slots, "used_slots": len(installed),
            "free_slots": max(slots - len(installed), 0), "installed_modules": installed,
            "source": "dmidecode", "note": None if max_match else "Firmware did not report maximum capacity."}
