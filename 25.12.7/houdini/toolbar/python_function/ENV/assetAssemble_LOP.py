import hou
import json
import re
import sys

def assetAssemble_LOP():
    newPath = r'U:\_hal\houdini_branch_tools\afx\houdini20.5\houdini\toolbar'
    sys.path.append(newPath)
    json_path = newPath + "/JSONRead/JSON/modelProcessedSop.json"

    if not json_path:
        raise hou.Error("No file selected. Exiting.")

    try:
        with open(json_path, "r") as f:
            recipe_data = json.load(f)
    except Exception as e:
        raise hou.Error(f"Failed to read JSON file: {e}")

    if "data" not in recipe_data:
        raise hou.Error('The JSON file does not contain a "data" key.')

    created_nodes = {}

    def create_nodes(parent_node, children_data):
        for child_name, child_info in children_data.items():
            try:
                node_type = child_info["type"]
                new_node = parent_node.createNode(node_type, child_name)
                created_nodes[child_name] = new_node  

                if "position" in child_info:
                    pos_x, pos_y = child_info["position"]
                    new_node.setPosition([pos_x, pos_y])

                if "parms" in child_info:
                    for parm_name, parm_value in child_info["parms"].items():
                        new_node.parm(parm_name).set(parm_value)

                if "flags" in child_info:
                    flags = child_info["flags"]
                    if "display" in flags:
                        new_node.setDisplayFlag(flags["display"])
                    if "render" in flags:
                        new_node.setRenderFlag(flags["render"])

            except Exception as e:
                print(f"Failed to create node {child_name}: {e}")

        for child_name, child_info in children_data.items():
            if "inputs" in child_info:
                for input_info in child_info["inputs"]:
                    from_node_name = input_info["from"]
                    from_index = input_info.get("from_index", 0)
                    to_index = input_info.get("to_index", 0)

                    if from_node_name in created_nodes and child_name in created_nodes:
                        from_node = created_nodes[from_node_name]
                        to_node = created_nodes[child_name]
                        to_node.setInput(to_index, from_node)
                    else:
                        print(f"Warning: Input node '{from_node_name}' not found for '{child_name}'.")

            if "children" in child_info:
                create_nodes(created_nodes[child_name], child_info["children"])

    current_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not current_pane:
        raise hou.Error("No network editor pane found.")

    current_path = current_pane.pwd().path()  

    root_node = hou.node(current_path)
    create_nodes(root_node, recipe_data["data"]["children"])

    print(f"Nodes imported successfully at {current_path}!")
