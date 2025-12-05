import hou
import re

def Scatter_LOP():
    selected_nodes = hou.selectedNodes()

    expected_index = 1
    base = None

    if len(selected_nodes) == 1:
        node = selected_nodes[0]
        if node.type().name() == "subnet":
            subnet = node
            geo_nodes = []
            for child in subnet.children():
                if child.type().name() == "geo":
                    geo_nodes.append(child)
            selected_nodes = geo_nodes
            base = subnet.name()
            expected_index = len(geo_nodes) + 1

    if base is None:
        if not selected_nodes:
            hou.ui.displayMessage("No nodes selected. Please select nodes to proceed.")
            return

        if len(selected_nodes) == 1:
            base = selected_nodes[0].name()
        else:
            node_indices = []
            base_names = []
            for node in selected_nodes:
                node_name = node.name()
                match = re.match(r'^([A-Za-z]+)(\d+)$', node_name)
                if not match:
                    hou.ui.displayMessage(f"Invalid node name: {node_name}. Expected format: baseName + index (e.g., geo1, geo2)")
                    return
                current_base = match.group(1)
                current_index = int(match.group(2))
                node_indices.append((node, current_index))
                base_names.append(current_base)

            if len(set(base_names)) != 1:
                hou.ui.displayMessage("All selected nodes must have the same base name.")
                return
            base = base_names[0]

            sorted_nodes = sorted(node_indices, key=lambda x: x[1])
            expected_index = sorted_nodes[0][1]

            for node, index in sorted_nodes:
                if index != expected_index:
                    hou.ui.displayMessage(f"Missing node: Expected {base}{expected_index}, got {base}{index}")
                    return
                expected_index += 1

    stage = hou.node("/stage")
    if not stage:
        raise RuntimeError("The /stage context does not exist.")

    selectedLOPNodes = []
    componentgeometry = stage.createNode("componentgeometry", base)
    selectedLOPNodes.append(componentgeometry)
    
    componentgeometryvariants = stage.createNode("componentgeometryvariants", f"{base}_component")
    componentgeometryvariants.setInput(0, componentgeometry)
    selectedLOPNodes.append(componentgeometryvariants)
    componentgeometryvariants.parm("variantsource").set(1)

    variant_count = expected_index - 1 if base != selected_nodes[0].name() else len(selected_nodes)
    componentgeometryvariants.parm("variantcount").set(variant_count)

    explorevariants = stage.createNode("explorevariants", f"{base}_variants")
    explorevariants.setInput(0, componentgeometryvariants)
    selectedLOPNodes.append(explorevariants)

    instancer = stage.createNode("instancer", f"{base}_instancer")
    instancer.setInput(0, explorevariants)
    selectedLOPNodes.append(instancer)
    instancer.parm("protopattern").set(f"/{explorevariants.name()}/ASSET/*")
    instancer.parm("protosourcemode").set('first')
    instancer.setDisplayFlag(True)

    selectedLOPNodes[0].parent().layoutChildren(items=selectedLOPNodes)

    geo_path = f"{componentgeometry.path()}/sopnet/geo"
    geo = hou.node(geo_path)
    if not geo:
        raise RuntimeError(f"Cannot find 'sopnet/geo' inside {componentgeometry.path()}.")

    object_merge = geo.createNode("object_merge", "object_merge")
    if base is not None:
        object_merge.parm("objpath1").set(f"/obj/ASSETS/{base}/Var`@GEOVARIANTINDEX+1`/output0")
    else:
        object_merge.parm("objpath1").set(f"/obj/ASSETS/{base}`@GEOVARIANTINDEX+1`/output0")
    object_merge.parm("xformtype").set("local")

    default_node = geo.node("default")
    if default_node:
        default_node.setInput(0, object_merge)

    polyreduce = geo.createNode("polyreduce::2.0", "polyreduce")
    polyreduce.parm("percentage").set(20)
    polyreduce.setInput(0, object_merge)

    shrinkwrap = geo.createNode("shrinkwrap::2.0", "shrinkwrap")
    shrinkwrap.setInput(0, object_merge)

    proxy_node = geo.node("proxy")
    if proxy_node:
        proxy_node.setInput(0, polyreduce)

    simproxy_node = geo.node("simproxy")
    if simproxy_node:
        simproxy_node.setInput(0, shrinkwrap)

    geo.layoutChildren()