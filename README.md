# Linux Hardware Q&A Assistant

A local Streamlit chatbot that answers hardware questions using live, read-only Linux inspection tools. Ollama is optional and provides broader natural-language understanding and tool selection. A deterministic fallback works without Ollama.

## Features
- CPU: `lscpu`, with psutil/platform fallback
- Memory: `free`, `/proc/meminfo`, psutil
- Storage: `lsblk` JSON output
- GPU: `lspci`
- RAM topology: `dmidecode` where installed and permitted
- Live tool execution: the model selects predefined tools; backend validates and executes them
- Follow-up context using recent conversation
- Structured JSON snapshots
- Allow-list, fixed command arguments, `shell=False`, timeouts, output limits
- No automatic privilege escalation and no arbitrary command execution

## Install

Linux / Ubuntu / WSL:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:
```powershell
python -m venv venv
venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run:
```bash
python -m streamlit run app.py
```

This assignment targets Linux. Direct Windows execution will not provide Linux-specific information. WSL may expose virtualized or incomplete hardware details.

## Enable local NLP model
Install Ollama from https://ollama.com/, then:
```bash
ollama pull qwen2.5:3b
```
Set `.env`:
```env
OLLAMA_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```
Restart Streamlit. Ollama must be running locally. Without it, built-in intent matching handles common hardware questions but is not equivalent to a general NLP model.

## RAM upgrade details
`dmidecode --type memory` can report firmware memory devices, slots and maximum capacity. It may require elevated permissions. The application intentionally does not call `sudo` automatically or run as root. If permission is denied, it reports the limitation. Firmware data is not a guarantee of RAM compatibility; verify the exact laptop/motherboard model and manufacturer specifications.

## Safety design
- The LLM can select only named functions in the tool schema.
- Backend maps those names to a fixed allow-list.
- User text and model arguments are never used to construct shell commands.
- `subprocess.run(..., shell=False)` uses fixed arguments, timeouts and bounded output.
- No write, install, network, or destructive system commands are exposed as tools.
- Missing tools and permission failures are returned as structured errors.

## Example questions
- How much RAM do I have?
- Can I install another memory stick?
- Is my SSD NVMe?
- What processor and GPU do I have?
- How many memory slots are in use?
- What is the maximum RAM capacity?
- And what about the GPU?

## Tests
```bash
python -m pytest -q
```


## Windows and Linux support

The assistant selects a platform-specific, fixed inspection backend:
- Windows: read-only PowerShell CIM queries for CPU, installed RAM modules, firmware-reported memory-device capacity, physical disks, and display adapters.
- Linux: fixed allow-listed commands (`lscpu`, `free`, `lsblk`, `lspci`, and `dmidecode`).

Run the Streamlit app as your normal user, not as Administrator/root. Windows CIM and Linux inspection results can be incomplete depending on firmware, permissions, drivers, or virtualization. In WSL, Linux commands describe the WSL virtual environment; run the app in native Windows PowerShell to inspect the Windows host hardware. Firmware-reported memory-device counts do not prove that RAM is removable or upgradeable. Confirm the exact laptop model with its manufacturer before buying components.

The inspection subprocesses use fixed application-authored arguments, `shell=False`, and timeouts. User questions and model output are never passed as shell commands. The app writes its normalized hardware snapshot to `data/hardware_info.json` inside the project folder.
