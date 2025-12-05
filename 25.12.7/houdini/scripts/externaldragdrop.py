import hou
import re
import os
import sys
import traceback
import json

if sys.version_info.major < 3:
    from urllib import unquote
else:
    from urllib.parse import unquote


# ----------------- CORE DROP LOGIC -----------------
def dropAccept(*args, **kwargs):
    pane = kwargs.get("pane") if "pane" in kwargs else None
    event = kwargs.get("event") if "event" in kwargs else None
    files = None
    mime_data = None

    # 兼容多种签名
    if pane is None and len(args) >= 2 and hasattr(args[0], "type") and hasattr(args[1], "mimeData"):
        pane, event = args[0], args[1]
    if pane is None and event is None and len(args) >= 1 and isinstance(args[0], (list, tuple)):
        files = list(args[0])
        try: pane = hou.ui.paneTabUnderCursor()
        except Exception: pane = None
    if pane is None:
        try: pane = hou.ui.paneTabUnderCursor()
        except Exception: pane = None
    if not pane or pane.type().name() != "NetworkEditor":
        print("-> Drop ignored: Not a network editor.")
        return False
    print(f"-> Pane: {pane.name()}, Type: {pane.type().name()}")

    if event is not None and hasattr(event, "mimeData"):
        try: mime_data = event.mimeData()
        except Exception: mime_data = None

    try:
        CUSTOM = "application/x-shotgun-library-data"
        if mime_data and mime_data.hasFormat(CUSTOM):
            print("-> Detected custom 'shotgun-library-data' MIME.")
            raw = mime_data.data(CUSTOM)
            try:
                payload = json.loads(bytes(raw).decode("utf-8"))
            except Exception:
                traceback.print_exc()
                hou.ui.displayMessage("Invalid JSON payload from drag.", severity=hou.severityType.Error)
                return False

            file_path = (payload.get("file_path") or "").replace("\\", "/")
            node_name = payload.get("version_name") or "imported_asset"
            fmt = (payload.get("format") or "").lower()
            file_ext = ".bgeo.sc" if fmt == "bgeo.sc" else (f".{fmt}" if fmt and not fmt.startswith(".") else fmt)
            # NEW: 如果 fmt 为空，从路径再推断一次
            if not file_ext:
                lp = file_path.lower()
                if lp.endswith(".bgeo.sc"):
                    file_ext = ".bgeo.sc"
                else:
                    _, ext = os.path.splitext(lp)
                    file_ext = ext

            cursor_position = pane.cursorPosition()
            network_node = pane.pwd()
            return bool(import_file(network_node, file_path, node_name, file_ext, cursor_position))

        if mime_data and mime_data.hasFormat("text/plain-python"):
            print("-> Detected 'text/plain-python' MIME type. Executing script.")
            try:
                pyb = mime_data.data("text/plain-python")
                try: script = pyb.data().decode("utf-8")
                except AttributeError: script = bytes(pyb).decode("utf-8")
                exec(script, globals(), locals())
                print("--- Python script execution finished ---")
                return True
            except Exception as e:
                traceback.print_exc()
                hou.ui.displayMessage(f"Error executing dropped Python: {e}", severity=hou.severityType.Error)
                return False

        if mime_data and mime_data.hasText() and not files:
            txt = mime_data.text().strip()
            if (txt.startswith("/") or re.match(r"^[A-Za-z]:/", txt) or txt.startswith("$") or txt.startswith("`") or txt.startswith("file://")):
                print("-> Detected plain text payload; treating as path.")
                files = [txt]

        if mime_data and mime_data.hasUrls() and not files:
            print("-> Detected URL MIME type. Processing as file drop.")
            urls = mime_data.urls()
            files = []
            for u in urls:
                p = u.toLocalFile()
                if p: files.append(p)
                else:
                    s = u.toString()
                    if s: files.append(s)

        if files:
            for i, file_path_raw in enumerate(files):
                raw = str(file_path_raw).strip()
                if raw.startswith("file://"):
                    if raw.startswith("file:///") and ":" in raw[8:11]:
                        raw = raw.replace("file:///", "", 1)
                    else:
                        raw = raw.replace("file://", "", 1)
                raw = unquote(raw)
                file_path = raw.replace("\\", "/")

                base_name_full = os.path.basename(file_path)
                if file_path.lower().endswith(".bgeo.sc"):
                    file_ext = ".bgeo.sc"
                    file_basename = base_name_full[:-len(".bgeo.sc")]
                else:
                    file_basename, file_ext_raw = os.path.splitext(base_name_full)
                    file_ext = file_ext_raw.lower()

                if not file_ext:
                    hou.ui.displayMessage("Unsupported or empty file extension.", severity=hou.severityType.Warning)
                    continue

                cursor_position = pane.cursorPosition() + hou.Vector2(i * 2, 0)
                network_node = pane.pwd()
                print(f"  - Normalized: {file_path}")
                print(f"  - Basename: {file_basename}, Ext: {file_ext}")
                print(f"  - Target Network: {network_node.path()}")

                if file_ext == ".hip":
                    if hou.ui.displayMessage(f"Load scene?\n{file_path}", buttons=("Load", "Cancel"), default_choice=1) == 0:
                        hou.hipFile.load(file_path)
                    return True

                node_name_from_file = re.sub(r"[^0-9a-zA-Z_]+", "_", file_basename)
                ok = import_file(network_node, file_path, node_name_from_file, file_ext, cursor_position)
                if ok is False:
                    print("  - import_file returned False for this item.")
            print("--- File drop processing finished ---")
            return True

    except Exception as e:
        traceback.print_exc()
        try:
            hou.ui.displayMessage(f"An error occurred during drop: {e}", severity=hou.severityType.Error)
        except Exception:
            pass
        return False

    print("-> Drop data not recognized or empty; nothing to do.")
    return False



