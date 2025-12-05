import hou,os,sys,re,json
import JSONRead.JSON_read as JSON_read_M
from importlib import reload
reload(JSON_read_M)

def GaeaPros_SOP():
    JSON_read_F = JSON_read_M.readJSON
    path = r'U:\_hal\houdini_branch_tools\afx\houdini20.0\houdini\toolbar\JSONRead\JSON\GaeaPros_SOP.json'
    JSON_read_F(path)
