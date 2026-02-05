import hou
import toolutils
import importlib
import sys, os, re
import shotgun_api3
from PySide2 import QtWidgets, QtCore, QtGui
# from .SGlogin import ShotgunDataManager

# 全局窗口实例，防止被垃圾回收
playblast_window = None


class SimplePlayblastUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SimplePlayblastUI, self).__init__(parent)
        self.sg = shotgun_api3.Shotgun(base_url="https://aivfx.shotgrid.autodesk.com",
                script_name="hal_roxy_templates_rw",
                api_key="cstmibkrtcwqmaz4sjwtexG~s")
        self.PROJECT_SGID = int(os.environ.get('HAL_PROJECT_SGID'))
        self.SHOTID = int(os.environ.get('HAL_SHOT_SGID'))
        self.data_store = {}


        self.setWindowTitle("FX Playblast")
        self.setMinimumWidth(700)
        self.init_ui()


    def get_current_version(self):
        """Get next available version number for playblast files"""
        HAL_TASK_OUTPUT_ROOT = os.environ.get("HAL_TASK_OUTPUT_ROOT", "")
        playblast_dir = os.path.join(HAL_TASK_OUTPUT_ROOT, "playblast")
        
        if not os.path.exists(playblast_dir):
            return "v001"

        version_dirs = [d for d in os.listdir(playblast_dir) 
                      if os.path.isdir(os.path.join(playblast_dir, d))]
        
        version_pattern = re.compile(r'^v(\d{3,})$', re.IGNORECASE)
        max_version = 0

        for version_dir in version_dirs:
            match = version_pattern.match(version_dir)
            if match:
                version_num = int(match.group(1))
                if version_num > max_version:
                    max_version = version_num

        # Return next version number (current max + 1)
        return f"v{(max_version + 1):03d}"

    def get_playblast_path(self, version):
        HAL_TASK_OUTPUT_ROOT = os.environ.get("HAL_TASK_OUTPUT_ROOT")
        if not HAL_TASK_OUTPUT_ROOT:
            QtWidgets.QMessageBox.warning(self, "Error", "HAL_TASK_OUTPUT_ROOT environment variable not set")
            return
            
        HAL_PROJECT_ABBR = os.environ.get("HAL_PROJECT_ABBR", "")
        HAL_SEQUENCE = os.environ.get("HAL_SEQUENCE", "")
        HAL_SHOT = os.environ.get("HAL_SHOT", "")
        HAL_TASK = os.environ.get("HAL_TASK", "")
        HAL_USER_ABBR = os.environ.get("HAL_USER_ABBR", "")
        
        # Create output path
        version = self.get_current_version()
        file_name = f"{HAL_PROJECT_ABBR}_{HAL_SEQUENCE}_{HAL_SHOT}_{HAL_TASK}_{version}_{HAL_USER_ABBR}"
        output_dir = os.path.join(HAL_TASK_OUTPUT_ROOT, "playblast", version)
        output_path = os.path.join(output_dir, file_name).replace(os.sep, "/")
        return output_path

    def init_ui(self):
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # 相机选择区域
        cam_layout = QtWidgets.QHBoxLayout()
        self.cam_path = QtWidgets.QLineEdit()
        self.cam_path.setPlaceholderText("选择相机节点")
        self.cam_path.setReadOnly(False)
        cam_layout.addWidget(self.cam_path)
        
        self.select_cam_btn = QtWidgets.QPushButton("选择相机")
        self.select_cam_btn.clicked.connect(self.select_camera)
        cam_layout.addWidget(self.select_cam_btn)
        main_layout.addLayout(cam_layout)
        
        # 帧范围区域
        frame_layout = QtWidgets.QHBoxLayout()
        frame_layout.addWidget(QtWidgets.QLabel("起始帧:"))
        self.start_frame = QtWidgets.QLineEdit("1")
        self.start_frame.setFixedWidth(60)
        frame_layout.addWidget(self.start_frame)
        
        frame_layout.addWidget(QtWidgets.QLabel("结束帧:"))
        self.end_frame = QtWidgets.QLineEdit("100")
        self.end_frame.setFixedWidth(60)
        frame_layout.addWidget(self.end_frame)
        main_layout.addLayout(frame_layout)
        
        # 


        # Export path section
        export_layout = QtWidgets.QHBoxLayout()
        export_layout.addWidget(QtWidgets.QLabel("导出路径:"))
        path = f"{self.get_playblast_path(self.get_current_version())}.$F.jpg"
        self.export_path = QtWidgets.QLineEdit(path)
        # self.export_path = QtWidgets.QLineEdit(self.get_current_version()[0])
        export_layout.addWidget(self.export_path)
        main_layout.addLayout(export_layout)
        
        # Load Shotgun data after UI is initialized
        QtCore.QTimer.singleShot(0, self.load_shotgun_data)
        
        # 按钮区域
        btn_layout = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton("执行Playblast")
        self.run_btn.clicked.connect(self.run_playblast)
        btn_layout.addWidget(self.run_btn)
        
        self.cancel_btn = QtWidgets.QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

    def getSGData(self, entity_type, entity_id, fields=None):
    # Store and retrieve Shotgun entity data in a dictionary cache
    # Add Var
    
        # Create unique cache key
        cache_key = f"{entity_type}_{entity_id}"
        
        # Fetch data if not cached
        if cache_key not in self.data_store:
            # Default fields if not specified
            if fields is None:
                fields = ["code", "sg_cut_in", "sg_cut_out", "sg_head_in", "sg_head_out"]
            
            # Fetch data from Shotgun
            entity_data = self.sg.find_one(
                entity_type,
                [["id", "is", entity_id]],
                fields=fields
            )
            
            # Store in cache
            self.data_store[cache_key] = entity_data or {}
        
        return self.data_store[cache_key], self.PROJECT_SGID, self.SHOTID
        
    def load_shotgun_data(self):
        """Load frame range from Shotgun after UI is initialized"""
        try:
            shot_data = self.getSGData("Shot", self.SHOTID)[0]
            cut_in = shot_data.get('sg_cut_in', '1')
            cut_out = shot_data.get('sg_cut_out', '100')
            self.start_frame.setText(str(cut_in))
            self.end_frame.setText(str(cut_out))
        except Exception as e:
            print(f"Failed to load Shotgun data: {str(e)}")
            self.start_frame.setText("1")
            self.end_frame.setText("100")


    def select_camera(self):
        """打开节点选择对话框选择相机"""
        try:
            Sop = hou.nodeTypeFilter.Sop
        except AttributeError:
            Sop = None
            
        selection = hou.ui.selectNode(title="选择相机节点", node_type_filter=Sop)
        if selection:
            # Handle both string path and node object return types
            if isinstance(selection, str):
                path = selection
            else:
                path = selection.path()
            
            if path and hou.node(path):  # Verify node exists
                self.cam_path.setText(path)
                self.cam_path.repaint()  # Force UI update
                print(f"Selected camera path: {path}")  # Debug output
            else:
                hou.ui.displayMessage("无效的相机节点", severity=hou.severityType.Error)
    
    def run_playblast(self):
        """执行Playblast操作"""
        # 验证输入
        cam_path = self.cam_path.text()
        if not cam_path:
            hou.ui.displayMessage("请先选择相机节点", severity=hou.severityType.Error)
            return
            
        try:
            start = int(self.start_frame.text())
            end = int(self.end_frame.text())
        except:
            hou.ui.displayMessage("帧范围必须为整数", severity=hou.severityType.Error)
            return
            
        if start > end:
            hou.ui.displayMessage("起始帧不能大于结束帧", severity=hou.severityType.Error)
            return
            
        # 执行Playblast
        try:
            viewer = toolutils.sceneViewer()
            if not viewer:
                hou.ui.displayMessage("无法获取场景查看器", severity=hou.severityType.Error)
                return
                
            viewport = viewer.curViewport()
            if not viewport:
                hou.ui.displayMessage("无法获取视图端口", severity=hou.severityType.Error)
                return
                
            # 设置相机
            cam_node = hou.node(cam_path)
            viewport.setCamera(cam_node)
            
            # 配置翻页设置
            settings = viewer.flipbookSettings()
            settings.frameRange((start, end))  # Correct method name
            settings.output(self.export_path.text())
            settings.resolution((1280, 720)) 
            
            # 执行Playblast
            viewer.flipbook(viewport, settings)
            # hou.ui.displayMessage(f"已启动Playblast: {start}~{end}帧", severity=hou.severityType.Message)
            
            # Update version after successful playblast
            self.update_export_path()
            
        except Exception as e:
            hou.ui.displayMessage(f"执行Playblast时出错: {str(e)}", severity=hou.severityType.Error)

    def update_export_path(self):
        """Update export path with new version number"""
        path = f"{self.get_playblast_path(self.get_current_version())}.$F.jpg"
        self.export_path.setText(path)

def show_playblast_ui():
    """显示Playblast界面"""
    global playblast_window
    if playblast_window and playblast_window.isVisible():
        playblast_window.raise_()
        return
        
    parent = hou.qt.mainWindow()
    playblast_window = SimplePlayblastUI(parent)
    playblast_window.show()

def get_command():
    def _command():
        importlib.reload(sys.modules[__name__])
        show_playblast_ui()
    return _command

def execute():
    importlib.reload(sys.modules[__name__])
    cmd = get_command()
    cmd()

execute()