def import_file(network_node, file_path, node_name, file_ext, cursor_position):
    """
    统一导入入口：不依赖 UI。node_name 必须由调用方传入。
    """
    node_name = re.sub(r"[^0-9a-zA-Z_]+", "_", node_name or "imported_asset") or "imported_asset"

    print(f"  - Checking lock status for: {network_node.path()}")
    if network_node.isInsideLockedHDA():
        error_msg = (
            f"Cannot create node inside a locked asset: {network_node.name()}.\n"
            "Please unlock the asset ('Allow Editing of Contents') or drop into an unlocked network."
        )
        print(f"  - LOCK DETECTED. Aborting. Message: {error_msg}")
        hou.ui.displayMessage(
            error_msg,
            severity=hou.severityType.Error,
            title="Drop Failed: Locked Asset"
        )
        return False

    print("  - Network is not locked. Proceeding.")
    net_type_name = network_node.type().name()
    print(f"  - Network Type: {net_type_name}")

    if net_type_name == "obj":
        print("  - Dropped in /obj. Creating a new 'geo' container.")
        geo_node = network_node.createNode("geo", f"GEO_{node_name}")
        geo_node.setPosition(cursor_position)
        network_node = geo_node
        net_type_name = "geo"
        cursor_position = hou.Vector2(0, 0)
        print(f"  - New context: {network_node.path()}")

    if net_type_name in ("lopnet", "stage"):
        print(f"  - Dispatching to _import_into_lop...")
        _import_into_lop(network_node, file_path, node_name, file_ext, cursor_position)
    elif net_type_name in ("geo", "sopnet"):
        print(f"  - Dispatching to _import_into_sop...")
        _import_into_sop(network_node, file_path, node_name, file_ext, cursor_position)
    else:
        hou.ui.displayMessage(f"Drop not supported in this context: {net_type_name}", severity=hou.severityType.Warning)
        return False
    return True


