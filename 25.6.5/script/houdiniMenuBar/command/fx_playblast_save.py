import hou
import toolutils


#Get Camera
cam = hou.node("/obj/cam1")  # 替换为你的相机名称


scene_viewer = toolutils.sceneViewer()# 获取当前场景视图
curViewport = scene_viewer.curViewport()
curViewport.setCamera(cam)
# scene_viewer.setCamera(camera_node)
settings = scene_viewer.flipbookSettings().stash()  # 正确获取设置副本[10](@ref)

# 配置参数
settings.frameRange((1001, 1060))
settings.output("$HIP/test/untitled.$F.jpg")
# settings.setOutputQuantization(100)  # JPEG质量
settings.resolution((1920, 1080))  # 直接设置分辨率

# 
scene_viewer.flipbook(scene_viewer.curViewport(), settings)

