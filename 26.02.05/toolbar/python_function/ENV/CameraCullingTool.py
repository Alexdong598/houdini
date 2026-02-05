from PySide2 import QtWidgets
import os
import hou

class CameraCullingTool(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(CameraCullingTool, self).__init__(parent)

        self.setWindowTitle("Quick Instance Scatter")
        self.resize(300, 50)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        mainLayout = QtWidgets.QVBoxLayout(central_widget)

        self.camera_culling_movement_HDAimport_Label = QtWidgets.QLabel("Delete The Mesh Outside the Camera Frustum")
        mainLayout.addWidget(self.camera_culling_movement_HDAimport_Label)
        self.camera_culling_movement_HDAimport_PushButton = QtWidgets.QPushButton("Camera Culling Movement HDA")
        mainLayout.addWidget(self.camera_culling_movement_HDAimport_PushButton)
        self.camera_culling_movement_HDAimport_PushButton.clicked.connect(self.camera_culling_movement_HDAimport)

        self.camera_culling_distance_HDAimport_Label = QtWidgets.QLabel("Separate Meshes From Camera Distance")
        mainLayout.addWidget(self.camera_culling_distance_HDAimport_Label)
        self.camera_culling_distance_HDAimport_PushButton = QtWidgets.QPushButton("Camera Culling Distance HDA")
        mainLayout.addWidget(self.camera_culling_distance_HDAimport_PushButton)
        self.camera_culling_distance_HDAimport_PushButton.clicked.connect(self.camera_culling_distance_HDAimport)



    def camera_culling_movement_HDAimport(self):
        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "sop_yu.dong.dev.Terrain_maskbycamera.1.0.hda"
        HDA = os.path.join(path, HDAname)

        pane_tabs = hou.ui.paneTabs()

        for pane in pane_tabs:
            if isinstance(pane, hou.NetworkEditor):
                current_path = pane.pwd().path()
                current_node = hou.node(current_path)

                if current_node and current_node.type().name() == "geo":
                    hou.hda.installFile(HDA)
                    hda_type_name = hou.hda.definitionsInFile(HDA)[0].nodeType().name()
                    hda_node = current_node.createNode(hda_type_name)
                    current_node.setPosition((0, 0))
                    break

    def camera_culling_distance_HDAimport(self):
        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "yu_dong_camera_cullplane_from_distance.hda"
        HDA = os.path.join(path, HDAname)

        pane_tabs = hou.ui.paneTabs()

        for pane in pane_tabs:
            if isinstance(pane, hou.NetworkEditor):
                current_path = pane.pwd().path()
                current_node = hou.node(current_path)

                if current_node and current_node.type().name() == "geo":
                    hou.hda.installFile(HDA)
                    hda_type_name = hou.hda.definitionsInFile(HDA)[0].nodeType().name()
                    hda_node = current_node.createNode(hda_type_name)
                    current_node.setPosition((0, 0))
                    break




# CameraCullingTool = CameraCullingTool(hou.ui.mainQtWindow())
# CameraCullingTool.show()