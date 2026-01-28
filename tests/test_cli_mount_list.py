# 2026 Jan Sechovec from Revolgy and Remangu
"""CLI mount list tests."""

import io

from click.testing import CliRunner

import egnyte_desktop.cli.main as cli_main


def test_mount_list_reads_proc_mounts(monkeypatch):
    mounts = (
        "EgnyteFuse /home/user/egnyte fuse rw,relatime,user_id=1000,group_id=1000 0 0\n"
        "tmpfs /run tmpfs rw,nosuid,nodev 0 0\n"
    )

    def fake_open(path, *args, **kwargs):
        if path == "/proc/mounts":
            return io.StringIO(mounts)
        raise FileNotFoundError(path)

    monkeypatch.setattr(cli_main, "open", fake_open)

    runner = CliRunner()
    result = runner.invoke(cli_main.cli, ["mount", "list"])
    assert result.exit_code == 0
    assert "/home/user/egnyte" in result.output
