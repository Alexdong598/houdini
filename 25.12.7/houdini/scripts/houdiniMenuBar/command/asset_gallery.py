import hou
from PySide2 import QtCore, QtWidgets
import os
import sys
import traceback

# -------------------------------------------------------------------
#  Hot-Reloading Module
# -------------------------------------------------------------------
try:
    from importlib import reload
except ImportError:
    from imp import reload

# -------------------------------------------------------------------
#  Helper Functions
# -------------------------------------------------------------------
original_paths = {}

def switch_all_to_stage():
    """Switches all network editor panes to /stage context and saves their original paths."""
    global original_paths
    original_paths.clear()
    
    stage_node = hou.node('/stage')
    if not stage_node:
        print("Error: /stage context not found. Cannot switch panes.")
        return

    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor):
            original_paths[pane.name()] = pane.pwd()
            pane.setPwd(stage_node)
    print("✅ Panes temporarily switched to /stage.")


def switch_all_from_stage_to_origin():
    """Restores all network editor panes to their original saved paths."""
    global original_paths
    if not original_paths:
        return

    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.name() in original_paths:
            original_node = original_paths.get(pane.name())
            if original_node:
                try:
                    pane.setPwd(original_node)
                except hou.OperationFailed:
                    print(f"Warning: Original path '{original_node.path()}' is no longer valid. Falling back to /obj.")
                    pane.setPwd(hou.node('/obj'))
    
    print("✅ Panes restored to original paths.")
    original_paths.clear()

# -------------------------------------------------------------------
#  Right-Side Asset Browser Panel
# -------------------------------------------------------------------
class AssetBrowserPanel(QtWidgets.QWidget):
    """
    A functional asset browser with source selection, recursive folder tabs, and a file list.
    """
    SOURCES = {
        "Megascans": "DY_GALLERY_MEGASCAN",
        "Project": "DY_GALLERY_PROJECT",
        "Database": "DY_GALLERY_DATABASE"
    }

    def __init__(self, main_window, parent=None):
        super(AssetBrowserPanel, self).__init__(parent)
        self.main_window = main_window
        self._setup_ui()
        self._connect_signals()
        self.on_source_changed()

    def _setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)

        self.source_combo = QtWidgets.QComboBox()
        for display_name, env_var in self.SOURCES.items():
            self.source_combo.addItem(display_name, env_var)

        self.content_container = QtWidgets.QFrame()
        self.content_container.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.content_container_layout = QtWidgets.QVBoxLayout(self.content_container)
        self.content_container_layout.setContentsMargins(2, 2, 2, 2)

        self.main_layout.addWidget(self.source_combo)
        self.main_layout.addWidget(self.content_container, 1)

    def _connect_signals(self):
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)

    @QtCore.Slot()
    def on_source_changed(self):
        while self.content_container_layout.count():
            child = self.content_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        env_var = self.source_combo.currentData()
        source_path = os.getenv(env_var)

        if not source_path or not os.path.isdir(source_path):
            error_label = QtWidgets.QLabel(f"Invalid path or environment variable not set:\n{env_var}\n({source_path})")
            error_label.setAlignment(QtCore.Qt.AlignCenter)
            error_label.setWordWrap(True)
            self.content_container_layout.addWidget(error_label)
            return

        content_widget = self._populate_widget_recursively(source_path)
        self.content_container_layout.addWidget(content_widget)

    def _populate_widget_recursively(self, path):
        try:
            entries = os.listdir(path)
        except OSError as e:
            return QtWidgets.QLabel(f"Cannot access path: {path}\nError: {e}")

        subdirs = sorted([d for d in entries if os.path.isdir(os.path.join(path, d))])
        db_files = sorted([f for f in entries if f.endswith(".db")])

        if subdirs:
            tab_widget = QtWidgets.QTabWidget()
            for subdir_name in subdirs:
                subdir_path = os.path.join(path, subdir_name)
                child_widget = self._populate_widget_recursively(subdir_path)
                tab_widget.addTab(child_widget, subdir_name)
            return tab_widget
        
        elif db_files:
            list_widget = QtWidgets.QListWidget()
            for db_name in db_files:
                item = QtWidgets.QListWidgetItem(os.path.splitext(db_name)[0])
                full_path = os.path.join(path, db_name)
                item.setData(QtCore.Qt.UserRole, full_path)
                item.setToolTip(full_path)
                list_widget.addItem(item)
            
            list_widget.currentItemChanged.connect(self.on_db_file_selected)
            return list_widget
            
        else:
            return QtWidgets.QLabel("No subfolders or .db files found.")

    @QtCore.Slot(QtWidgets.QListWidgetItem)
    def on_db_file_selected(self, current_item):
        if not current_item:
            return
        
        db_path = current_item.data(QtCore.Qt.UserRole)
        print(f"Selected DB file path: {db_path}")
        hou.putenv("ASSETGALLERY_DATA_SOURCE", db_path)

        # Close the window. WA_DeleteOnClose ensures it gets destroyed.
        print("✅ DB source set. Re-launching the Asset Gallery to apply changes...")
        self.main_window.close()

        # Schedule a relaunch after the current event loop finishes processing the close event.
        # This prevents issues with the singleton check in the launch function.
        QtCore.QTimer.singleShot(0, launch_asset_gallery)

