# Examples

This folder contains example configuration files for running egnyte-cli as a service.

## systemd Service

The `egnyte-sync.service` file is an example systemd unit for running egnyte-cli as a background sync service.

### Installation

1. Copy and customize the service file:

```bash
cp examples/egnyte-sync.service ~/.config/systemd/user/egnyte-sync.service
```

2. Edit the file to match your environment (paths, user, etc.)

3. Enable and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable egnyte-sync.service
systemctl --user start egnyte-sync.service
```

4. Check status:

```bash
systemctl --user status egnyte-sync.service
```
