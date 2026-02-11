# 2026 Jan Sechovec from Revolgy and Remangu
"""CLI main entry point"""

import click
import sys
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from builtins import open as open

from ..config import Config
from ..auth import OAuthHandler
from ..api_client import EgnyteAPIClient
from ..sync_engine import SyncEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def _title(text: str):
    """Print a bold section title."""
    click.secho(text, bold=True)

def _info(text: str):
    """Print an informational message."""
    click.secho(text, fg="cyan")

def _success(text: str):
    """Print a success message."""
    click.secho(text, fg="green")

def _warn(text: str):
    """Print a warning message."""
    click.secho(text, fg="yellow")

def _error(text: str):
    """Print an error message."""
    click.secho(text, fg="red", bold=True, err=True)

def _hint(text: str):
    """Print a hint in a subdued style."""
    click.secho(text, fg="bright_black")

def _kv(label: str, value: str):
    """Print a aligned key/value line."""
    click.echo(f"{label:<16} {value}")

def _bullet(text: str):
    """Print a single bullet line."""
    click.echo(f"- {text}")

class MountGroup(click.Group):
    """Mount group that treats unknown args as mount points."""
    def resolve_command(self, ctx, args):
        """Map unknown commands to 'start' to keep old UX."""
        # Treat unknown subcommand as mount point for "start"
        if args and args[0] not in self.commands:
            args = ['start'] + args
        return super().resolve_command(ctx, args)