# -------------------------------------------------------------------
#  Main UI Class
# -------------------------------------------------------------------
class AssetGalleryWindow(QtWidgets.QWidget):
    OBJECT_NAME = "MyUniqueAssetGalleryWindow"

    def __init__(self, parent=None):
        super(AssetGalleryWindow, self).__init__(parent)
        self._setup_properties()
        self._create_widgets()
        self._create_layout()

    def _setup_properties(self):
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("Asset Gallery Pro")
        self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.resize(1400, 800)

    def _create_widgets(self):
        try:
            import layout.assetgallery as assetgallery
            self.asset_gallery_widget = assetgallery.Window()
        except ImportError:
            self.asset_gallery_widget = QtWidgets.QLabel("Error: 'layout.assetgallery' module not found!")
            self.asset_gallery_widget.setAlignment(QtCore.Qt.AlignCenter)

        self.right_panel = AssetBrowserPanel(main_window=self)
        
    def _create_layout(self):
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.asset_gallery_widget)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([900, 500])

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(self.splitter)
    
    def refresh_left_panel(self):
        print("▶️ Main window received request to refresh left panel...")
        if hasattr(self.asset_gallery_widget, "reload_view"):
            self.asset_gallery_widget.reload_view()
        else:
            print("❌ ERROR: 'layout.assetgallery.Window' has no 'reload_view' method.")
            hou.ui.displayMessage(
                "Cannot refresh: Implement a 'reload_view' method in layout.assetgallery.",
                severity=hou.severityType.Error
            )

# -------------------------------------------------------------------
#  Launcher Function
# -------------------------------------------------------------------
def launch_asset_gallery():
    """
    Manages the singleton instance of the Asset Gallery window, including hot-reloading.
    """
    # For hot-reloading to work reliably, save this script as a .py file (e.g., "asset_gallery_pro.py")
    # and place it in a directory in Houdini's Python path (e.g., .../python3.9libs).
    # Then, your shelf tool should use:
    #
    # import asset_gallery_pro
    # reload(asset_gallery_pro)
    # asset_gallery_pro.launch_asset_gallery()
    
    try:
        import layout.assetgallery
        reload(layout.assetgallery)
    except ImportError:
        pass

    main_window = hou.qt.mainWindow()
    for widget in main_window.findChildren(QtWidgets.QWidget, AssetGalleryWindow.OBJECT_NAME):
        if widget.isVisible():
            print("Window already exists. Bringing it to the front.")
            widget.setWindowState(widget.windowState() & ~QtCore.Qt.WindowMinimized | QtCore.Qt.WindowActive)
            widget.raise_()
            widget.activateWindow()
            return

    print("Creating new Asset Gallery window...")
    
    switch_all_to_stage()
    try:
        gallery_window = AssetGalleryWindow()
        gallery_window.show()
    except Exception as e:
        print("A critical error occurred while creating the window:")
        traceback.print_exc()
        hou.ui.displayMessage(f"Error creating window:\n{e}", severity=hou.severityType.Error)
    finally:
        switch_all_from_stage_to_origin()

# -------------------------------------------------------------------
#  Main Execution Entry Point
# -------------------------------------------------------------------
# if __name__ == "__main__":
launch_asset_gallery()