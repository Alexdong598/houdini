def run():
    import hou
    import os
    
    node = hou.pwd()
    HDAnode = node.parent()
    
    HDAnode.parm("refreshVersion").pressButton()
    HDAnode.cook(force=True)
    
run()