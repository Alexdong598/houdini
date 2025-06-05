import hou

def create_sphere():
    # Get the obj network
    obj_network = hou.node("/obj")
    
    # Create a geo node
    geo = obj_network.createNode("geo")
    geo.setName("dy_sphere_geo", unique_name=True)
    geo.setPosition([0, 0])
    
    # Create a sphere inside the geo node
    sphere = geo.createNode("sphere")
    sphere.setName("dy_sphere", unique_name=True)
    sphere.setPosition([0, 0])
    
    # Layout the networks
    geo.layoutChildren()
    obj_network.layoutChildren()

create_sphere()
