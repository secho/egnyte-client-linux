"""Main GUI application entry point"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf
import sys
import logging
from pathlib import Path

from ..config import Config
from ..auth import OAuthHandler
from ..api_client import EgnyteAPIClient
from ..sync_engine import SyncEngine
from ..file_watcher import FileWatcher
from .main_window import MainWindow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for GUI application"""
    # Initialize configuration
    config = Config()
    
    # Check if configured
    if not config.get_domain() or not config.get_client_id():
        print("Please configure the application first:")
        print("1. Set domain: egnyte-cli config set domain yourdomain")
        print("2. Set client ID: egnyte-cli config set client_id YOUR_CLIENT_ID")
        sys.exit(1)
    
    # Initialize components
    auth = OAuthHandler(config)
    
    # Check authentication
    if not auth.is_authenticated():
        print("Not authenticated. Starting authentication flow...")
        try:
            auth.authenticate()
        except Exception as e:
            print(f"Authentication failed: {e}")
            sys.exit(1)
    
    api_client = EgnyteAPIClient(config, auth)
    sync_engine = SyncEngine(api_client, config)
    file_watcher = FileWatcher(sync_engine, config)
    
    # Create and run application
    app = Gtk.Application(application_id="com.egnyte.desktop")
    
    def on_activate(app):
        """Handle application activation"""
        window = MainWindow(app, config, api_client, sync_engine, file_watcher)
        # Start file watcher in background
        file_watcher.start()
    
    app.connect('activate', on_activate)
    
    # Activate the application (this triggers the 'activate' signal)
    app.activate()
    
    # Run the application main loop
    exit_status = app.run(sys.argv if len(sys.argv) > 1 else [])
    
    # Cleanup
    file_watcher.stop()
    
    sys.exit(exit_status)


if __name__ == '__main__':
    main()

