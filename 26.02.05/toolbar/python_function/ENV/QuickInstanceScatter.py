from PySide2 import QtWidgets
import os
import hou

class QuickInstanceScatter(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(QuickInstanceScatter, self).__init__(parent)

        self.setWindowTitle("Quick Instance Scatter")
        self.resize(300, 400)

        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        mainLayout = QtWidgets.QVBoxLayout(central_widget)

        self.advanced_scatter_HDAimport_Label = QtWidgets.QLabel("HDA Scatter points through the HF mask")
        mainLayout.addWidget(self.advanced_scatter_HDAimport_Label)
        self.advanced_scatter_HDAimport_PushButton = QtWidgets.QPushButton("Advanced Scatter HDA")
        mainLayout.addWidget(self.advanced_scatter_HDAimport_PushButton)
        self.advanced_scatter_HDAimport_PushButton.clicked.connect(self.advanced_scatter_HDAimport)

        self.randomized_scatter_point_HDAimport_Label = QtWidgets.QLabel("HDA Randomly assign points region")
        mainLayout.addWidget(self.randomized_scatter_point_HDAimport_Label)
        self.randomized_scatter_point_HDAimport_PushButton = QtWidgets.QPushButton("Randomized Scatter Points HDA")
        mainLayout.addWidget(self.randomized_scatter_point_HDAimport_PushButton)
        self.randomized_scatter_point_HDAimport_PushButton.clicked.connect(self.randomized_scatter_point_HDAimport)

        self.random_scale_HDAimport_Label = QtWidgets.QLabel("HDA Randomly control the size of points")
        mainLayout.addWidget(self.random_scale_HDAimport_Label)
        self.random_scale_HDAimport_PushButton = QtWidgets.QPushButton("Random Scale HDA")
        mainLayout.addWidget(self.random_scale_HDAimport_PushButton)
        self.random_scale_HDAimport_PushButton.clicked.connect(self.random_scale_HDAimport)

        self.one_click_nameAttrib_Label = QtWidgets.QLabel("Tag the name variant to the instance by one click")
        mainLayout.addWidget(self.one_click_nameAttrib_Label)
        self.one_click_nameAttrib_PushButton = QtWidgets.QPushButton("One Click Name Attribute")
        mainLayout.addWidget(self.one_click_nameAttrib_PushButton)
        self.one_click_nameAttrib_PushButton.clicked.connect(self.one_click_nameAttrib)

        self.multiCopyToPoint_HDAimport_Label = QtWidgets.QLabel("HDA Variant instance copy to point by name")
        mainLayout.addWidget(self.multiCopyToPoint_HDAimport_Label)
        self.multiCopyToPoint_HDAimport_PushButton = QtWidgets.QPushButton("Multi Copy To Point HDA")
        mainLayout.addWidget(self.multiCopyToPoint_HDAimport_PushButton)
        self.multiCopyToPoint_HDAimport_PushButton.clicked.connect(self.multiCopyToPoint_HDAimport)

    def advanced_scatter_HDAimport(self):
        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "sop_DY.dev.DY_Advanced_Scatter.1.0.hda"
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

    def randomized_scatter_point_HDAimport(self):
        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "sop_DY.dev.DY_Randomized_Scatter_Points.1.0.hda"
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

    def random_scale_HDAimport(self):
        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "wenzhong_chen_Random_Scale.1.0.hda"
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

    def one_click_nameAttrib(self):

        selectedNodes = hou.selectedNodes()
        created_nodes = []

        for node in selectedNodes:
            parent = node.parent()
            nameNode = parent.createNode("name")

            nameNode.setInput(0, node)
            currentPosition = node.position()
            nameNode.setPosition(currentPosition + hou.Vector2(0, -1.0))

            nameParm = nameNode.parm("name1")
            if nameParm is not None:
                nameParm.set("piece" + str(node.name()))

            created_nodes.append(nameNode)

        mergeNode = parent.createNode("merge")
        for index, created_node in enumerate(created_nodes):
            mergeNode.setInput(index, created_node)

        mid_node_num = int(round((len(created_nodes) - 1) * 0.5))
        mid_node = created_nodes[mid_node_num]
        mid_nodePos = mid_node.position()
        mergeNode.setPosition(mid_nodePos + hou.Vector2(0, -2.0))

    def multiCopyToPoint_HDAimport(self):

        path = "U:/_hal/houdini_branch_tools/afx/otls"
        HDAname = "sop_yu.dong.dev.multiCopyToPoints.1.0.hda"
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

                    hda_node.setPosition((0, 0))
                    break

# quick_instance_scatter = QuickInstanceScatter(hou.ui.mainQtWindow())
# quick_instance_scatter.show()