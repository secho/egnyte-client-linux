"""CLI main entry point"""

import click
import sys
import logging
from pathlib import Path

from ..config import Config
from ..auth import OAuthHandler
from ..api_client import EgnyteAPIClient
from ..sync_engine import SyncEngine

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


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
        click.echo(f"Domain set to: {value}")
    elif key == 'client_id':
        config.set_client_id(value)
        click.echo(f"Client ID set")
    elif key == 'client_secret':
        config.set_client_secret(value)
        click.echo(f"Client secret set")
    elif key == 'redirect_uri':
        config.set_redirect_uri(value)
        click.echo(f"Redirect URI set to: {value}")
    else:
        config.set(key, value)
        click.echo(f"{key} set to: {value}")


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
        click.echo(f"Configuration key '{key}' not found", err=True)
        sys.exit(1)


@config.command('list')
@click.pass_context
def config_list(ctx):
    """List all configuration"""
    config = ctx.obj['config']
    domain = config.get_domain()
    client_id = config.get_client_id()
    client_secret = config.get_client_secret()
    
    click.echo("Configuration:")
    click.echo(f"  Domain: {domain or 'Not set'}")
    click.echo(f"  Client ID: {'*' * 20 if client_id else 'Not set'}")
    click.echo(f"  Client Secret: {'*' * 20 if client_secret else 'Not set'}")
    click.echo(f"  Redirect URI: {config.get_redirect_uri()}")
    
    sync_paths = config.get_sync_paths()
    if sync_paths:
        click.echo("\nSync Paths:")
        for local, remote in sync_paths.items():
            click.echo(f"  {local} <-> {remote}")


@cli.group()
def auth():
    """Authentication commands"""
    pass


