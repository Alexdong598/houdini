import hou
import json
import sys

# 定义 JSON 文件的默认路径
JSON_BASE_PATH = r'U:\_hal\houdini_branch_tools\afx\houdini20.0\houdini\toolbar\JSONRead\JSON'

def selectJSON():
    """让用户选择一个JSON文件并返回文件路径"""
    newPath = r'U:\_hal\houdini_branch_tools\afx\houdini20.0\houdini\toolbar'
    if newPath not in sys.path:
        sys.path.append(newPath)

    json_path = hou.ui.selectFile(
        title="Select a JSON file to import",
        pattern="*.json",
        start_directory=JSON_BASE_PATH,
    )
    if not json_path:
        raise hou.Error("No file selected. Exiting.")
    return json_path

def readJSON(json_path):
    """读取JSON文件并在当前网络编辑器中创建节点"""
    try:
        with open(json_path, "r") as f:
            recipe_data = json.load(f)
    except Exception as e:
        raise hou.Error(f"Failed to read JSON file: {e}")

    if "data" not in recipe_data or "children" not in recipe_data["data"]:
        raise hou.Error('Invalid JSON: Missing "data" or "children" key.')

    created_nodes = {}
    errors = []  # 收集错误信息

    def create_nodes(parent_node, children_data):
        if parent_node.type().name() == "subnet":
            input_nodes = parent_node.indirectInputs()
            if input_nodes:
                created_nodes["input0"] = input_nodes[0]
            else:
                input_node = parent_node.createInputNode(0, "input0")
                created_nodes["input0"] = input_node

        nodes_to_create = list(children_data.items())
        
        for child_name, child_info in nodes_to_create:
            # 修正无效节点名称
            safe_name = f"node_{child_name}" if child_name.isdigit() else child_name
            try:
                node_type = child_info["type"]

                if node_type == "StickyNote":
                    new_node = parent_node.createStickyNote()
                    created_nodes[child_name] = new_node
                    
                    if "text" in child_info:
                        new_node.setText(child_info["text"])
                    if "position" in child_info:
                        pos_x, pos_y = child_info["position"]
                        new_node.setPosition([pos_x, pos_y])
                    if "size" in child_info:
                        size_x, size_y = child_info["size"]
                        new_node.setSize([size_x, size_y])
                    if "color" in child_info:
                        new_node.setColor(hou.Color(child_info["color"]))
                    if "text_color" in child_info:
                        new_node.setTextColor(hou.Color(child_info["text_color"]))
                    if "draw_background" in child_info:
                        new_node.setDrawBackground(child_info["draw_background"])

                elif node_type == "NetworkDot":
                    new_node = parent_node.createNetworkDot()
                    created_nodes[child_name] = new_node
                    
                    if "position" in child_info:
                        pos_x, pos_y = child_info["position"]
                        new_node.setPosition([pos_x, pos_y])
                    if "color" in child_info:
                        new_node.setColor(hou.Color(child_info["color"]))

                elif node_type == "NetworkBox":
                    new_box = parent_node.createNetworkBox(safe_name)
                    created_nodes[child_name] = new_box
                    
                    if "position" in child_info:
                        new_box.setPosition(child_info["position"])
                    if "size" in child_info:
                        new_box.setSize(child_info["size"])
                    if "color" in child_info:
                        new_box.setColor(hou.Color(child_info["color"]))
                    if "box_content" in child_info:
                        for content_node_name in child_info["box_content"]:
                            content_node = created_nodes.get(content_node_name)
                            if content_node:
                                new_box.addNode(content_node)

                else:
                    new_node = parent_node.createNode(node_type, safe_name)
                    created_nodes[child_name] = new_node

                    if "position" in child_info:
                        new_node.setPosition(child_info["position"])
                    if "color" in child_info:
                        new_node.setColor(hou.Color(child_info["color"]))
                    # 只对支持 setShape 的节点调用
                    if "user_data" in child_info and "nodeshape" in child_info["user_data"]:
                        if hasattr(new_node, "setShape"):
                            new_node.setShape(child_info["user_data"]["nodeshape"])
                        else:
                            errors.append(f"Node {safe_name} does not support setShape")

                    if "parms" in child_info:
                        for parm_name, parm_value in child_info["parms"].items():
                            parm = new_node.parm(parm_name)
                            if parm is None:
                                errors.append(f"Parameter {parm_name} not found on {safe_name}")
                                continue
                            try:
                                if isinstance(parm_value, list):
                                    parm_tuple = new_node.parmTuple(parm_name)
                                    for i, item in enumerate(parm_value):
                                        if isinstance(item, dict) and "expression" in item:
                                            parm_tuple[i].setExpression(item["expression"])
                                        else:
                                            parm_tuple[i].set(item)
                                elif isinstance(parm_value, dict) and "expression" in parm_value:
                                    parm.setExpression(parm_value["expression"])
                                elif isinstance(parm_value, (int, float, str)):
                                    parm.set(parm_value)
                                else:
                                    errors.append(f"Unsupported parm type for {parm_name} on {safe_name}: {type(parm_value)}")
                            except Exception as e:
                                errors.append(f"Failed to set parm {parm_name} on {safe_name}: {e}")

                    if "flags" in child_info:
                        flags = child_info["flags"]
                        if "display" in flags:
                            new_node.setDisplayFlag(flags["display"])
                        if "render" in flags:
                            new_node.setRenderFlag(flags["render"])

            except Exception as e:
                errors.append(f"Failed to create node {safe_name}: {e}")

        # 连接输入
        for child_name, child_info in nodes_to_create:
            current_node = created_nodes.get(child_name)
            if not current_node:
                continue

            if "inputs" in child_info:
                for input_info in child_info["inputs"]:
                    from_node_name = input_info["from"]
                    if from_node_name == "1" and current_node.parent().type().name() == "subnet":
                        from_node_name = "input0"
                    from_node = created_nodes.get(from_node_name)
                    if from_node:
                        to_index = input_info.get("to_index", 0)
                        current_node.setInput(to_index, from_node)
                    else:
                        errors.append(f"Input node '{from_node_name}' not found for '{child_name}'")

            if "children" in child_info:
                create_nodes(current_node, child_info["children"])

    current_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not current_pane:
        raise hou.Error("No network editor pane found.")

    current_path = current_pane.pwd().path()
    root_node = hou.node(current_path)
    
    create_nodes(root_node, recipe_data["data"]["children"])
    
    if errors:
        print("Import completed with errors:")
        for error in errors:
            print(error)
    else:
        print(f"Nodes imported successfully at {current_path}!")

def main():
    """主函数：选择JSON文件并读取"""
    json_path = selectJSON()
    readJSON(json_path)

if __name__ == "__main__":
    main()