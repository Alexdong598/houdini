import os
import hou

def USD_Component_Input():
    hda_path = "U:/_hal/houdini_branch_tools/afx/otls/lop_yu.dong.USD_Component_Input.hda"
    try:
        stage = hou.node("/stage")
        hda_def = hou.hda.definitionsInFile(hda_path)[0]
        if not hda_def.isInstalled():
            hda_def.install()
        new_node = stage.createNode(hda_def.nodeTypeName())
        new_node.setPosition(hou.ui.curDesktop().paneTabOfType(hou.paneTabType.NetworkEditor).visibleBounds().center())
        
    except:
        hou.ui.displayMessage("创建失败！检查HDA路径是否正确")
