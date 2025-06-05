import hou

def create_cube():
    # Get the obj network
    obj_network = hou.node("/obj")
    
    # Create a geo node
    geo = obj_network.createNode("geo")
    geo.setName("dy_cube_geo", unique_name=True)
    geo.setPosition([0, 0])
    
    # Create a cube inside the geo node
    cube = geo.createNode("box")
    cube.setName("dy_cube", unique_name=True)
    cube.setPosition([0, 0])
    
    # Layout the networks
    geo.layoutChildren()
    obj_network.layoutChildren()

create_cube()
