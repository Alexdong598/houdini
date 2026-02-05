#使用说明：
#将/stage/mteriallibrary下的mtlxmaterial节点右键存为digital asset,asset label 和 tab submenu设为mymtlx。
#在工具架新建脚本，将以下代码粘贴到script中。
#选中具有Mesh信息的LOP节点，点击执行脚本

import hou

# 获取当前选中的节点
selected_nodes = hou.selectedNodes()

if not selected_nodes:
    raise Exception("没有选中的节点。")

# 获取第一个选中的节点
node = selected_nodes[0]

# 打印选中的节点信息
print(f"选中的节点: {node.path()}")
print(f"选中节点的类型: {node.type().name()}")

# 尝试获取 stage 对象
stage = node.stage()

if stage is None:
    raise Exception("无法获取 LOP Stage。")

# 获取几何体节点中的所有 Mesh 名称并去重
all_meshes = set()

def collect_meshes(prim):
    if prim.GetTypeName() == 'Mesh':
        mesh_name = prim.GetPath().name  # 获取路径的最后一部分作为名称
        all_meshes.add(mesh_name)
    for child in prim.GetChildren():
        collect_meshes(child)

# 遍历 stage 中的所有根原始体
for root_prim in stage.GetPseudoRoot().GetChildren():
    collect_meshes(root_prim)

# 打印所有的 Mesh 名称
print("Found Meshes:", all_meshes)

# 将 Mesh 名称保存到一个列表中
mesh_names = list(all_meshes)

# 在 /stage 上下文中创建 materiallibrary 节点
stage_context = node.parent()
material_library_node = stage_context.createNode("materiallibrary", "my_materiallibrary")

# 设置参数 matpathprefix 为 /mtl/
material_library_node.parm("matpathprefix").set("/mtl/")

# 在 materiallibrary 节点内部基于列表数量创建 mymtlx 节点
for mesh_name in mesh_names:
    mymtlx_node = material_library_node.createNode("mymtlx", f"mtlx_{mesh_name}")
    mymtlx_node.setMaterialFlag(True)
    mymtlx_node.allowEditingOfContents()  # 将节点设为可编辑模式
    print(f"Created mymtlx node: {mymtlx_node.path()}")

# 设置 materiallibrary 节点显示标志
material_library_node.setDisplayFlag(True)

# 将 materiallibrary 节点连接到选中节点的输出
outputs = node.outputs()
if outputs:
    for output in outputs:
        output.setInput(0, material_library_node)
else:
    material_library_node.setNextInput(node)

# 保存和刷新 Houdini UI
hou.ui.displayMessage(f"Successfully created and configured mymtlx nodes in {material_library_node.path()}")
material_library_node.layoutChildren()

print("Completed creating and configuring mymtlx nodes.")