@auth.command('login')
@click.option('--code', help='Authorization code (if manually entering)')
@click.pass_context
def auth_login(ctx, code):
    """Authenticate with Egnyte
    
    If Egnyte requires HTTPS redirect URI, you'll need to manually enter the code:
    1. Open the authorization URL shown
    2. Complete authorization in browser
    3. Copy the 'code' parameter from the error page URL
    4. Run: egnyte-cli auth login --code YOUR_CODE
    """
    config = ctx.obj['config']
    
    if not config.get_domain() or not config.get_client_id():
        click.echo("Error: Domain and Client ID must be configured first", err=True)
        click.echo("Use: egnyte-cli config set domain YOUR_DOMAIN", err=True)
        click.echo("Use: egnyte-cli config set client_id YOUR_CLIENT_ID", err=True)
        sys.exit(1)
    
    if not config.get_client_secret():
        click.echo("Error: Client secret must be configured", err=True)
        click.echo("Use: egnyte-cli config set client_secret YOUR_CLIENT_SECRET", err=True)
        click.echo("\nYou can find your client secret in the Egnyte Developer Portal", err=True)
        sys.exit(1)
    
    auth = OAuthHandler(config)
    
    try:
        click.echo("Starting authentication...")
        tokens = auth.authenticate(manual_code=code)
        click.echo("Authentication successful!")
    except KeyboardInterrupt:
        click.echo("\nAuthentication cancelled", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Authentication failed: {e}", err=True)
        sys.exit(1)


@auth.command('status')
@click.pass_context
def auth_status(ctx):
    """Check authentication status"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if auth.is_authenticated():
        click.echo("Authenticated")
    else:
        click.echo("Not authenticated. Run 'egnyte-cli auth login'")
        sys.exit(1)


@cli.group()
def sync():
    """Synchronization commands"""
    pass


@sync.command('add')
@click.argument('local_path')
@click.argument('remote_path')
@click.pass_context
def sync_add(ctx, local_path, remote_path):
    """Add a sync path"""
    config = ctx.obj['config']
    
    local = Path(local_path)
    if not local.exists():
        click.echo(f"Error: Local path does not exist: {local_path}", err=True)
        sys.exit(1)
    
    config.add_sync_path(local_path, remote_path)
    click.echo(f"Added sync path: {local_path} <-> {remote_path}")


@sync.command('remove')
@click.argument('local_path')
@click.pass_context
def sync_remove(ctx, local_path):
    """Remove a sync path"""
    config = ctx.obj['config']
    config.remove_sync_path(local_path)
    click.echo(f"Removed sync path: {local_path}")


@sync.command('list')
@click.pass_context
def sync_list(ctx):
    """List all sync paths"""
    config = ctx.obj['config']
    sync_paths = config.get_sync_paths()
    
    if not sync_paths:
        click.echo("No sync paths configured")
        return
    
    click.echo("Sync Paths:")
    for local, remote in sync_paths.items():
        click.echo(f"  {local} <-> {remote}")


@sync.command('now')
@click.option('--path', help='Sync specific path (local path)')
@click.pass_context
def sync_now(ctx, path):
    """Sync files now"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        click.echo("Error: Not authenticated. Run 'egnyte-cli auth login'", err=True)
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    sync_engine = SyncEngine(api_client, config)
    
    try:
        if path:
            # Sync specific path
            sync_paths = config.get_sync_paths()
            if path not in sync_paths:
                click.echo(f"Error: Path not in sync list: {path}", err=True)
                sys.exit(1)
            
            remote_path = sync_paths[path]
            click.echo(f"Syncing {path}...")
            results = sync_engine.sync_folder(Path(path), remote_path)
        else:
            # Sync all
            click.echo("Syncing all paths...")
            results = sync_engine.sync_all()
        
        success = sum(1 for r in results if r['success'])
        click.echo(f"Sync complete: {success}/{len(results)} files synced")
        
        if success < len(results):
            for r in results:
                if not r['success']:
                    click.echo(f"  Failed: {r['local_path']} - {r.get('error', 'Unknown error')}", err=True)
    
    except Exception as e:
        click.echo(f"Sync error: {e}", err=True)
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
        click.echo("Error: Not authenticated. Run 'egnyte-cli auth login'", err=True)
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        if output:
            local_path = Path(output)
        else:
            # Use filename from remote path
            local_path = Path(remote_path.split('/')[-1])
        
        click.echo(f"Downloading {remote_path}...")
        api_client.download_file(remote_path, local_path)
        click.echo(f"Downloaded to: {local_path}")
    
    except Exception as e:
        click.echo(f"Download error: {e}", err=True)
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
        click.echo("Error: Not authenticated. Run 'egnyte-cli auth login'", err=True)
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    local_file = Path(local_path)
    
    if not local_file.exists():
        click.echo(f"Error: File does not exist: {local_path}", err=True)
        sys.exit(1)
    
    if local_file.is_dir():
        click.echo(f"Error: {local_path} is a directory. Use sync command for directories.", err=True)
        sys.exit(1)
    
    try:
        # Show what will be uploaded
        if remote_path.endswith('/'):
            final_remote_path = remote_path.rstrip('/') + '/' + local_file.name
        else:
            final_remote_path = remote_path
        
        # Check if trying to upload directly to /Shared/
        if final_remote_path == f'/Shared/{local_file.name}':
            click.echo("Warning: Cannot upload directly to /Shared/. Using /Shared/Documents/ instead.")
            final_remote_path = f'/Shared/Documents/{local_file.name}'
        
        click.echo(f"Uploading {local_path} to {final_remote_path}...")
        
        result = api_client.upload_file(local_file, remote_path, overwrite=overwrite, create_folders=create_folders)
        click.echo(f"✓ Uploaded successfully to: {final_remote_path}")
    
    except Exception as e:
        click.echo(f"Upload error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('remote_path', default='/')
@click.pass_context
def ls(ctx, remote_path):
    """List files and folders"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        click.echo("Error: Not authenticated. Run 'egnyte-cli auth login'", err=True)
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        items = api_client.list_folder(remote_path)
        
        if not items:
            click.echo("Empty folder")
            return
        
        # Sort: folders first, then files
        folders = [i for i in items if i.get('is_folder')]
        files = [i for i in items if not i.get('is_folder')]
        
        for item in sorted(folders, key=lambda x: x.get('name', '')):
            name = item.get('name', '')
            size = item.get('size', 0)
            click.echo(f"  {name}/  [{size} bytes]")
        
        for item in sorted(files, key=lambda x: x.get('name', '')):
            name = item.get('name', '')
            size = item.get('size', 0)
            modified = item.get('modified_time', '')[:19] if item.get('modified_time') else ''
            click.echo(f"  {name}  [{size} bytes]  {modified}")
    
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show application status"""
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    click.echo("Egnyte Desktop Client Status")
    click.echo("=" * 40)
    
    # Authentication
    if auth.is_authenticated():
        click.echo("Authentication: ✓ Authenticated")
    else:
        click.echo("Authentication: ✗ Not authenticated")
    
    # Configuration
    domain = config.get_domain()
    click.echo(f"Domain: {domain or 'Not set'}")
    
    # Sync paths
    sync_paths = config.get_sync_paths()
    click.echo(f"Sync Paths: {len(sync_paths)} configured")
    for local, remote in sync_paths.items():
        click.echo(f"  {local} <-> {remote}")


@cli.command()
@click.argument('mount_point')
@click.option('--foreground/--background', default=False, help='Run in foreground (for debugging)')
@click.pass_context
def mount(ctx, mount_point, foreground):
    """Mount Egnyte as a FUSE filesystem
    
    Requires: sudo apt-get install fuse libfuse-dev
    
    Example:
        egnyte-cli mount ~/egnyte
    """
    try:
        from ..fuse_mount import mount_egnyte
    except ImportError as e:
        click.echo(f"Error: Cannot import fuse_mount module: {e}", err=True)
        # Try to import fuse directly to give better error message
        try:
            import fuse
            click.echo("fuse module is available", err=True)
        except ImportError as fuse_error:
            click.echo("fuse-python not installed", err=True)
            click.echo("Install with: pip install fuse-python", err=True)
            click.echo("Also install system package: sudo apt-get install fuse libfuse-dev", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error loading mount module: {e}", err=True)
        import traceback
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)
    
    config = ctx.obj['config']
    auth = OAuthHandler(config)
    
    if not auth.is_authenticated():
        click.echo("Error: Not authenticated. Run 'egnyte-cli auth login'", err=True)
        sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    
    try:
        click.echo(f"Mounting Egnyte to {mount_point}...")
        click.echo("Press Ctrl+C to unmount")
        
        mount_egnyte(mount_point, config, api_client, foreground=foreground)
    except KeyboardInterrupt:
        click.echo("\nUnmounting...")
        import subprocess
        subprocess.run(['fusermount', '-u', mount_point], check=False)
        click.echo("Unmounted")
    except Exception as e:
        click.echo(f"Mount error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point"""
    cli(obj={})


if __name__ == '__main__':
    main()

