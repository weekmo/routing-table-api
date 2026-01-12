# Podman Systemd Integration

This directory contains systemd unit files for managing the routing table API as a system service using Podman.

## Files

- `routing-table-api.service` - Main API service
- `routing-table-api-test.service` - Test runner (one-shot)

## Installation

1. **Copy unit files to systemd directory:**
   ```bash
   # For user services (rootless)
   mkdir -p ~/.config/systemd/user/
   cp podman-systemd/*.service ~/.config/systemd/user/
   
   # For system services (requires root)
   sudo cp podman-systemd/*.service /etc/systemd/system/
   ```

2. **Reload systemd:**
   ```bash
   # User services
   systemctl --user daemon-reload
   
   # System services
   sudo systemctl daemon-reload
   ```

3. **Enable and start the API service:**
   ```bash
   # User services
   systemctl --user enable routing-table-api.service
   systemctl --user start routing-table-api.service
   
   # System services
   sudo systemctl enable routing-table-api.service
   sudo systemctl start routing-table-api.service
   ```

4. **Run tests:**
   ```bash
   # User services
   systemctl --user start routing-table-api-test.service
   
   # System services
   sudo systemctl start routing-table-api-test.service
   ```

## Usage

**Check service status:**
```bash
systemctl --user status routing-table-api.service
```

**View logs:**
```bash
journalctl --user -u routing-table-api.service -f
```

**Stop service:**
```bash
systemctl --user stop routing-table-api.service
```

**Restart service:**
```bash
systemctl --user restart routing-table-api.service
```

## Advantages of Systemd Integration

- **Auto-restart on failure:** Service automatically restarts if it crashes
- **Boot on startup:** Service starts automatically on system boot
- **Resource limits:** CPU and memory limits enforced by systemd
- **Logging:** Centralized logging via journald
- **Dependencies:** Proper service ordering and dependencies
- **Rootless:** Can run as non-root user with user services
