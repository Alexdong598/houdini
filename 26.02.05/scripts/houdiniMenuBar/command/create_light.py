import hou

def create_light():
    # Get the obj network
    obj_network = hou.node("/obj")
    
    # Create a light node
    light = obj_network.createNode("light")
    light.setName("dy_light", unique_name=True)
    light.setPosition([0, 0])
    
    # Layout the network
    obj_network.layoutChildren()

create_light()
