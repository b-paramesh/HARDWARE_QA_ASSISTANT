import os
import platform
import shutil
import subprocess

# Linux commands and arguments are fixed. User/LLM text is never passed to a shell.
COMMANDS = {
    "cpu": ("lscpu",),
    "memory": ("free", "-b"),
    "storage": ("lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,MODEL,ROTA,TRAN"),
    "gpu": ("lspci",),
    "memory_topology": ("dmidecode", "--type", "memory"),
}

def is_windows():
    return platform.system().lower() == "windows"

def get_tool_status():
    if is_windows():
        powershell = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
        return {name: bool(powershell) for name in
                ("cpu", "memory", "storage", "gpu", "memory_topology")}
    return {name: shutil.which(args[0]) is not None for name, args in COMMANDS.items()}

def run_powershell_json(script, timeout=10):
    """Run a fixed, application-authored PowerShell CIM query and parse its JSON."""
    if not is_windows():
        return {"ok": False, "data": None, "error": "Windows PowerShell inspection is only available on Windows."}
    executable = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
    if not executable:
        return {"ok": False, "data": None, "error": "PowerShell was not found."}
    safe_env = {"PATH": os.environ.get("PATH", ""), "SystemRoot": os.environ.get("SystemRoot", ""),
                "WINDIR": os.environ.get("WINDIR", ""), "LANG": "C"}
    try:
        completed = subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=timeout, check=False,
            shell=False, env=safe_env
        )
        if completed.returncode != 0:
            return {"ok": False, "data": None,
                    "error": (completed.stderr or "PowerShell inspection failed.").strip()[:500]}
        import json
        return {"ok": True, "data": json.loads(completed.stdout), "error": None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "data": None, "error": f"PowerShell inspection timed out after {timeout} seconds."}
    except (OSError, ValueError) as exc:
        return {"ok": False, "data": None, "error": str(exc)[:500]}

def run_tool(tool_name):
    if tool_name not in COMMANDS:
        return {"ok": False, "stdout": "", "error": "Rejected: tool is not allow-listed."}
    args = COMMANDS[tool_name]
    executable = shutil.which(args[0])
    if not executable:
        return {"ok": False, "stdout": "", "error": f"Required utility '{args[0]}' is not installed."}
    safe_env = {"PATH": os.environ.get("PATH", ""), "LANG": "C", "LC_ALL": "C"}
    try:
        completed = subprocess.run(
            [executable, *args[1:]], capture_output=True, text=True,
            timeout=8, check=False, shell=False, env=safe_env
        )
        if completed.returncode != 0:
            error = (completed.stderr or "Command failed.").strip()[:500]
            if tool_name == "memory_topology":
                error = "dmidecode could not read firmware data. " + error
            return {"ok": False, "stdout": "", "error": error}
        return {"ok": True, "stdout": completed.stdout[:30000], "error": None}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "error": "Command timed out after 8 seconds."}
    except OSError as exc:
        return {"ok": False, "stdout": "", "error": str(exc)[:500]}
