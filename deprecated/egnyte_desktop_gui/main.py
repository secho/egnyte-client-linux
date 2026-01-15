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
    
    # Prefer dark theme by default
    settings = Gtk.Settings.get_default()
    if settings:
        settings.set_property("gtk-application-prefer-dark-theme", True)
    
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
            file_watcher_holder["instance"] = file_watcher
        
        if auth.is_authenticated():
            start_main_window()
            return
        
        def show_error_and_quit(message: str):
            error = Gtk.MessageDialog(
                parent=None,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                message_format=message,
            )
            error.run()
            error.destroy()
            app.quit()
        
        try:
            try:
                gi.require_version('WebKit2', '4.1')
                from gi.repository import WebKit2  # type: ignore
            except Exception:
                gi.require_version('WebKit2', '4.0')
                from gi.repository import WebKit2  # type: ignore
        except Exception as e:
            show_error_and_quit(
                "Embedded browser is not available.\n"
                "Install WebKit2GTK (package name varies by distro):\n"
                "  Ubuntu/Debian: gir1.2-webkit2-4.0 or gir1.2-webkit2-4.1\n"
                "  Fedora: webkit2gtk4.0 or webkit2gtk4.1\n\n"
                f"Details: {e}"
            )
            return
        
        dialog = Gtk.Dialog(title="Sign in to Egnyte", transient_for=None, modal=True)
        dialog.set_application(app)
        dialog.set_default_size(900, 700)
        dialog.set_resizable(True)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        
        label = Gtk.Label(label="Complete login below. If prompted, approve the localhost certificate warning.")
        label.set_justify(Gtk.Justification.LEFT)
        content_area.pack_start(label, False, False, 0)
        
        try:
            context = WebKit2.WebContext.new_ephemeral()
        except Exception:
            context = WebKit2.WebContext.get_default()
        
        try:
            context.set_tls_errors_policy(WebKit2.TLSErrorsPolicy.IGNORE)
        except Exception:
            pass
        
        webview = WebKit2.WebView.new_with_context(context)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(webview)
        content_area.pack_start(scrolled, True, True, 0)
        
        dialog.show_all()
        
        auth_url = auth.get_authorization_url()
        webview.load_uri(auth_url)
        
        def do_auth():
            try:
                redirect_uri = config.get_redirect_uri()
                auth_code = auth.start_callback_server(redirect_uri)
                if not auth_code:
                    raise Exception("Timed out waiting for the OAuth callback")
                auth.exchange_code_for_tokens(auth_code, redirect_uri_override=redirect_uri)
                GLib.idle_add(dialog.destroy)
                GLib.idle_add(start_main_window)
            except Exception as e:
                def show_error():
                    dialog.destroy()
                    show_error_and_quit(f"Authentication failed: {e}")
                GLib.idle_add(show_error)
        
        threading.Thread(target=do_auth, daemon=True).start()
    
    app.connect('activate', on_activate)
    
    # Run the application main loop
    exit_status = app.run(sys.argv if len(sys.argv) > 1 else [])
    
    # Cleanup
    if file_watcher_holder["instance"]:
        file_watcher_holder["instance"].stop()
    
    sys.exit(exit_status)


if __name__ == '__main__':
    main()

