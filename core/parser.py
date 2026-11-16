def summarize_hardware(info):
    output = []
    cpu, mem = info.get("cpu", {}), info.get("memory", {})
    storage, gpu, topo = info.get("storage", {}), info.get("gpu", {}), info.get("memory_topology", {})
    output.append(f"CPU: {cpu.get('processor', 'Unavailable')}; {cpu.get('physical_cores', 'Unknown')} physical cores; {cpu.get('logical_threads', 'Unknown')} logical threads.")
    output.append(f"RAM: {mem.get('total_gb', 'Unknown')} GB installed; {mem.get('available_gb', 'Unknown')} GB available.")
    if mem.get("usable_total_gb"):
        output.append(f"Windows-usable RAM: {mem.get('usable_total_gb')} GB.")
    if storage.get("devices"):
        for d in storage["devices"]:
            output.append(f"Storage: {d.get('model', d.get('name', d.get('device', 'Disk')))}; {d.get('size_gb', 'Unknown')} GB; {d.get('type', 'Unknown')}.")
    else:
        output.append("Storage details unavailable.")
    output.append("GPU: " + ("; ".join(gpu.get("devices", [])) if gpu.get("available") else gpu.get("note", "Unavailable")))
    if topo.get("available"):
        output.append(f"RAM slots: {topo.get('used_slots')} used / {topo.get('total_slots')} reported; maximum firmware capacity: {topo.get('maximum_capacity') or 'Not reported'}.")
    else:
        output.append("RAM topology: " + topo.get("note", "Unavailable"))
    return "\\n".join(output)
