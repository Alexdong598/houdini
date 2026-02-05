import os
import hou

def terrainCut():
    path = "U:/_hal/houdini_branch_tools/afx/otls"
    HDAname = "sop_yu.dong.dev.terrainCut.1.0.hda"
    HDA = os.path.join(path, HDAname)
    pane_tabs = hou.ui.paneTabs()

    for pane in pane_tabs:
        if isinstance(pane, hou.NetworkEditor):
            current_path = pane.pwd().path()

            if current_path.startswith("/stage"):
                current_node = hou.node(current_path)
                if current_node:
                    parent_node = current_node.parent()
                    if current_node.type().name() == "subnet" and current_node.name() == "create":
                        if parent_node.type().name() == "sopnet" and parent_node.name() == "sopnet":
                            hou.hda.installFile(HDA)
                            hda_type_name = hou.hda.definitionsInFile(HDA)[0].nodeType().name()
                            hda_node = current_node.createNode(hda_type_name)
                            current_node.setPosition((0, 0))
                            break
            elif current_path.startswith("/obj"):
                current_node = hou.node(current_path)
                if current_node and current_node.type().name() == "geo":
                    hou.hda.installFile(HDA)
                    hda_type_name = hou.hda.definitionsInFile(HDA)[0].nodeType().name()
                    hda_node = current_node.createNode(hda_type_name)
                    current_node.setPosition((0, 0))
                    break

