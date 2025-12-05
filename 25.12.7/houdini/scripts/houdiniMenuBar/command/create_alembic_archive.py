import hou

def create_alembic_archive():
    # Get the obj network
    obj_network = hou.node("/obj")
    
    # Create an alembic archive node
    alembic = obj_network.createNode("alembicarchive")
    alembic.setName("dy_alembic", unique_name=True)
    alembic.setPosition([0, 0])
    
    # Layout the network
    obj_network.layoutChildren()

create_alembic_archive()
