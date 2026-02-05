import hou
import json
import sys

def readJSON():
    # 文件路径设置
    newPath = r'U:\_hal\houdini_branch_tools\afx\houdini20.5\houdini\toolbar'
    sys.path.append(newPath)
    JSON_path = newPath + "/JSONRead/JSON"

    # 选择 JSON 文件
    json_path = hou.ui.selectFile(
        title="Select a JSON file to import",
        pattern="*.json",
        start_directory=JSON_path,
    )

    if not json_path:
        raise hou.Error("No file selected. Exiting.")

    # 读取 JSON 文件
    try:
        with open(json_path, "r") as f:
            recipe_data = json.load(f)
    except Exception as e:
        raise hou.Error(f"Failed to read JSON file: {e}")

    # 验证 JSON 数据结构
    if "data" not in recipe_data or "children" not in recipe_data["data"]:
        raise hou.Error('Invalid JSON: Missing "data" or "children" key.')

    created_nodes = {}
    
    def create_nodes(parent_node, children_data):
        # ================== 第一个脚本的关键改进 ==================
        # 1. 使用 indirectInputs() 获取子网输入节点
        if parent_node.type().name() == "subnet":
            input_nodes = parent_node.indirectInputs()
            if input_nodes:
                # 使用第一个输入节点（通常为 input0）
                created_nodes["input0"] = input_nodes[0]
            else:
                # 如果子网没有输入节点，自动创建一个（保持原逻辑兼容性）
                input_node = parent_node.createInputNode(0, "input0")
                created_nodes["input0"] = input_node
        # 创建节点
        nodes_to_create = list(children_data.items())
        
        for child_name, child_info in nodes_to_create:
            try:
                node_type = child_info["type"]

                if node_type == "StickyNote":  # 创建 Sticky Note
                    new_node = parent_node.createStickyNote()
                    created_nodes[child_name] = new_node
                    
                    # 设置 Sticky Note 的文本
                    if "text" in child_info:
                        new_node.setText(child_info["text"])
                    
                    # 设置 Sticky Note 的位置
                    if "position" in child_info:
                        pos_x, pos_y = child_info["position"]
                        new_node.setPosition([pos_x, pos_y])
                    
                    # 设置 Sticky Note 的大小
                    if "size" in child_info:
                        size_x, size_y = child_info["size"]
                        new_node.setSize([size_x, size_y])
                    
                    # 设置 Sticky Note 的颜色
                    if "color" in child_info:
                        color = child_info["color"]
                        new_node.setColor(hou.Color(color))
                    
                    # 设置 Sticky Note 文本颜色
                    if "text_color" in child_info:
                        text_color = child_info["text_color"]
                        new_node.setTextColor(hou.Color(text_color))
                    
                    # 设置是否绘制背景
                    if "draw_background" in child_info:
                        new_node.setDrawBackground(child_info["draw_background"])

                elif node_type == "NetworkDot":  # 创建 Pin Dot (Network Dot)
                    new_node = parent_node.createNetworkDot()
                    created_nodes[child_name] = new_node
                    
                    # 设置 Pin Dot 的位置
                    if "position" in child_info:
                        pos_x, pos_y = child_info["position"]
                        new_node.setPosition([pos_x, pos_y])
                    
                    # 设置 Pin Dot 的颜色
                    if "color" in child_info:
                        color = child_info["color"]
                        new_node.setColor(hou.Color(color))

                elif node_type == "NetworkBox":  # 创建 Network Box
                    new_box = parent_node.createNetworkBox(child_name)
                    created_nodes[child_name] = new_box
                    
                    # 设置 Network Box 的位置和大小
                    if "position" in child_info:
                        box_x, box_y = child_info["position"]
                        new_box.setPosition([box_x, box_y])
                    
                    if "size" in child_info:
                        size_x, size_y = child_info["size"]
                        new_box.setSize([size_x, size_y])
                    
                    # 设置 Network Box 的颜色
                    if "color" in child_info:
                        color = child_info["color"]
                        new_box.setColor(hou.Color(color))
                    
                    # 包含指定的节点
                    if "box_content" in child_info:
                        for content_node_name in child_info["box_content"]:
                            content_node = created_nodes.get(content_node_name)
                            if content_node:
                                new_box.addNode(content_node)

                else:  # 创建其他类型的节点
                    new_node = parent_node.createNode(node_type, child_name)
                    created_nodes[child_name] = new_node

                    # 设置节点位置
                    if "position" in child_info:
                        pos_x, pos_y = child_info["position"]
                        new_node.setPosition([pos_x, pos_y])

                    # 设置节点颜色
                    if "color" in child_info:
                        color = child_info["color"]
                        new_node.setColor(hou.Color(color))
                    
                    # 设置节点形状
                    if "user_data" in child_info and "nodeshape" in child_info["user_data"]:
                        shape = child_info["user_data"]["nodeshape"]
                        new_node.setShape(shape)

                    # 设置节点参数
                    if "parms" in child_info:
                        for parm_name, parm_value in child_info["parms"].items():
                            if isinstance(parm_value, list):
                                parm_tuple = new_node.parmTuple(parm_name)
                                for i, item in enumerate(parm_value):
                                    if isinstance(item, dict) and "expression" in item:
                                        parm_tuple[i].setExpression(item["expression"])
                                    else:
                                        parm_tuple[i].set(item)
                            else:
                                if isinstance(parm_value, dict) and "expression" in parm_value:
                                    new_node.parm(parm_name).setExpression(parm_value["expression"])
                                else:
                                    new_node.parm(parm_name).set(parm_value)

                    # 设置显示/渲染标志
                    if "flags" in child_info:
                        flags = child_info["flags"]
                        if "display" in flags:
                            new_node.setDisplayFlag(flags["display"])
                        if "render" in flags:
                            new_node.setRenderFlag(flags["render"])

            except Exception as e:
                print(f"Failed to create node {child_name}: {e}")

        # 连接输入
        for child_name, child_info in nodes_to_create:
            current_node = created_nodes.get(child_name)
            if not current_node:
                continue

            if "inputs" in child_info:
                for input_info in child_info["inputs"]:
                    from_node_name = input_info["from"]
                    from_node = created_nodes.get(from_node_name)
                    if from_node:
                        to_index = input_info.get("to_index", 0)
                        current_node.setInput(to_index, from_node)
                    else:
                        print(f"Warning: Input node '{from_node_name}' not found for '{child_name}'.")

            if "children" in child_info:
                create_nodes(current_node, child_info["children"])

    # 获取当前网络编辑器的路径
    current_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not current_pane:
        raise hou.Error("No network editor pane found.")

    current_path = current_pane.pwd().path()
    root_node = hou.node(current_path)
    
    # 调用创建节点的函数
    create_nodes(root_node, recipe_data["data"]["children"])

    print(f"Nodes imported successfully at {current_path}!")

# # 调用函数
# readJSON()
