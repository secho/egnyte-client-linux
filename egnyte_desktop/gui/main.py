"""Main GUI application entry point"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GdkPixbuf
import sys
import logging
from pathlib import Path
import threading

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
    file_watcher_holder = {"instance": None}
    
    # Check if configured
    if not config.get_domain() or not config.get_client_id():
        print("Please configure the application first:")
        print("1. Set domain: egnyte-cli config set domain yourdomain")
        print("2. Set client ID: egnyte-cli config set client_id YOUR_CLIENT_ID")
        sys.exit(1)
    
    # Create and run application
    app = Gtk.Application(application_id="com.egnyte.desktop")
    
    def on_activate(app):
        """Handle application activation"""
        auth = OAuthHandler(config)
        
        def start_main_window():
            api_client = EgnyteAPIClient(config, auth)
            sync_engine = SyncEngine(api_client, config)
            file_watcher = FileWatcher(sync_engine, config)
            window = MainWindow(app, config, api_client, sync_engine, file_watcher)
            file_watcher.start()
            file_watcher_holder["instance"] = file_watcher
        
        if auth.is_authenticated():
            start_main_window()
            return
        
        dialog = Gtk.Dialog(title="Authenticating...", transient_for=None, modal=True)
        dialog.set_default_size(420, 140)
        dialog.set_resizable(False)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        
        label = Gtk.Label(
            label="Waiting for browser authorization.\n"
                  "If prompted, approve the localhost certificate warning."
        )
        label.set_justify(Gtk.Justification.LEFT)
        content_area.pack_start(label, False, False, 0)
        
        spinner = Gtk.Spinner()
        spinner.start()
        content_area.pack_start(spinner, False, False, 0)
        
        dialog.show_all()
        
        def do_auth():
            try:
                auth.authenticate(allow_manual_fallback=False)
                GLib.idle_add(dialog.destroy)
                GLib.idle_add(start_main_window)
            except Exception as e:
                def show_error():
                    dialog.destroy()
                    error = Gtk.MessageDialog(
                        parent=None,
                        flags=Gtk.DialogFlags.MODAL,
                        type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.CLOSE,
                        message_format=f"Authentication failed: {e}"
                    )
                    error.run()
                    error.destroy()
                    app.quit()
                GLib.idle_add(show_error)
        
        threading.Thread(target=do_auth, daemon=True).start()
    
    app.connect('activate', on_activate)
    
    # Activate the application (this triggers the 'activate' signal)
    app.activate()
    
    # Run the application main loop
    exit_status = app.run(sys.argv if len(sys.argv) > 1 else [])
    
    # Cleanup
    if file_watcher_holder["instance"]:
        file_watcher_holder["instance"].stop()
    
    sys.exit(exit_status)


if __name__ == '__main__':
    main()

