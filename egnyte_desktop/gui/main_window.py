"""Main window for GTK3 GUI"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window"""
    
    def __init__(self, app: Gtk.Application, config, api_client, sync_engine, file_watcher):
        self.app = app
        self.config = config
        self.api_client = api_client
        self.sync_engine = sync_engine
        self.file_watcher = file_watcher
        
        # Build UI
        self.builder = Gtk.Builder()
        self._build_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Add window to application
        app.add_window(self.window)
        
        # Load initial data
        self._refresh_file_list()
        
        # Show window
        self.window.show_all()
        self.window.present()  # Bring window to front
    
    def _build_ui(self):
        """Build the UI"""
        # Create main window
        self.window = Gtk.Window(title="Egnyte Desktop")
        self.window.set_default_size(1000, 700)
        self.window.connect("destroy", Gtk.main_quit)
        
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.window.add(main_box)
        
        # Menu bar
        menubar = self._create_menu_bar()
        main_box.pack_start(menubar, False, False, 0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_box.pack_start(toolbar, False, False, 0)
        
        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.status_context_id = self.status_bar.get_context_id("main")
        main_box.pack_end(self.status_bar, False, False, 0)
        
        # Main content area (paned)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(paned, True, True, 0)
        
        # Left: File tree
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_box.set_margin_start(5)
        left_box.set_margin_end(5)
        left_box.set_margin_top(5)
        left_box.set_margin_bottom(5)
        
        left_label = Gtk.Label(label="<b>Remote Files</b>")
        left_label.set_use_markup(True)
        left_box.pack_start(left_label, False, False, 0)
        
        # Scrolled window for file tree
        scrolled_left = Gtk.ScrolledWindow()
        scrolled_left.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.file_tree = Gtk.TreeView()
        self.file_tree.set_headers_visible(True)
        scrolled_left.add(self.file_tree)
        
        left_box.pack_start(scrolled_left, True, True, 0)
        
        paned.pack1(left_box, True, False)
        
        # Right: Sync status
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_box.set_margin_start(5)
        right_box.set_margin_end(5)
        right_box.set_margin_top(5)
        right_box.set_margin_bottom(5)
        
        right_label = Gtk.Label(label="<b>Sync Status</b>")
        right_label.set_use_markup(True)
        right_box.pack_start(right_label, False, False, 0)
        
        # Sync paths list
        scrolled_right = Gtk.ScrolledWindow()
        scrolled_right.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.sync_list = Gtk.TreeView()
        self.sync_list.set_headers_visible(True)
        scrolled_right.add(self.sync_list)
        
        right_box.pack_start(scrolled_right, True, True, 0)
        
        # Sync button
        sync_button = Gtk.Button(label="Sync Now")
        sync_button.connect("clicked", self._on_sync_clicked)
        right_box.pack_start(sync_button, False, False, 0)
        
        paned.pack2(right_box, True, False)
        paned.set_position(500)
        
        # Setup file tree
        self._setup_file_tree()
        
        # Setup sync list
        self._setup_sync_list()
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = Gtk.MenuBar()
        
        # File menu
        file_menu = Gtk.Menu()
        file_item = Gtk.MenuItem(label="File")
        file_item.set_submenu(file_menu)
        
        add_sync_item = Gtk.MenuItem(label="Add Sync Path...")
        add_sync_item.connect("activate", self._on_add_sync_path)
        file_menu.append(add_sync_item)
        
        remove_sync_item = Gtk.MenuItem(label="Remove Sync Path")
        remove_sync_item.connect("activate", self._on_remove_sync_path)
        file_menu.append(remove_sync_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        file_menu.append(quit_item)
        
        menubar.append(file_item)
        
        # View menu
        view_menu = Gtk.Menu()
        view_item = Gtk.MenuItem(label="View")
        view_item.set_submenu(view_menu)
        
        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect("activate", lambda _: self._refresh_file_list())
        view_menu.append(refresh_item)
        
        menubar.append(view_item)
        
        # Help menu
        help_menu = Gtk.Menu()
        help_item = Gtk.MenuItem(label="Help")
        help_item.set_submenu(help_menu)
        
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self._on_about)
        help_menu.append(about_item)
        
        menubar.append(help_item)
        
        return menubar
    
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        
        # Sync button
        sync_icon = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.LARGE_TOOLBAR)
        sync_tool = Gtk.ToolButton(icon_widget=sync_icon, label="Sync")
        sync_tool.connect("clicked", self._on_sync_clicked)
        toolbar.insert(sync_tool, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Upload button
        upload_icon = Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.LARGE_TOOLBAR)
        upload_tool = Gtk.ToolButton(icon_widget=upload_icon, label="Upload")
        upload_tool.connect("clicked", self._on_upload_clicked)
        toolbar.insert(upload_tool, -1)
        
        # Download button
        download_icon = Gtk.Image.new_from_icon_name("document-open", Gtk.IconSize.LARGE_TOOLBAR)
        download_tool = Gtk.ToolButton(icon_widget=download_icon, label="Download")
        download_tool.connect("clicked", self._on_download_clicked)
        toolbar.insert(download_tool, -1)
        
        return toolbar
    
    def _setup_file_tree(self):
        """Setup file tree view"""
        # Name column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        column.set_sort_column_id(0)
        self.file_tree.append_column(column)
        
        # Size column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Size", renderer, text=1)
        column.set_sort_column_id(1)
        self.file_tree.append_column(column)
        
        # Modified column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Modified", renderer, text=2)
        column.set_sort_column_id(2)
        self.file_tree.append_column(column)
        
        # Type column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Type", renderer, text=3)
        self.file_tree.append_column(column)
        
        # Store
        self.file_store = Gtk.TreeStore(str, str, str, str)  # name, size, modified, type
        self.file_tree.set_model(self.file_store)
        
        # Selection
        self.file_tree.get_selection().connect("changed", self._on_file_selection_changed)
    
    def _setup_sync_list(self):
        """Setup sync status list"""
        # Local path column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Local Path", renderer, text=0)
        self.sync_list.append_column(column)
        
        # Remote path column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Remote Path", renderer, text=1)
        self.sync_list.append_column(column)
        
        # Status column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Status", renderer, text=2)
        self.sync_list.append_column(column)
        
        # Store
        self.sync_store = Gtk.ListStore(str, str, str)  # local, remote, status
        self.sync_list.set_model(self.sync_store)
        
        # Load sync paths
        self._refresh_sync_list()
    
    def _connect_signals(self):
        """Connect UI signals"""
        pass
    
    def _refresh_file_list(self, path: str = "/"):
        """Refresh file tree from remote"""
        def load_files():
            try:
                items = self.api_client.list_folder(path)
                GLib.idle_add(self._populate_file_tree, items, path)
            except Exception as e:
                logger.error(f"Error loading files: {e}")
                GLib.idle_add(self._show_error, f"Error loading files: {e}")
        
        threading.Thread(target=load_files, daemon=True).start()
    
    def _populate_file_tree(self, items, base_path: str):
        """Populate file tree with items"""
        self.file_store.clear()
        
        for item in items:
            name = item.get('name', '')
            size = str(item.get('size', 0))
            modified = item.get('modified_time', '')[:19] if item.get('modified_time') else ''
            item_type = 'Folder' if item.get('is_folder') else 'File'
            
            self.file_store.append(None, [name, size, modified, item_type])
        
        self._update_status(f"Loaded {len(items)} items")
    
    def _refresh_sync_list(self):
        """Refresh sync paths list"""
        self.sync_store.clear()
        
        sync_paths = self.config.get_sync_paths()
        for local_path, remote_path in sync_paths.items():
            status = "Active" if self.file_watcher.is_running() else "Inactive"
            self.sync_store.append([local_path, remote_path, status])
    
    def _on_file_selection_changed(self, selection):
        """Handle file selection change"""
        model, tree_iter = selection.get_selected()
        if tree_iter:
            name = model[tree_iter][0]
            self._update_status(f"Selected: {name}")
    
    def _on_sync_clicked(self, widget):
        """Handle sync button click"""
        self._update_status("Syncing...")
        
        def do_sync():
            try:
                results = self.sync_engine.sync_all()
                success_count = sum(1 for r in results if r['success'])
                GLib.idle_add(self._update_status, 
                            f"Sync complete: {success_count}/{len(results)} files synced")
                GLib.idle_add(self._refresh_sync_list)
            except Exception as e:
                logger.error(f"Sync error: {e}")
                GLib.idle_add(self._show_error, f"Sync error: {e}")
        
        threading.Thread(target=do_sync, daemon=True).start()
    
    def _on_upload_clicked(self, widget):
        """Handle upload button click"""
        dialog = Gtk.FileChooserDialog(
            title="Select File to Upload",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = Path(dialog.get_filename())
            # Get remote path from user
            remote_dialog = Gtk.Dialog(title="Enter Remote Path", parent=self.window)
            remote_dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)
            
            content_area = remote_dialog.get_content_area()
            entry = Gtk.Entry()
            entry.set_text(f"/Shared/{file_path.name}")
            content_area.pack_start(entry, True, True, 0)
            remote_dialog.show_all()
            
            if remote_dialog.run() == Gtk.ResponseType.OK:
                remote_path = entry.get_text()
                self._upload_file(file_path, remote_path)
            
            remote_dialog.destroy()
        
        dialog.destroy()
    
    def _on_download_clicked(self, widget):
        """Handle download button click"""
        selection = self.file_tree.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            name = model[tree_iter][0]
            # In a real implementation, get full path from tree
            self._update_status(f"Downloading {name}...")
    
    def _upload_file(self, local_path: Path, remote_path: str):
        """Upload a file"""
        def do_upload():
            try:
                self.api_client.upload_file(local_path, remote_path)
                GLib.idle_add(self._update_status, f"Uploaded: {local_path.name}")
                GLib.idle_add(self._refresh_file_list)
            except Exception as e:
                logger.error(f"Upload error: {e}")
                GLib.idle_add(self._show_error, f"Upload error: {e}")
        
        threading.Thread(target=do_upload, daemon=True).start()
    
    def _on_add_sync_path(self, widget):
        """Add a sync path"""
        dialog = Gtk.Dialog(title="Add Sync Path", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        
        # Local path
        local_label = Gtk.Label(label="Local Path:")
        local_label.set_halign(Gtk.Align.START)
        content_area.pack_start(local_label, False, False, 0)
        
        local_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        local_entry = Gtk.Entry()
        local_button = Gtk.Button(label="Browse...")
        local_button.connect("clicked", lambda b: self._browse_folder(local_entry))
        local_box.pack_start(local_entry, True, True, 0)
        local_box.pack_start(local_button, False, False, 0)
        content_area.pack_start(local_box, False, False, 0)
        
        # Remote path
        remote_label = Gtk.Label(label="Remote Path:")
        remote_label.set_halign(Gtk.Align.START)
        content_area.pack_start(remote_label, False, False, 0)
        
        remote_entry = Gtk.Entry()
        remote_entry.set_text("/Shared/")
        content_area.pack_start(remote_entry, False, False, 0)
        
        dialog.show_all()
        
        if dialog.run() == Gtk.ResponseType.OK:
            local_path = local_entry.get_text()
            remote_path = remote_entry.get_text()
            if local_path and remote_path:
                self.config.add_sync_path(local_path, remote_path)
                self._refresh_sync_list()
                self.file_watcher.stop()
                self.file_watcher.start()
                self._update_status(f"Added sync path: {local_path} <-> {remote_path}")
        
        dialog.destroy()
    
    def _browse_folder(self, entry: Gtk.Entry):
        """Browse for folder"""
        dialog = Gtk.FileChooserDialog(
            title="Select Folder",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        if dialog.run() == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def _on_remove_sync_path(self, widget):
        """Remove selected sync path"""
        selection = self.sync_list.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            local_path = model[tree_iter][0]
            self.config.remove_sync_path(local_path)
            self._refresh_sync_list()
            self.file_watcher.stop()
            self.file_watcher.start()
            self._update_status(f"Removed sync path: {local_path}")
    
    def _on_about(self, widget):
        """Show about dialog"""
        about = Gtk.AboutDialog()
        about.set_program_name("Egnyte Desktop")
        about.set_version("1.0.0")
        about.set_copyright("© 2024")
        about.set_comments("Native Linux desktop client for Egnyte")
        about.set_website("https://developers.egnyte.com")
        about.run()
        about.destroy()
    
    def _update_status(self, message: str):
        """Update status bar"""
        self.status_bar.push(self.status_context_id, message)
    
    def _show_error(self, message: str):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=message
        )
        dialog.run()
        dialog.destroy()

