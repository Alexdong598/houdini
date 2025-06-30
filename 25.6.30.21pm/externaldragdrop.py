import hou
import re
import os
import sys
import platform
from PySide2 import QtWidgets

# Conditionally import unquote based on Python version
if sys.version_info.major < 3:
    from urllib import unquote
else:
    from urllib.parse import unquote

# ----------------- HELPER FUNCTION -----------------

def get_shotgun_library_instance():
    """
    Finds and returns the running instance of ShotgunLibraryUI in Houdini.
    It checks both the objectName and the class name for robustness.
    """
    for widget in QtWidgets.QApplication.allWidgets():
        # Check both objectName (set explicitly) and className (from the class definition)
        if widget.objectName() == "shotgunLibraryUI_unique" or widget.metaObject().className() == "ShotgunLibraryUI":
            return widget
    return None

# ----------------- CORE DROP LOGIC -----------------

def dropAccept(files):
    """
    This function is called by Houdini when files are dropped into a network editor.
    """
    pane = hou.ui.paneTabUnderCursor()
    if not pane or pane.type().name() != "NetworkEditor":
        return False
    
    # Process each dropped file
    for i, file_uri in enumerate(files):
        # --- File Path Processing ---
        # Modern Houdini versions handle URI correctly, this code ensures compatibility.
        # It correctly decodes the file URI to a system-specific file path.
        url = hou.expandString(file_uri)
        if url.startswith('file:///'):
            path_part = url[8:]
            if platform.system() == "Windows" and path_part.startswith('/'):
                path_part = path_part[1:]
        else:
            path_part = url

        file_path = unquote(path_part).replace('/', os.sep)
        
        # --- File Info Extraction ---
        file_basename_full, file_ext_raw = os.path.splitext(os.path.basename(file_path))
        
        # Special handling for double extensions like .bgeo.sc
        if file_path.lower().endswith('.bgeo.sc'):
            file_ext = '.bgeo.sc'
            file_basename = file_basename_full.replace('.bgeo', '')
        else:
            file_ext = file_ext_raw.lower()
            file_basename = file_basename_full

        # --- Convert to Relative Path ($HIP) if applicable ---
        hip_path = hou.getenv("HIP")
        if hip_path and os.path.normpath(file_path).startswith(os.path.normpath(hip_path)):
            relative_path = "$HIP" + file_path[len(hip_path):]
            file_path = relative_path.replace(os.sep, '/')
        
        # --- Drop Context ---
        cursor_position = pane.cursorPosition() + hou.Vector2(i * 2, 0) # Use a smaller offset
        network_node = pane.pwd()

        # --- HIP File Handling (special case) ---
        if file_ext == ".hip":
            hou.hipFile.load(file_path)
            return True

        # --- Node Creation ---
        try:
            # Pass all necessary info to the import dispatcher
            import_file(network_node, file_path, file_basename, file_ext, cursor_position)
        except Exception as e:
            print(f"Failed to import file: {file_path}")
            traceback.print_exc()
            hou.ui.displayMessage(f"Failed to import file: {e}", severity=hou.severityType.Error)
            return False

    return True

def import_file(network_node, file_path, file_basename, file_ext, cursor_position):
    """
    Dispatches the import task based on the network context (LOP, SOP, etc.).
    It now gets the correct node name from the UI.
    """
    
    # --- Get Node Name from UI ---
    # This is a key change: get the name from the UI for accuracy.
    ui = get_shotgun_library_instance()
    node_name = ""
    if ui and ui.material_combo.count() > 0:
        node_name = ui.material_combo.currentText()
    
    # Fallback to file basename if UI or version name is not available
    if not node_name:
        node_name = re.sub(r"[^0-9a-zA-Z_]+", "_", file_basename) # Sanitize the name
    
    net_type_name = network_node.type().name()
    
    # --- Auto-create Geo container if dropped in /obj ---
    if net_type_name == "obj":
        geo_node = network_node.createNode("geo", f"GEO_{node_name}")
        geo_node.setPosition(cursor_position)
        network_node = geo_node  # Continue creation inside the new geo node
        net_type_name = "geo"    # Update network type for dispatching
        cursor_position = hou.Vector2(0, 0) # Reset position for inside the container

    # --- Dispatch based on final network type ---
    if net_type_name in ("lopnet", "stage"):
        _import_into_lop(network_node, file_path, node_name, file_ext, cursor_position)
    elif net_type_name in ("geo", "sopnet"):
        _import_into_sop(network_node, file_path, node_name, file_ext, cursor_position)
    else:
        print(f"Unsupported network type for this import script: {net_type_name}")
        hou.ui.displayMessage(f"Drop not supported in this context: {net_type_name}", severity=hou.severityType.Warning)
        return False
    return True

def _import_into_lop(parent_node, file_path, node_name, file_ext, pos):
    """Handles the import logic within a LOP network (stage)."""
    
    ui = get_shotgun_library_instance()
    new_node = None

    if file_ext in (".usd", ".usda", ".usdc"):
        node_type = 'sublayer' # Default
        if ui:
            # *** FIXED: Correctly get the combo box and its text ***
            import_method = ui.houdini_usd_combo.currentText()
            if "reference" in import_method:
                node_type = "reference" # Correct node type name
        else:
            print("Warning: Shotgun Library UI not found. Defaulting to 'sublayer' import.")

        new_node = parent_node.createNode(node_type, node_name)
        new_node.parm("filepath1").set(file_path)

    elif file_ext == ".abc":
        new_node = parent_node.createNode("sopcreate", node_name)
        alembic_node = new_node.node("sopnet/create").createNode("alembic", "import_alembic")
        alembic_node.parm("fileName").set(file_path)
        alembic_node.setDisplayFlag(True) # Set display on inner node
        
    elif file_ext == ".bgeo.sc":
        new_node = parent_node.createNode("sopcreate", node_name)
        file_cache = new_node.node("sopnet/create").createNode("filecache::2.0", "import_bgeo")
        file_cache.parm("loadfromdisk").set(1)
        file_cache.parm("filemethod").set("explicit")
        file_cache.parm("file").set(file_path)
        file_cache.setDisplayFlag(True) # Set display on inner node

    if new_node:
        new_node.setPosition(pos)
        new_node.setDisplayFlag(True)
        new_node.setCurrent(True, clear_all_selected=True)

def _import_into_sop(parent_node, file_path, node_name, file_ext, pos):
    """Handles the import logic within a SOP network."""
    
    new_node = None
    
    if file_ext in (".usd", ".usda", ".usdc"):
        new_node = parent_node.createNode("usdimport", node_name)
        new_node.parm("filepath1").set(file_path)
        new_node.parm("purpose").set("Render") # Render, Proxy, Guide

    elif file_ext == ".abc":
        new_node = parent_node.createNode("alembic", node_name)
        new_node.parm("fileName").set(file_path)
        
    elif file_ext == ".bgeo.sc":
        new_node = parent_node.createNode("filecache::2.0", node_name)
        new_node.parm("loadfromdisk").set(1)
        new_node.parm("filemethod").set("explicit")
        new_node.parm("file").set(file_path)

    if new_node:
        new_node.setPosition(pos)
        new_node.setDisplayFlag(True)
        new_node.setCurrent(True, clear_all_selected=True)
