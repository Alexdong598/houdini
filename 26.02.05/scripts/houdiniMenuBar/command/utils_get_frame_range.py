import hou

def get_frame_range():
    HAL_FRAME_START = int(hou.getenv("HAL_FRAME_START"))
    HAL_FRAME_END = int(hou.getenv("HAL_FRAME_END"))
    HAL_HEAD_IN = int(hou.getenv("HAL_HEAD_IN"))
    HAL_TAIL_OUT = int(hou.getenv("HAL_TAIL_OUT"))

    hou.playbar.setFrameRange(HAL_HEAD_IN, HAL_TAIL_OUT)
    hou.playbar.setPlaybackRange(HAL_HEAD_IN, HAL_TAIL_OUT)

get_frame_range()