@click.group()
@click.pass_context
def cli(ctx):
    """Egnyte Desktop Client - Command Line Interface"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = Config()


@cli.group()
def config():
    """Configuration commands"""
    pass


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key, value):
    """Set configuration value"""
    config = ctx.obj['config']
    
    if key == 'domain':
        config.set_domain(value)
        _success("Domain updated.")
        _kv("Domain:", value)
    elif key == 'client_id':
        config.set_client_id(value)
        _success("Client ID updated.")
    elif key == 'client_secret':
        config.set_client_secret(value)
        _success("Client secret updated.")
    elif key == 'redirect_uri':
        config.set_redirect_uri(value)
        _success("Redirect URI updated.")
        _kv("Redirect URI:", value)
    else:
        config.set(key, value)
        _success(f"{key} updated.")
        _kv(f"{key}:", value)


@config.command('get')
@click.argument('key')
@click.pass_context
def config_get(ctx, key):
    """Get configuration value"""
    config = ctx.obj['config']
    value = config.get(key)
    if value:
        click.echo(value)
    else:
        _error(f"Configuration key '{key}' not found.")
        sys.exit(1)


@config.command('list')
@click.pass_context
def config_list(ctx):
    """List all configuration"""
    config = ctx.obj['config']
    domain = config.get_domain()
    client_id = config.get_client_id()
    client_secret = config.get_client_secret()
    
    _title("Configuration")
    _kv("Domain:", domain or "Not set")
    _kv("Client ID:", ("*" * 20) if client_id else "Not set")
    _kv("Client Secret:", ("*" * 20) if client_secret else "Not set")
    _kv("Redirect URI:", config.get_redirect_uri())
    _kv("Conflict policy:", config.get_sync_conflict_policy())
    _kv("Delete local on remote missing:", str(config.get_delete_local_on_remote_missing()))
    _kv("Delete remote on local missing:", str(config.get_delete_remote_on_local_missing()))
    
    sync_paths = config.get_sync_paths()
    if sync_paths:
        click.echo()
        _title("Sync Paths")
        for local, remote in sync_paths.items():
            _bullet(f"{local} <-> {remote}")


@cli.group()
def auth():
    """Authentication commands"""
    pass


@auth.command('login')
@click.option('--code', help='Authorization code (if manually entering)')
@click.option('--password-flow', is_flag=True, help='Use Resource Owner Password flow (internal apps)')
@click.option('--username', '-u', help='Egnyte username (for password flow)')
@click.pass_context
def auth_login(ctx, code, password_flow, username):
    """Authenticate with Egnyte
    
    If Egnyte requires HTTPS redirect URI, you'll need to manually enter the code:
    1. Open the authorization URL shown
    2. Complete authorization in browser
    3. Copy the 'code' parameter from the error page URL
    4. Run: egnyte-cli auth login --code YOUR_CODE

    Password flow (internal apps only):
    - Use: egnyte-cli auth login --password-flow --username USERNAME
    """
    config = ctx.obj['config']

    if password_flow and code:
        _error("Cannot combine --code with --password-flow.")
        sys.exit(1)
    
    if not config.get_domain() or not config.get_client_id():
        _error("Domain and Client ID must be configured first.")
        _hint("egnyte-cli config set domain YOUR_DOMAIN")
        _hint("egnyte-cli config set client_id YOUR_CLIENT_ID")
        sys.exit(1)
    
    if not config.get_client_secret():
        _error("Client secret must be configured.")
        _hint("egnyte-cli config set client_secret YOUR_CLIENT_SECRET")
        _hint("Client secret is available in the Egnyte Developer Portal.")
        sys.exit(1)
    
    auth = OAuthHandler(config)
    
    try:
        if password_flow:
            _info("Starting password authentication...")
            if not username:
                username = click.prompt("Username")
            password = click.prompt("Password", hide_input=True)
            tokens = auth.authenticate_password(username=username, password=password)
        else:
            _info("Starting authentication...")
            tokens = auth.authenticate(manual_code=code)
        _success("Authentication successful.")
    except KeyboardInterrupt:
        _warn("Authentication cancelled.")
        sys.exit(1)
    except Exception as e:
        _error(f"Authentication failed: {e}")
        sys.exit(1)


@auth.command('status')
@click.pass_context
def auth_status(ctx):
    """Check authentication status"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if auth.is_authenticated():
        _success("Authenticated.")
        tokens = auth.load_tokens() or {}
        api_client = EgnyteAPIClient(config, auth)
        
        user_display = "Unknown"
        try:
            user_info = api_client.get_user_info()
            user_display = (
                user_info.get("username")
                or user_info.get("userName")
                or user_info.get("email")
                or user_info.get("name")
                or "Unknown"
            )
        except Exception:
            pass
        
        issued_at = tokens.get("issued_at")
        expires_in = tokens.get("expires_in")
        
        auth_time = "Unknown"
        expires_at = "Unknown"
        if issued_at:
            auth_time = datetime.fromtimestamp(int(issued_at), tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            if expires_in:
                expires_at_ts = int(issued_at) + int(expires_in)
                expires_at = datetime.fromtimestamp(expires_at_ts, tz=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        _kv("User:", user_display)
        _kv("Authenticated:", auth_time)
        _kv("Token expires:", expires_at)
        if tokens.get("access_token") and not tokens.get("refresh_token"):
            _hint("No refresh token stored; re-authenticate when token expires.")
    else:
        _warn("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)


@auth.command('revoke')
@click.pass_context
def auth_revoke(ctx):
    """Revoke local authentication tokens"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    auth.revoke_tokens()
    _success("Local authentication tokens removed.")


@cli.group()
def sync():
    """Synchronization commands"""
    pass


@cli.group()
def service():
    """Background sync service"""
    pass


@service.command('run')
@click.option('--remote-interval', default=15, show_default=True, help='Remote polling interval (seconds)')
def service_run(remote_interval):
    """Run sync service in foreground"""
    config = Config()
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    try:
        from ..sync_service import EgnyteSyncService
        _info("Starting Egnyte sync service...")
        service = EgnyteSyncService(config, remote_interval=remote_interval)
        service.start()
    except KeyboardInterrupt:
        _warn("Service stopped.")
    except Exception as e:
        _error(f"Service error: {e}")
        sys.exit(1)


@sync.command('add')
@click.argument('local_path')
@click.argument('remote_path')
@click.option('--conflict-policy', type=click.Choice(['newest', 'local', 'remote']), help='Conflict policy for this path')
@click.option('--delete-local-on-remote-missing', is_flag=True, help='Delete local when remote missing')
@click.option('--delete-remote-on-local-missing', is_flag=True, help='Delete remote when local missing')
@click.pass_context
def sync_add(ctx, local_path, remote_path, conflict_policy, delete_local_on_remote_missing, delete_remote_on_local_missing):
    """Add a sync path"""
    config = ctx.obj['config']
    
    local = Path(local_path)
    if not local.exists():
        _error(f"Local path does not exist: {local_path}")
        sys.exit(1)
    
    policy = {}
    if conflict_policy:
        policy['conflict_policy'] = conflict_policy
    if delete_local_on_remote_missing:
        policy['delete_local_on_remote_missing'] = True
    if delete_remote_on_local_missing:
        policy['delete_remote_on_local_missing'] = True
    
    if policy:
        config.set_sync_path_policy(local_path, policy)
        config.set('sync_paths', {**config.get('sync_paths', {}), local_path: {'remote': remote_path, 'policy': policy}})
    else:
        config.add_sync_path(local_path, remote_path)
    _success("Sync path added.")
    _bullet(f"{local_path} <-> {remote_path}")


@sync.command('remove')
@click.argument('local_path')
@click.pass_context
def sync_remove(ctx, local_path):
    """Remove a sync path"""
    config = ctx.obj['config']
    config.remove_sync_path(local_path)
    _success("Sync path removed.")
    _bullet(local_path)


@sync.command('set-policy')
@click.argument('local_path')
@click.option('--conflict-policy', type=click.Choice(['newest', 'local', 'remote']), help='Conflict policy for this path')
@click.option('--delete-local-on-remote-missing/--keep-local-on-remote-missing', default=None, help='Delete local when remote missing')
@click.option('--delete-remote-on-local-missing/--keep-remote-on-local-missing', default=None, help='Delete remote when local missing')
@click.pass_context
def sync_set_policy(ctx, local_path, conflict_policy, delete_local_on_remote_missing, delete_remote_on_local_missing):
    """Update policy for a sync path"""
    config = ctx.obj['config']
    entries = config.get_sync_entries()
    if local_path not in entries:
        _error(f"Sync path not found: {local_path}")
        sys.exit(1)
    
    policy = entries[local_path].get('policy', {}) or {}
    if conflict_policy:
        policy['conflict_policy'] = conflict_policy
    if delete_local_on_remote_missing is not None:
        policy['delete_local_on_remote_missing'] = bool(delete_local_on_remote_missing)
    if delete_remote_on_local_missing is not None:
        policy['delete_remote_on_local_missing'] = bool(delete_remote_on_local_missing)
    
    config.set_sync_path_policy(local_path, policy)
    _success("Sync policy updated.")
    _bullet(f"{local_path} -> {entries[local_path].get('remote', '')}")


@sync.command('list')
@click.pass_context
def sync_list(ctx):
    """List all sync paths"""
    config = ctx.obj['config']
    sync_entries = config.get_sync_entries()
    
    if not sync_entries:
        _warn("No sync paths configured.")
        return
    
    _title("Sync Paths")
    for local, entry in sync_entries.items():
        remote = entry.get('remote', '')
        policy = entry.get('policy', {}) or {}
        details = []
        if policy.get('conflict_policy'):
            details.append(f"conflict={policy.get('conflict_policy')}")
        if policy.get('delete_local_on_remote_missing'):
            details.append("delete_local_on_remote_missing")
        if policy.get('delete_remote_on_local_missing'):
            details.append("delete_remote_on_local_missing")
        suffix = f" ({', '.join(details)})" if details else ""
        _bullet(f"{local} <-> {remote}{suffix}")


@sync.command('now')
@click.option('--path', help='Sync specific path (local path)')
@click.pass_context
def sync_now(ctx, path):
    """Sync files now"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    sync_engine = SyncEngine(api_client, config)
    
    try:
        if path:
            # Sync specific path
            sync_paths = config.get_sync_paths()
            if path not in sync_paths:
                _error(f"Path not in sync list: {path}")
                sys.exit(1)
            
            remote_path = sync_paths[path]
            _info(f"Syncing {path}...")
            results = sync_engine.sync_folder(Path(path), remote_path)
        else:
            # Sync all
            _info("Syncing all paths...")
            results = sync_engine.sync_all()
        
        success = sum(1 for r in results if r['success'])
        _success(f"Sync complete: {success}/{len(results)} files synced.")
        
        if success < len(results):
            for r in results:
                if not r['success']:
                    _error(f"Failed: {r['local_path']} - {r.get('error', 'Unknown error')}")
    
    except Exception as e:
        _error(f"Sync error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('remote_path')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def download(ctx, remote_path, output):
    """Download a file"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        if output:
            local_path = Path(output)
        else:
            # Use filename from remote path
            local_path = Path(remote_path.split('/')[-1])
        
        _info(f"Downloading {remote_path}...")
        api_client.download_file(remote_path, local_path)
        _success(f"Downloaded to: {local_path}")
    
    except Exception as e:
        _error(f"Download error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('local_path')
@click.argument('remote_path')
@click.option('--overwrite/--no-overwrite', default=True, help='Overwrite existing file')
@click.option('--create-folders/--no-create-folders', default=True, help='Create parent folders if needed')
@click.pass_context
def upload(ctx, local_path, remote_path, overwrite, create_folders):
    """Upload a file
    
    Note: Cannot upload directly to /Shared/ - use /Shared/Documents/ or create a subfolder.
    
    Examples:
        egnyte-cli upload file.txt /Shared/Documents/
        egnyte-cli upload file.txt /Shared/Documents/file.txt
        egnyte-cli upload ~/Pictures/image.png /Private/jas_admin/
    """
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    local_file = Path(local_path)
    
    if not local_file.exists():
        _error(f"File does not exist: {local_path}")
        sys.exit(1)
    
    if local_file.is_dir():
        _error(f"{local_path} is a directory. Use sync command for directories.")
        sys.exit(1)
    
    try:
        # Show what will be uploaded
        if remote_path.endswith('/'):
            final_remote_path = remote_path.rstrip('/') + '/' + local_file.name
        else:
            final_remote_path = remote_path
        
        # Check if trying to upload directly to /Shared/
        if final_remote_path == f'/Shared/{local_file.name}':
            _warn("Cannot upload directly to /Shared/. Using /Shared/Documents/ instead.")
            final_remote_path = f'/Shared/Documents/{local_file.name}'
        
        _info(f"Uploading {local_path} to {final_remote_path}...")
        _hint("Tip: pass --no-create-folders for faster uploads when folder exists.")
        
        result = api_client.upload_file(local_file, remote_path, overwrite=overwrite, create_folders=create_folders)
        _success(f"Uploaded to: {final_remote_path}")
    
    except Exception as e:
        _error(f"Upload error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('remote_path', default='/')
@click.pass_context
def ls(ctx, remote_path):
    """List files and folders"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        items = api_client.list_folder(remote_path)
        
        if not items:
            _warn("Empty folder.")
            return
        
        # Sort: folders first, then files
        folders = [i for i in items if i.get('is_folder')]
        files = [i for i in items if not i.get('is_folder')]
        
        _title(f"Listing {remote_path}")
        for item in sorted(folders, key=lambda x: x.get('name', '')):
            name = item.get('name', '')
            size = item.get('size', 0)
            _bullet(f"{name}/  [{size} bytes]")
        
        for item in sorted(files, key=lambda x: x.get('name', '')):
            name = item.get('name', '')
            size = item.get('size', 0)
            modified = item.get('modified_time', '')[:19] if item.get('modified_time') else ''
            _bullet(f"{name}  [{size} bytes]  {modified}")
    
    except Exception as e:
        _error(f"Error: {e}")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show application status"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    _title("Egnyte CLI Status")
    
    # Authentication
    if auth.is_authenticated():
        _kv("Authentication:", "Authenticated")
    else:
        _kv("Authentication:", "Not authenticated")
    
    # Configuration
    domain = config.get_domain()
    _kv("Domain:", domain or "Not set")
    
    # Sync paths
    sync_paths = config.get_sync_paths()
    _kv("Sync paths:", f"{len(sync_paths)} configured")
    for local, remote in sync_paths.items():
        _bullet(f"{local} <-> {remote}")


def _list_egnyte_mounts():
    """Read /proc/mounts and return Egnyte mount points."""
    mounts = []
    try:
        with open("/proc/mounts", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                source, mount_point, fstype, options = parts[0], parts[1], parts[2], parts[3]
                if (
                    fstype == "fuse.egnyte"
                    or "subtype=egnyte" in options
                    or "fsname=egnyte" in options
                    or (fstype.startswith("fuse") and source in {"egnyte", "EgnyteFuse"})
                ):
                    mounts.append(mount_point)
    except Exception:
        pass
    return mounts


@cli.group(cls=MountGroup)
def mount():
    """Mount Egnyte as a FUSE filesystem
    
    Requires: sudo apt-get install fuse libfuse-dev
    
    Example:
        egnyte-cli mount ~/egnyte
    """
    pass


def _mount_start(ctx, mount_point, foreground):
    """Perform the actual mount operation."""
    try:
        from ..fuse_mount import mount_egnyte
    except ImportError as e:
        _error(f"Cannot import fuse_mount module: {e}")
        # Try to import fuse directly to give better error message
        try:
            import fuse
            _info("fuse module is available.")
        except ImportError:
            _error("fuse-python not installed.")
            _hint("pip install fuse-python")
            _hint("sudo apt-get install fuse libfuse-dev")
        sys.exit(1)
    except Exception as e:
        _error(f"Error loading mount module: {e}")
        import traceback
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)
    
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        _error("Not authenticated.")
        _hint("egnyte-cli auth login")
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        _info(f"Mounting Egnyte to {mount_point}...")
        _hint("Press Ctrl+C to unmount")
        
        mount_egnyte(mount_point, config, api_client, foreground=foreground)
    except KeyboardInterrupt:
        _info("Unmounting...")
        subprocess.run(['fusermount', '-u', mount_point], check=False)
        _success("Unmounted.")
    except Exception as e:
        _error(f"Mount error: {e}")
        sys.exit(1)


@mount.command('list')
def mount_list():
    """List Egnyte mounts"""
    mounts = _list_egnyte_mounts()
    if not mounts:
        _warn("No Egnyte mounts found.")
        return
    _title("Egnyte Mounts")
    for m in mounts:
        _bullet(m)


@mount.command('umount')
@click.argument('mount_point', required=False)
@click.option('--all', 'unmount_all', is_flag=True, help='Unmount all Egnyte mounts')
def mount_umount(mount_point, unmount_all):
    """Unmount an Egnyte mount"""
    if unmount_all:
        mounts = _list_egnyte_mounts()
        if not mounts:
            _warn("No Egnyte mounts found.")
            return
        for m in mounts:
            subprocess.run(['fusermount', '-u', m], check=False)
            _success(f"Unmounted {m}")
        return
    
    if not mount_point:
        _error("Mount point is required.")
        _hint("egnyte-cli mount umount /path/to/mount")
        sys.exit(1)
    
    subprocess.run(['fusermount', '-u', mount_point], check=False)
    _success(f"Unmounted {mount_point}")


@mount.command('unmount')
@click.argument('mount_point', required=False)
@click.option('--all', 'unmount_all', is_flag=True, help='Unmount all Egnyte mounts')
def mount_unmount(mount_point, unmount_all):
    """Unmount an Egnyte mount (alias of umount)"""
    if unmount_all:
        mounts = _list_egnyte_mounts()
        if not mounts:
            _warn("No Egnyte mounts found.")
            return
        for m in mounts:
            subprocess.run(['fusermount', '-u', m], check=False)
            _success(f"Unmounted {m}")
        return
    
    if not mount_point:
        _error("Mount point is required.")
        _hint("egnyte-cli mount unmount /path/to/mount")
        sys.exit(1)
    
    subprocess.run(['fusermount', '-u', mount_point], check=False)
    _success(f"Unmounted {mount_point}")


@mount.command('start')
@click.argument('mount_point')
@click.option('--foreground/--background', default=False, help='Run in foreground (for debugging)')
@click.pass_context
def mount_start(ctx, mount_point, foreground):
    """Mount Egnyte (explicit subcommand)"""
    _mount_start(ctx, mount_point, foreground)


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == '__main__':
    main()

