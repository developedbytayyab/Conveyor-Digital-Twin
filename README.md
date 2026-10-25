# Conveyor Digital Twin — Remote Windows + Local Ollama LLM

A runnable **simulation prototype** featuring an illustrative 3D conveyor, simulated sensors, Isolation Forest anomaly detection, heuristic maintenance priority, bounded speed recommendations, CSV/PDF reports, and a chat-style local LLM copilot using Ollama.

> **Important:** This release uses simulated sensor data. It is not connected to a real PLC, conveyor, or industrial sensors. Do not use its recommendations as safety controls. The dashboard must be protected before internet exposure.

## Requirements

- Windows 10/11 PC with a supported 64-bit Python installation (Python 3.11 or 3.12 recommended).
- Internet access on first install, to download Python packages and the Ollama model.
- RAM/CPU/GPU sufficient for your selected model. `llama3.2:3b` is a modest starter model; performance depends on the PC.
- Cloudflare account and domain for the recommended secure remote-access method (or another authenticated VPN/reverse proxy).

## A. Install the project on the remote Windows PC

1. Extract this ZIP to a stable folder, e.g. `C:\ConveyorDigitalTwin`. Avoid running it from inside the ZIP.
2. Install Python 3.11 or 3.12 from https://www.python.org/downloads/windows/ . If using the installer, select **Add Python to PATH**.
3. Double-click `setup_windows.bat`. It creates `.venv` and installs the Python dependencies.
4. Install Ollama for Windows from https://ollama.com/download/windows and launch it. Ollama normally runs its local API on `http://127.0.0.1:11434`.
5. Open **Command Prompt** and run:
   ```bat
   ollama pull llama3.2:3b
   ollama list
   ```
   Keep Ollama running. Do not expose port 11434 directly to the internet.
6. In the project folder, run `run_tests.bat`. Expected result: all tests pass.
7. Start the dashboard by double-clicking `start_dashboard.bat`. Open `http://127.0.0.1:8501` on the remote PC.
8. Open **Local LLM Copilot** tab and use **Test Ollama connection**. Ask a question to check inference.

### Password protection

Set a long, unique password in the same Command Prompt **before** starting the app:

```bat
cd /d C:\ConveyorDigitalTwin
set TWIN_APP_PASSWORD=replace-this-with-a-long-unique-secret
set OLLAMA_MODEL=llama3.2:3b
.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Keep the password private. The app-level password is a basic extra layer, not a substitute for a properly configured access gateway. `set` applies only to that Command Prompt window. To persist a secret, use Windows environment variable settings carefully, or a protected service manager; do not commit secrets to source control.

## B. Secure access from anywhere (recommended: Cloudflare Tunnel + Access)

This method avoids opening inbound ports on your router. Keep Streamlit bound to `127.0.0.1` and keep Ollama bound to its local address.

1. First make sure the dashboard works locally at `http://127.0.0.1:8501`.
2. In Cloudflare, add/manage a domain and follow Cloudflare's current Zero Trust setup instructions: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/ .
3. Install `cloudflared` on the remote Windows PC using Cloudflare's official instructions: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/ .
4. In the Cloudflare Zero Trust dashboard, create a **Tunnel**, choose the Windows connector, and follow the commands shown by Cloudflare to authenticate and install/run the connector. These commands and token are account-specific; do not copy a token from anyone else.
5. Add a **Public Hostname** to the tunnel, e.g. `conveyor.your-domain.example`, with service type HTTP and origin `http://127.0.0.1:8501`.
6. In Zero Trust, create a **Cloudflare Access application** for that hostname and an allow policy limited to your own email address or approved identity group. Test it in a private/incognito browser before relying on it.
7. Only after Access is enforcing login should you use the public hostname from another network/device.
8. Keep Windows Firewall/router inbound ports closed. Do **not** create port-forwarding rules for 8501 or 11434. Do not create a public tunnel hostname for Ollama's port 11434.
9. Configure the PC to stay powered on and connected to the internet. Configure `cloudflared` as a Windows service using Cloudflare's documented procedure if you need it to survive logouts/reboots.

Cloudflare product UI and commands can change; use the current official documentation linked above. Never share a tunnel token or password in chat.

### Other remote-access options

A private VPN such as Tailscale or WireGuard is another reasonable choice. Prefer a private VPN if only you need access and you do not want a public hostname. Do not expose Streamlit directly to the public internet without authentication and TLS.

## C. Start/stop and troubleshooting

- **Start:** launch Ollama, then run `start_dashboard.bat`. Start the Cloudflare Tunnel service/connector if using it.
- **Stop:** press `Ctrl+C` in the Streamlit terminal. Ollama can remain running.
- **Ollama connection fails:** verify Ollama is running; in Command Prompt run `ollama list` and `curl http://127.0.0.1:11434/api/tags`.
- **Model not found:** run `ollama pull llama3.2:3b`. If using another model, set `OLLAMA_MODEL` to its exact `ollama list` name.
- **Model is slow / PC runs out of memory:** try a smaller quantized model supported by Ollama; exact choices depend on current Ollama catalog and PC resources.
- **Dashboard inaccessible remotely:** confirm the local dashboard is working, Cloudflare Tunnel is connected, Access policy permits your login, DNS hostname is correct, and Windows has outbound internet. Do not solve this by opening public inbound ports.
- **Port 8501 is busy:** change `--server.port 8501` in the launch command and set the Cloudflare origin to the same port.
- **Dependency install error:** use Python 3.11/3.12, update pip, then rerun `setup_windows.bat`.

## Project files

- `app.py` — Streamlit dashboard, illustrative 3D twin, sensor charts, reports and LLM chat tab
- `simulator.py` — synthetic sensor data
- `ml_detector.py` — Isolation Forest and threshold-based anomaly detection
- `optimizer.py` — bounded speed recommendations
- `reports.py` — CSV/PDF export
- `tests/` — core tests
- `setup_windows.bat` — create environment and install dependencies
- `start_dashboard.bat` — launch dashboard bound to localhost
- `check_ollama.bat` — check the local Ollama API

## Scope and limitations

- Simulated readings only; no real-time telemetry or PLC integration.
- 3D geometry is illustrative, not calibrated CAD.
- Anomaly model is a prototype; validate with labeled real sensor data before operational use.
- Maintenance advice is heuristic; remaining useful life is not calculated.
- Speed recommendations are advisory only and do not control hardware.
- Local LLM responses can be wrong; verify against manuals, procedures, and qualified personnel.
