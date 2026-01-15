"""Main window for GTK3 GUI"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, GLib, Gdk, GdkPixbuf
import threading
import logging
import subprocess
from datetime import datetime
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
        self.current_path = "/"
        self.path_history = []
        self.mount_point = None
        
        # Build UI
        self.builder = Gtk.Builder()
        self._build_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Start file watcher with activity callback if not already running
        if not self.file_watcher.is_running():
            self.file_watcher.start(sync_callback=self._on_auto_sync)
        
        # Add window to application
        app.add_window(self.window)
        
        # Load initial data
        self._refresh_file_list(self.current_path)
        
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
        
        # Path/search bar
        nav_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        nav_bar.set_margin_start(6)
        nav_bar.set_margin_end(6)
        nav_bar.set_margin_top(2)
        nav_bar.set_margin_bottom(2)
        
        self.back_button = Gtk.Button.new_from_icon_name("go-previous", Gtk.IconSize.BUTTON)
        self.back_button.connect("clicked", self._on_back_clicked)
        nav_bar.pack_start(self.back_button, False, False, 0)
        
        self.up_button = Gtk.Button.new_from_icon_name("go-up", Gtk.IconSize.BUTTON)
        self.up_button.connect("clicked", self._on_up_clicked)
        nav_bar.pack_start(self.up_button, False, False, 0)
        
        self.path_entry = Gtk.Entry()
        self.path_entry.set_placeholder_text("Remote path (e.g. /Shared/Documents)")
        self.path_entry.set_text(self.current_path)
        self.path_entry.connect("activate", self._on_path_activate)
        nav_bar.pack_start(self.path_entry, True, True, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search in current folder")
        self.search_entry.connect("activate", self._on_search_activate)
        nav_bar.pack_start(self.search_entry, False, False, 0)
        
        main_box.pack_start(nav_bar, False, False, 0)
        
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
        
        # Right: Notebook (Sync, Details, Activity, Transfers)
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_box.set_margin_start(5)
        right_box.set_margin_end(5)
        right_box.set_margin_top(5)
        right_box.set_margin_bottom(5)
        
        self.right_notebook = Gtk.Notebook()
        self.right_notebook.set_scrollable(True)
        
        sync_page = self._build_sync_page()
        details_page = self._build_details_page()
        activity_page = self._build_activity_page()
        transfers_page = self._build_transfers_page()
        
        self.right_notebook.append_page(sync_page, Gtk.Label(label="Sync"))
        self.right_notebook.append_page(details_page, Gtk.Label(label="Details"))
        self.right_notebook.append_page(activity_page, Gtk.Label(label="Activity"))
        self.right_notebook.append_page(transfers_page, Gtk.Label(label="Transfers"))
        
        right_box.pack_start(self.right_notebook, True, True, 0)
        
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
        
        new_folder_item = Gtk.MenuItem(label="New Folder...")
        new_folder_item.connect("activate", self._on_new_folder_clicked)
        file_menu.append(new_folder_item)
        
        upload_item = Gtk.MenuItem(label="Upload File...")
        upload_item.connect("activate", self._on_upload_clicked)
        file_menu.append(upload_item)
        
        download_item = Gtk.MenuItem(label="Download Selected...")
        download_item.connect("activate", self._on_download_clicked)
        file_menu.append(download_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        add_sync_item = Gtk.MenuItem(label="Add Sync Path...")
        add_sync_item.connect("activate", self._on_add_sync_path)
        file_menu.append(add_sync_item)
        
        remove_sync_item = Gtk.MenuItem(label="Remove Sync Path")
        remove_sync_item.connect("activate", self._on_remove_sync_path)
        file_menu.append(remove_sync_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        mount_item = Gtk.MenuItem(label="Mount...")
        mount_item.connect("activate", self._on_mount_clicked)
        file_menu.append(mount_item)
        
        unmount_item = Gtk.MenuItem(label="Unmount")
        unmount_item.connect("activate", self._on_unmount_clicked)
        file_menu.append(unmount_item)
        
        file_menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        file_menu.append(quit_item)
        
        menubar.append(file_item)
        
        # Edit menu
        edit_menu = Gtk.Menu()
        edit_item = Gtk.MenuItem(label="Edit")
        edit_item.set_submenu(edit_menu)
        
        rename_item = Gtk.MenuItem(label="Rename...")
        rename_item.connect("activate", self._on_rename_clicked)
        edit_menu.append(rename_item)
        
        delete_item = Gtk.MenuItem(label="Delete")
        delete_item.connect("activate", self._on_delete_clicked)
        edit_menu.append(delete_item)
        
        menubar.append(edit_item)
        
        # View menu
        view_menu = Gtk.Menu()
        view_item = Gtk.MenuItem(label="View")
        view_item.set_submenu(view_menu)
        
        refresh_item = Gtk.MenuItem(label="Refresh")
        refresh_item.connect("activate", lambda _: self._refresh_file_list(self.current_path))
        view_menu.append(refresh_item)
        
        view_menu.append(Gtk.SeparatorMenuItem())
        
        toggle_dark_item = Gtk.MenuItem(label="Toggle Dark Theme")
        toggle_dark_item.connect("activate", self._on_toggle_dark_theme)
        view_menu.append(toggle_dark_item)
        
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
        
        back_icon = Gtk.Image.new_from_icon_name("go-previous", Gtk.IconSize.LARGE_TOOLBAR)
        back_tool = Gtk.ToolButton(icon_widget=back_icon, label="Back")
        back_tool.connect("clicked", self._on_back_clicked)
        toolbar.insert(back_tool, -1)
        
        up_icon = Gtk.Image.new_from_icon_name("go-up", Gtk.IconSize.LARGE_TOOLBAR)
        up_tool = Gtk.ToolButton(icon_widget=up_icon, label="Up")
        up_tool.connect("clicked", self._on_up_clicked)
        toolbar.insert(up_tool, -1)
        
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.LARGE_TOOLBAR)
        refresh_tool = Gtk.ToolButton(icon_widget=refresh_icon, label="Refresh")
        refresh_tool.connect("clicked", lambda _: self._refresh_file_list(self.current_path))
        toolbar.insert(refresh_tool, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        new_folder_icon = Gtk.Image.new_from_icon_name("folder-new", Gtk.IconSize.LARGE_TOOLBAR)
        new_folder_tool = Gtk.ToolButton(icon_widget=new_folder_icon, label="New Folder")
        new_folder_tool.connect("clicked", self._on_new_folder_clicked)
        toolbar.insert(new_folder_tool, -1)
        
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
        
        delete_icon = Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.LARGE_TOOLBAR)
        delete_tool = Gtk.ToolButton(icon_widget=delete_icon, label="Delete")
        delete_tool.connect("clicked", self._on_delete_clicked)
        toolbar.insert(delete_tool, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        sync_icon = Gtk.Image.new_from_icon_name("view-refresh", Gtk.IconSize.LARGE_TOOLBAR)
        sync_tool = Gtk.ToolButton(icon_widget=sync_icon, label="Sync")
        sync_tool.connect("clicked", self._on_sync_clicked)
        toolbar.insert(sync_tool, -1)
        
        return toolbar

    def _build_sync_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label(label="<b>Sync Paths</b>")
        label.set_use_markup(True)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.sync_list = Gtk.TreeView()
        self.sync_list.set_headers_visible(True)
        scrolled.add(self.sync_list)
        
        box.pack_start(scrolled, True, True, 0)
        
        button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sync_button = Gtk.Button(label="Sync Now")
        sync_button.connect("clicked", self._on_sync_clicked)
        button_row.pack_start(sync_button, False, False, 0)
        
        add_button = Gtk.Button(label="Add")
        add_button.connect("clicked", self._on_add_sync_path)
        button_row.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button(label="Remove")
        remove_button.connect("clicked", self._on_remove_sync_path)
        button_row.pack_start(remove_button, False, False, 0)
        
        box.pack_start(button_row, False, False, 0)
        
        return box
    
    def _build_details_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label(label="<b>Item Details</b>")
        label.set_use_markup(True)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)
        
        grid = Gtk.Grid(column_spacing=8, row_spacing=6)
        grid.set_column_homogeneous(False)
        
        fields = ["Name", "Path", "Type", "Size", "Modified", "Checksum"]
        self.detail_labels = {}
        for i, field in enumerate(fields):
            field_label = Gtk.Label(label=f"{field}:")
            field_label.set_halign(Gtk.Align.START)
            value_label = Gtk.Label(label="-")
            value_label.set_halign(Gtk.Align.START)
            value_label.set_selectable(True)
            grid.attach(field_label, 0, i, 1, 1)
            grid.attach(value_label, 1, i, 1, 1)
            self.detail_labels[field.lower()] = value_label
        
        box.pack_start(grid, False, False, 0)
        return box
    
    def _build_activity_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label(label="<b>Activity</b>")
        label.set_use_markup(True)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.activity_list = Gtk.TreeView()
        self.activity_store = Gtk.ListStore(str, str, str)  # time, action, detail
        self.activity_list.set_model(self.activity_store)
        
        for idx, title in enumerate(["Time", "Action", "Detail"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=idx)
            self.activity_list.append_column(column)
        
        scrolled.add(self.activity_list)
        box.pack_start(scrolled, True, True, 0)
        return box
    
    def _build_transfers_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label(label="<b>Transfers</b>")
        label.set_use_markup(True)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.transfers_list = Gtk.TreeView()
        self.transfers_store = Gtk.ListStore(str, str, str, str)  # time, direction, name, status
        self.transfers_list.set_model(self.transfers_store)
        
        for idx, title in enumerate(["Time", "Direction", "Name", "Status"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=idx)
            self.transfers_list.append_column(column)
        
        scrolled.add(self.transfers_list)
        box.pack_start(scrolled, True, True, 0)
        return box
    
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
        self.file_store = Gtk.TreeStore(str, str, str, str, str, bool)  # name, size, modified, type, path, is_folder
        self.file_tree.set_model(self.file_store)
        
        # Selection
        self.file_tree.get_selection().connect("changed", self._on_file_selection_changed)
        self.file_tree.connect("row-activated", self._on_row_activated)
        self.file_tree.connect("button-press-event", self._on_file_tree_button_press)
    
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

    def _normalize_path(self, path: str) -> str:
        if not path:
            return "/"
        if not path.startswith("/"):
            path = "/" + path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        return path
    
    def _navigate_to(self, path: str, push_history: bool = True):
        path = self._normalize_path(path)
        if push_history and path != self.current_path:
            self.path_history.append(self.current_path)
        self.current_path = path
        self.path_entry.set_text(self.current_path)
        self._refresh_file_list(self.current_path)
    
    def _on_path_activate(self, widget):
        self._navigate_to(self.path_entry.get_text(), push_history=True)
    
    def _on_back_clicked(self, widget):
        if not self.path_history:
            return
        previous = self.path_history.pop()
        self._navigate_to(previous, push_history=False)
    
    def _on_up_clicked(self, widget):
        if self.current_path == "/":
            return
        parent = "/".join(self.current_path.rstrip("/").split("/")[:-1])
        self._navigate_to(parent or "/", push_history=True)
    
    def _on_search_activate(self, widget):
        query = self.search_entry.get_text().strip()
        if not query:
            self._refresh_file_list(self.current_path)
            return
        
        def do_search():
            try:
                results = self.api_client.search(query, folder=self.current_path)
                items = [r.get('item', r) for r in results]
                GLib.idle_add(self._populate_file_tree, items, self.current_path)
                GLib.idle_add(self._update_status, f"Search results for '{query}'")
                GLib.idle_add(self._log_activity, "Search", f"{query} in {self.current_path}")
            except Exception as e:
                logger.error(f"Search error: {e}")
                GLib.idle_add(self._show_error, f"Search error: {e}")
        
        threading.Thread(target=do_search, daemon=True).start()
    
    def _refresh_file_list(self, path: str = "/"):
        """Refresh file tree from remote"""
        self.path_entry.set_text(self.current_path)
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
            item_path = item.get('path')
            if not item_path:
                base = base_path.rstrip("/") or "/"
                item_path = f"{base}/{name}" if base != "/" else f"/{name}"
            
            self.file_store.append(None, [name, size, modified, item_type, item_path, item.get('is_folder', False)])
        
        self._update_status(f"Loaded {len(items)} items from {base_path}")
    
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
            path = model[tree_iter][4]
            self._update_status(f"Selected: {name} ({path})")
            self._load_details(path)

    def _get_selected_item(self):
        selection = self.file_tree.get_selection()
        model, tree_iter = selection.get_selected()
        if not tree_iter:
            return None
        return {
            "name": model[tree_iter][0],
            "path": model[tree_iter][4],
            "is_folder": model[tree_iter][5],
        }
    
    def _on_row_activated(self, tree, path, column):
        item = self._get_selected_item()
        if not item:
            return
        if item["is_folder"]:
            self._navigate_to(item["path"], push_history=True)
        else:
            self._download_selected_item()
    
    def _on_file_tree_button_press(self, widget, event):
        if event.button == 3:  # right click
            self._show_context_menu()
            return True
        return False
    
    def _show_context_menu(self):
        menu = Gtk.Menu()
        
        open_item = Gtk.MenuItem(label="Open")
        open_item.connect("activate", self._on_open_clicked)
        menu.append(open_item)
        
        download_item = Gtk.MenuItem(label="Download")
        download_item.connect("activate", self._on_download_clicked)
        menu.append(download_item)
        
        rename_item = Gtk.MenuItem(label="Rename")
        rename_item.connect("activate", self._on_rename_clicked)
        menu.append(rename_item)
        
        delete_item = Gtk.MenuItem(label="Delete")
        delete_item.connect("activate", self._on_delete_clicked)
        menu.append(delete_item)
        
        menu.show_all()
        menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def _log_activity(self, action: str, detail: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.activity_store.prepend([timestamp, action, detail])
    
    def _add_transfer(self, direction: str, name: str, status: str = "Queued"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        return self.transfers_store.prepend([timestamp, direction, name, status])
    
    def _update_transfer_status(self, tree_iter, status: str):
        try:
            self.transfers_store.set_value(tree_iter, 3, status)
        except Exception:
            pass

    def _set_detail(self, key: str, value: str):
        label = self.detail_labels.get(key)
        if label:
            label.set_text(value if value else "-")
    
    def _load_details(self, path: str):
        def do_load():
            try:
                info = self.api_client.get_file_info(path)
                name = info.get('name', '')
                item_type = "Folder" if info.get('is_folder') else "File"
                size = str(info.get('size', 0))
                modified = info.get('modified_time', '')[:19] if info.get('modified_time') else ''
                checksum = info.get('checksum', '') or ''
                
                def apply():
                    self._set_detail("name", name)
                    self._set_detail("path", path)
                    self._set_detail("type", item_type)
                    self._set_detail("size", size)
                    self._set_detail("modified", modified)
                    self._set_detail("checksum", checksum)
                GLib.idle_add(apply)
            except Exception as e:
                logger.error(f"Details error: {e}")
                def apply_error():
                    self._set_detail("name", "")
                    self._set_detail("path", path)
                    self._set_detail("type", "")
                    self._set_detail("size", "")
                    self._set_detail("modified", "")
                    self._set_detail("checksum", "")
                GLib.idle_add(apply_error)
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def _on_sync_clicked(self, widget):
        """Handle sync button click"""
        self._update_status("Syncing...")
        self._log_activity("Sync", "Manual sync started")
        
        def do_sync():
            try:
                results = self.sync_engine.sync_all()
                success_count = sum(1 for r in results if r['success'])
                GLib.idle_add(self._update_status, 
                            f"Sync complete: {success_count}/{len(results)} files synced")
                GLib.idle_add(self._log_activity, "Sync", f"Completed: {success_count}/{len(results)}")
                GLib.idle_add(self._refresh_sync_list)
            except Exception as e:
                logger.error(f"Sync error: {e}")
                GLib.idle_add(self._show_error, f"Sync error: {e}")
        
        threading.Thread(target=do_sync, daemon=True).start()

    def _on_auto_sync(self, local_path: Path, remote_path: str):
        message = f"Auto-synced {local_path.name} → {remote_path}"
        GLib.idle_add(self._log_activity, "Auto Sync", message)
    
    def _on_open_clicked(self, widget):
        item = self._get_selected_item()
        if not item:
            return
        if item["is_folder"]:
            self._navigate_to(item["path"], push_history=True)
        else:
            self._download_selected_item()
    
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
            default_remote = f"{self.current_path.rstrip('/')}/{file_path.name}" if self.current_path != "/" else f"/{file_path.name}"
            remote_dialog = Gtk.Dialog(title="Upload To", parent=self.window)
            remote_dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                     Gtk.STOCK_OK, Gtk.ResponseType.OK)
            
            content_area = remote_dialog.get_content_area()
            entry = Gtk.Entry()
            entry.set_text(default_remote)
            content_area.pack_start(entry, True, True, 0)
            remote_dialog.show_all()
            
            if remote_dialog.run() == Gtk.ResponseType.OK:
                remote_path = entry.get_text().strip()
                if remote_path:
                    transfer_iter = self._add_transfer("Upload", file_path.name, "Queued")
                    self._upload_file(file_path, remote_path, transfer_iter=transfer_iter)
            
            remote_dialog.destroy()
        
        dialog.destroy()
    
    def _on_download_clicked(self, widget):
        """Handle download button click"""
        self._download_selected_item()

    def _download_selected_item(self):
        item = self._get_selected_item()
        if not item:
            return
        if item["is_folder"]:
            self._show_error("Download is only supported for files.")
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Save File As",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name(item["name"])
        
        if dialog.run() == Gtk.ResponseType.OK:
            local_path = Path(dialog.get_filename())
            self._update_status(f"Downloading {item['name']}...")
            transfer_iter = self._add_transfer("Download", item["name"], "Queued")
            
            def do_download():
                try:
                    if transfer_iter:
                        GLib.idle_add(self._update_transfer_status, transfer_iter, "In Progress")
                    self.api_client.download_file(item["path"], local_path)
                    GLib.idle_add(self._update_status, f"Downloaded to: {local_path}")
                    GLib.idle_add(self._log_activity, "Download", f"{item['name']} → {local_path}")
                    if transfer_iter:
                        GLib.idle_add(self._update_transfer_status, transfer_iter, "Completed")
                except Exception as e:
                    logger.error(f"Download error: {e}")
                    GLib.idle_add(self._show_error, f"Download error: {e}")
                    if transfer_iter:
                        GLib.idle_add(self._update_transfer_status, transfer_iter, "Failed")
            
            threading.Thread(target=do_download, daemon=True).start()
        
        dialog.destroy()
    
    def _upload_file(self, local_path: Path, remote_path: str, transfer_iter=None):
        """Upload a file"""
        def do_upload():
            try:
                if transfer_iter:
                    GLib.idle_add(self._update_transfer_status, transfer_iter, "In Progress")
                self.api_client.upload_file(local_path, remote_path)
                GLib.idle_add(self._update_status, f"Uploaded: {local_path.name}")
                GLib.idle_add(self._log_activity, "Upload", f"{local_path.name} → {remote_path}")
                GLib.idle_add(self._refresh_file_list, self.current_path)
                if transfer_iter:
                    GLib.idle_add(self._update_transfer_status, transfer_iter, "Completed")
            except Exception as e:
                logger.error(f"Upload error: {e}")
                GLib.idle_add(self._show_error, f"Upload error: {e}")
                if transfer_iter:
                    GLib.idle_add(self._update_transfer_status, transfer_iter, "Failed")
        
        threading.Thread(target=do_upload, daemon=True).start()

    def _on_new_folder_clicked(self, widget):
        dialog = Gtk.Dialog(title="New Folder", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK)
        content_area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("Folder name")
        content_area.pack_start(entry, True, True, 0)
        dialog.show_all()
        
        if dialog.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            if name:
                folder_path = f"{self.current_path.rstrip('/')}/{name}" if self.current_path != "/" else f"/{name}"
                def do_create():
                    try:
                        self.api_client.create_folder(folder_path)
                        GLib.idle_add(self._update_status, f"Created folder: {folder_path}")
                        GLib.idle_add(self._log_activity, "New Folder", folder_path)
                        GLib.idle_add(self._refresh_file_list, self.current_path)
                    except Exception as e:
                        logger.error(f"Create folder error: {e}")
                        GLib.idle_add(self._show_error, f"Create folder error: {e}")
                threading.Thread(target=do_create, daemon=True).start()
        dialog.destroy()
    
    def _on_delete_clicked(self, widget):
        item = self._get_selected_item()
        if not item:
            return
        
        confirm = Gtk.MessageDialog(
            parent=self.window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            message_format=f"Delete {item['name']}?"
        )
        response = confirm.run()
        confirm.destroy()
        
        if response != Gtk.ResponseType.OK:
            return
        
        def do_delete():
            try:
                self.api_client.delete_file(item["path"])
                GLib.idle_add(self._update_status, f"Deleted: {item['name']}")
                GLib.idle_add(self._log_activity, "Delete", item["path"])
                GLib.idle_add(self._refresh_file_list, self.current_path)
            except Exception as e:
                logger.error(f"Delete error: {e}")
                GLib.idle_add(self._show_error, f"Delete error: {e}")
        
        threading.Thread(target=do_delete, daemon=True).start()
    
    def _on_rename_clicked(self, widget):
        item = self._get_selected_item()
        if not item:
            return
        
        dialog = Gtk.Dialog(title="Rename", parent=self.window)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK)
        content_area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text(item["name"])
        content_area.pack_start(entry, True, True, 0)
        dialog.show_all()
        
        if dialog.run() == Gtk.ResponseType.OK:
            new_name = entry.get_text().strip()
            if new_name and new_name != item["name"]:
                parent = "/".join(item["path"].rstrip("/").split("/")[:-1]) or "/"
                new_path = f"{parent.rstrip('/')}/{new_name}" if parent != "/" else f"/{new_name}"
                def do_rename():
                    try:
                        self.api_client.move_file(item["path"], new_path)
                        GLib.idle_add(self._update_status, f"Renamed to: {new_name}")
                        GLib.idle_add(self._log_activity, "Rename", f"{item['path']} → {new_path}")
                        GLib.idle_add(self._refresh_file_list, self.current_path)
                    except Exception as e:
                        logger.error(f"Rename error: {e}")
                        GLib.idle_add(self._show_error, f"Rename error: {e}")
                threading.Thread(target=do_rename, daemon=True).start()
        dialog.destroy()
    
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
    
    def _on_mount_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Mount Point",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        if dialog.run() == Gtk.ResponseType.OK:
            mount_point = dialog.get_filename()
            self.mount_point = mount_point
            self._update_status(f"Mounting to {mount_point}...")
            
            def do_mount():
                try:
                    from ..fuse_mount import mount_egnyte
                    mount_egnyte(mount_point, self.config, self.api_client, foreground=False)
                    GLib.idle_add(self._update_status, f"Mounted at {mount_point}")
                    GLib.idle_add(self._log_activity, "Mount", mount_point)
                except Exception as e:
                    logger.error(f"Mount error: {e}")
                    GLib.idle_add(self._show_error, f"Mount error: {e}")
            
            threading.Thread(target=do_mount, daemon=True).start()
        
        dialog.destroy()
    
    def _on_unmount_clicked(self, widget):
        if not self.mount_point:
            self._show_error("No active mount point.")
            return
        
        self._update_status(f"Unmounting {self.mount_point}...")
        try:
            subprocess.run(['fusermount', '-u', self.mount_point], check=False)
            self._update_status(f"Unmounted {self.mount_point}")
            self._log_activity("Unmount", self.mount_point)
            self.mount_point = None
        except Exception as e:
            self._show_error(f"Unmount error: {e}")
    
    def _on_toggle_dark_theme(self, widget):
        settings = Gtk.Settings.get_default()
        if not settings:
            return
        current = settings.get_property("gtk-application-prefer-dark-theme")
        settings.set_property("gtk-application-prefer-dark-theme", not current)
    
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