def _import_into_lop(parent_node, file_path, node_name, file_ext, pos):
    """Handles the import logic within a LOP network (stage)."""
    print("\n--- _import_into_lop() called ---")
    new_node = None

    if file_ext in (".usd", ".usda", ".usdc"):
        node_type = "yu.dong::usd_lop_import"
        print(f"  - USD file detected. Creating node type: '{node_type}'")
        new_node = parent_node.createNode(node_type, node_name)
        print(f"  - Node '{new_node.name()}' created. Setting filepath...")
        new_node.parm("filepath1").set(file_path)
        print(f"  - Filepath set to: '{file_path}'")

    elif file_ext == ".abc":
        print("  - ABC file detected. Creating 'sopcreate' node...")
        new_node = parent_node.createNode("sopcreate", node_name)
        internal_sopnet = new_node.node("sopnet/create")
        print(f"  - Creating 'alembic' node inside {internal_sopnet.path()}...")
        alembic_node = internal_sopnet.createNode("alembic", "import_alembic")
        alembic_node.parm("fileName").set(file_path)
        alembic_node.setDisplayFlag(True)

    elif file_ext == ".bgeo.sc":
        print("  - BGEO.SC file detected. Creating 'sopcreate' node...")
        new_node = parent_node.createNode("sopcreate", node_name)
        internal_sopnet = new_node.node("sopnet/create")
        print(f"  - Creating 'filecache' node inside {internal_sopnet.path()}...")
        file_cache = internal_sopnet.createNode("filecache::2.0", "import_bgeo")
        file_cache.parm("loadfromdisk").set(1)
        file_cache.parm("filemethod").set("explicit")
        file_cache.parm("file").set(file_path)
        file_cache.setDisplayFlag(True)

    elif file_ext == ".vdb":
        print("  - VDB file detected. Creating 'sopcreate' + 'file' node...")
        new_node = parent_node.createNode("sopcreate", node_name)
        internal_sopnet = new_node.node("sopnet/create")
        file_node = internal_sopnet.createNode("file", "import_vdb")
        file_node.parm("file").set(file_path)
        file_node.setDisplayFlag(True)

    elif file_ext == ".obj":
        print("  - OBJ file detected. Creating 'sopcreate' + 'file' node...")
        new_node = parent_node.createNode("sopcreate", node_name)
        internal_sopnet = new_node.node("sopnet/create")
        file_node = internal_sopnet.createNode("file", "import_obj")
        file_node.parm("file").set(file_path)
        file_node.setDisplayFlag(True)

    if new_node:
        print(f"  - Finalizing node '{new_node.name()}' position and flags.")
        new_node.setPosition(pos)
        new_node.setDisplayFlag(True)
        new_node.setCurrent(True, clear_all_selected=True)
    print("--- _import_into_lop() finished ---")


def _import_into_sop(parent_node, file_path, node_name, file_ext, pos):
    """Handles the import logic within a SOP network."""
    print("\n--- _import_into_sop() called ---")
    new_node = None

    if file_ext in (".usd", ".usda", ".usdc"):
        print("  - USD file detected. Creating 'usdimport' node...")
        new_node = parent_node.createNode("usdimport", node_name)
        new_node.parm("filepath1").set(file_path)
        new_node.parm("purpose").set("render")

    elif file_ext == ".abc":
        print("  - ABC file detected. Creating 'alembic' node...")
        new_node = parent_node.createNode("alembic", node_name)
        new_node.parm("fileName").set(file_path)

    elif file_ext == ".bgeo.sc":
        print("  - BGEO.SC file detected. Creating 'filecache' node...")
        new_node = parent_node.createNode("filecache::2.0", node_name)
        new_node.parm("loadfromdisk").set(1)
        new_node.parm("filemethod").set("explicit")
        new_node.parm("file").set(file_path)

    elif file_ext == ".vdb":
        print("  - VDB file detected. Creating 'file' node...")
        new_node = parent_node.createNode("file", node_name)
        new_node.parm("file").set(file_path)

    elif file_ext == ".obj":
        print("  - OBJ file detected. Creating 'file' node...")
        new_node = parent_node.createNode("file", node_name)
        new_node.parm("file").set(file_path)

    if new_node:
        print(f"  - Finalizing node '{new_node.name()}' position and flags.")
        new_node.setPosition(pos)
        new_node.setDisplayFlag(True)
        new_node.setCurrent(True, clear_all_selected=True)
    print("--- _import_into_sop() finished ---")
