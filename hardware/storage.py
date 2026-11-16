import json
import psutil
from core.executor import is_windows, run_powershell_json, run_tool

def get_storage_info():
    if is_windows():
        query = r"""$ErrorActionPreference='Stop'; $disks=@(Get-CimInstance Win32_DiskDrive | ForEach-Object { $d=$_; $physical=$null; try {$physical=Get-PhysicalDisk | Where-Object {$_.FriendlyName -eq $d.Model -or $_.SerialNumber -eq $d.SerialNumber} | Select-Object -First 1} catch {}; $kind='Unknown'; $bus='Unknown'; if($physical){$kind=[string]$physical.MediaType; $bus=[string]$physical.BusType}; [pscustomobject]@{Name=$d.DeviceID; Model=$d.Model; SizeBytes=[int64]$d.Size; MediaType=$kind; BusType=$bus} }); $disks | ConvertTo-Json -Depth 4 -Compress"""
        result = run_powershell_json(query)
        if result["ok"]:
            rows = result["data"] if isinstance(result["data"], list) else [result["data"]]
            devices = []
            for d in rows:
                if not d:
                    continue
                size = int(d.get("SizeBytes") or 0)
                devices.append({
                    "name": d.get("Name") or "Physical disk",
                    "model": d.get("Model") or "Unknown",
                    "size_bytes": size,
                    "size_gb": round(size / (1024 ** 3), 2) if size else None,
                    "type": d.get("MediaType") or "Unknown",
                    "transport": d.get("BusType") or "Unknown"
                })
            return {"available": bool(devices), "devices": devices, "source": "Windows CIM Win32_DiskDrive"}
        return {"available": False, "devices": [], "source": "Windows CIM",
                "note": result.get("error") or "Physical disk details unavailable."}

    result = run_tool("storage")
    if result["ok"]:
        try:
            parsed = json.loads(result["stdout"])
            devices = []
            for item in parsed.get("blockdevices", []):
                if item.get("type") != "disk":
                    continue
                transport = (item.get("tran") or "").lower()
                rotational = item.get("rota")
                if transport == "nvme":
                    kind = "NVMe SSD"
                elif rotational is False or str(rotational).lower() in ("0", "false"):
                    kind = "SSD (interface not confirmed)"
                elif rotational is True or str(rotational).lower() in ("1", "true"):
                    kind = "HDD"
                else:
                    kind = "Unknown"
                devices.append({"name": item.get("name", "Unknown"), "size_bytes": item.get("size"),
                    "size_gb": round(int(item["size"]) / (1024 ** 3), 2) if str(item.get("size", "")).isdigit() else None,
                    "model": item.get("model") or "Unknown", "transport": transport or "Unknown", "type": kind})
            return {"available": bool(devices), "devices": devices, "source": "lsblk"}
        except (ValueError, TypeError, KeyError):
            pass
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({"device": part.device, "mountpoint": part.mountpoint,
                               "size_gb": round(usage.total / (1024 ** 3), 2), "type": "Unknown"})
        except (PermissionError, OSError):
            continue
    return {"available": bool(partitions), "devices": partitions, "source": "psutil fallback",
            "note": "Physical disk model and NVMe/SATA interface are unavailable without lsblk."}
