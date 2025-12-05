import shotgun_api3
import os
import re
import importlib
import sys


class ShotgunDataManager:
    def __init__(self):
        # --- 请确保在这里填入你自己的 Shotgun 服务器信息 ---
        self.sg = shotgun_api3.Shotgun(base_url="https://aivfx.shotgrid.autodesk.com",
                          script_name="hal_roxy_templates_rw",
                          api_key="cstmibkrtcwqmaz4sjwtexG~s")
        
        # 安全地处理环境变量
        self.HAL_PROJECT_SGID = os.environ.get('HAL_PROJECT_SGID')
        self.HAL_PROJECT = os.environ.get('HAL_PROJECT')
        self.HAL_PROJECT_ABBR = os.environ.get('HAL_PROJECT_ABBR')
        self.HAL_PROJECT_ROOT = os.environ.get('HAL_PROJECT_ROOT')

        self.HAL_AREA = os.environ.get('HAL_AREA')
        self.HAL_USER_ABBR = os.environ.get('HAL_USER_ABBR')
        self.HAL_USER_LOGIN = os.environ.get('HAL_USER_LOGIN')

        self.HAL_TREE = os.environ.get('HAL_TREE')
        if self.HAL_TREE == "shots":
            # 从 Sequence 到 Shot
            self.HAL_SEQUENCE = os.environ.get('HAL_SEQUENCE')
            self.HAL_SEQUENCE_SGID = os.environ.get('HAL_SEQUENCE_SGID')
            self.HAL_SEQUENCE_ROOT = os.environ.get('HAL_SEQUENCE_ROOT')

            self.HAL_SHOT = os.environ.get('HAL_SHOT')
            self.HAL_SHOT_SGID = os.environ.get('HAL_SHOT_SGID')
            self.HAL_SHOT_ROOT = os.environ.get('HAL_SHOT_ROOT')
            
        if self.HAL_TREE == "assets":
            # 从 Category 到 Asset (Category 没有配置 ShotgunID)
            self.HAL_CATEGORY = os.environ.get('HAL_CATEGORY')
            self.HAL_CATEGORY_ROOT = os.environ.get('HAL_CATEGORY_ROOT')

            self.HAL_ASSET = os.environ.get('HAL_ASSET')
            self.HAL_ASSET_SGID = os.environ.get('HAL_ASSET_SGID')
            self.HAL_ASSET_ROOT = os.environ.get('HAL_ASSET_ROOT')

        # 获取 Task 信息
        self.HAL_TASK = os.environ.get('HAL_TASK')
        self.HAL_TASK_TYPE = os.environ.get('HAL_TASK_TYPE')
        self.HAL_TASK_ROOT = os.environ.get('HAL_TASK_ROOT')
        self.HAL_TASK_SGID = os.environ.get('HAL_TASK_SGID')
        self.HAL_TASK_OUTPUT_ROOT = os.environ.get('HAL_TASK_OUTPUT_ROOT') # Y:/ 发布根目录
        self.HAL_TASK_ROOT = os.environ.get('HAL_TASK_ROOT') # X:/ 工程根目录

        self.data_store = {}
        self.task = None # 初始化 task 属性
        
    def getSGData(self, entity_type, entity_id, fields=None):
        """在字典缓存中存储和检索 Shotgun 实体数据"""
        cache_key = f"{entity_type}_{entity_id}"
        
        if cache_key not in self.data_store:
            if fields is None:
                fields = ["code", "sg_head_in", "sg_tail_out", "sg_cut_in", "sg_cut_out"]
            
            entity_data = self.sg.find_one(
                entity_type,
                [["id", "is", entity_id]],
                fields=fields
            )
            self.data_store[cache_key] = entity_data or {}
        
        return self.data_store[cache_key], self.HAL_PROJECT_SGID, self.HAL_SHOT_SGID

    def upload_file(self, entity_type, entity_id, path, field_name=None, display_name=None, tag_list=None):
        try:
            return self.sg.upload(
                entity_type, entity_id, path,
                field_name=field_name, display_name=display_name, tag_list=tag_list
            )
        except Exception as e:
            print(f"Failed to upload file: {e}")
            raise

    def upload_thumbnail(self, entity_type, entity_id, path, **kwargs):
        try:
            return self.sg.upload_thumbnail(
                entity_type, entity_id, path, **kwargs
            )
        except Exception as e:
            print(f"Failed to upload thumbnail: {e}")
            raise

    def upload_filmstrip_thumbnail(self, entity_type, entity_id, path, **kwargs):
        try:
            return self.sg.upload_filmstrip_thumbnail(
                entity_type, entity_id, path, **kwargs
            )
        except Exception as e:
            print(f"Failed to upload filmstrip thumbnail: {e}")
            raise

    def SG_Find_Version(self, custom_name_suffix=None):
        """查找现有版本并确定下一个版本的名称"""
        parent_entity_type = None
        parent_entity_id = None

        if self.HAL_TREE == "shots":
            self.HAL_CONTENT = f"{self.HAL_SEQUENCE}_{self.HAL_SHOT}_{self.HAL_TASK}"
        elif self.HAL_TREE == "assets":
            self.HAL_CONTENT = f"{self.HAL_ASSET}_{self.HAL_TASK}"
        else:
            raise ValueError("HAL_TREE must be 'shots' or 'assets'.")
        print(f"Using default content from environment: '{self.HAL_CONTENT}'")

        if self.HAL_TREE == "shots":
            parent_entity_type = 'Shot'
            parent_entity_id = int(self.HAL_SHOT_SGID)
        elif self.HAL_TREE == "assets":
            parent_entity_type = 'Asset'
            parent_entity_id = int(self.HAL_ASSET_SGID)
        else:
            raise ValueError("HAL_TREE must be 'shots' or 'assets'.")

        task_filters = [
            ['project', 'is', {'type': 'Project', 'id': int(self.HAL_PROJECT_SGID)}],
            ['entity', 'is', {'type': parent_entity_type, 'id': parent_entity_id}],
            ['content', 'is', self.HAL_CONTENT] 
        ]

        self.task = self.sg.find_one('Task', task_filters, fields=['id', 'content', 'entity'])
        
        if not self.task:
            raise ValueError(f"No Task found with content '{self.HAL_CONTENT}' for {parent_entity_type} ID {parent_entity_id} in Project ID {self.HAL_PROJECT_SGID}")

        print(f"Found Task: {self.task['content']} (ID: {self.task['id']}) linked to {self.task['entity']['type']} ID {self.task['entity']['id']}")
        
        version_filters = [
            ['project', 'is', {'type': 'Project', 'id': int(self.HAL_PROJECT_SGID)}],
            ['entity', 'is', {'type': parent_entity_type, 'id': parent_entity_id}], 
            ['sg_task', 'is', self.task] 
        ]
        
        all_versions = self.sg.find('Version', 
                                    version_filters, 
                                    fields=['code'],
                                    order=[{'field_name': 'created_at', 'direction': 'desc'}]
                                    )
        
        versionCodes = []
        version_numbers = []
        highestVersionCode = ""
        
        if all_versions:
            print(f"\nFound {len(all_versions)} Versions linked to Task '{self.task['content']}':")
            
            for version in all_versions:
                versionCodes.append(version['code'])
                version_str = version['code']
                version_match = re.search(r'_v(\d{3,})', version_str)
                if not version_match:
                    version_match = re.search(r'v(\d{3,})$', version_str)
                
                if version_match:
                    version_numbers.append(int(version_match.group(1)))
                else:
                    print(f"Warning: Could not parse version number from: {version_str}")

            if version_numbers:
                next_version = max(version_numbers) + 1
                base_name = f"{self.HAL_CONTENT}_v{next_version:03d}_{self.HAL_USER_ABBR}"
                highestVersionCode = base_name
            else:
                print("Warning: Found versions but couldn't parse version numbers. Defaulting to v001.")
                base_name = f"{self.HAL_CONTENT}_v001_{self.HAL_USER_ABBR}"
                highestVersionCode = base_name
        else:
            print(f"No Versions found linked to Task '{self.task['content']}' for {parent_entity_type} ID {parent_entity_id}.")
            base_name = f"{self.HAL_CONTENT}_v001_{self.HAL_USER_ABBR}"
            highestVersionCode = base_name
        
        if custom_name_suffix:
            highestVersionCode = f"{highestVersionCode}-{custom_name_suffix}"
            
        versionCodesNum = len(versionCodes)
        print(f"The new version name is:{highestVersionCode}")

        return versionCodes, highestVersionCode, versionCodesNum

    def Create_SG_Version(self, thumbnail_path, submit_path=None, first_frame=None, last_frame=None, custom_name_suffix=None):
        """
        创建 Shotgun Version，上传缩略图，并返回更新后的完整 Version 数据。
        
        :param thumbnail_path: (必须) 缩略图文件的路径。
        :param submit_path: (可选) 'sg_path_to_geometry' 字段的值。
        :param first_frame: (可选) 'sg_first_frame' 字段的值。
        :param last_frame: (可选) 'sg_last_frame' 字段的值。
        :param custom_name_suffix: (可选) 附加到版本名称末尾的自定义字符串。
        """
        version_info = self.SG_Find_Version(custom_name_suffix=custom_name_suffix)
        highestVersion = version_info[1]

        sg_name = self.HAL_PROJECT   

        data = {
            "project": {"type": "Project", "name": sg_name, "id": int(self.HAL_PROJECT_SGID)},
            "code": f"{highestVersion}",
            "sg_status_list": "ip",
            "sg_task": self.task,
            "sg_path_to_geometry": submit_path,
            "sg_first_frame": first_frame,
            "sg_last_frame": last_frame
        }
        
        if self.HAL_TREE == "assets":
            data["entity"] = {"type": "Asset", "id": int(self.HAL_ASSET_SGID)}
        elif self.HAL_TREE == "shots":
            data["entity"] = {"type": "Shot", "id": int(self.HAL_SHOT_SGID)}

        print(f"Creating Version '{highestVersion}'...")
        created_version = self.sg.create('Version', data)
        print(f"Successfully created Version ID: {created_version['id']}")
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            display_name = os.path.splitext(os.path.basename(thumbnail_path))[0]
            
            print(f"Uploading thumbnail '{thumbnail_path}' to Version ID {created_version['id']}...")
            try:
                self.upload_thumbnail(
                    entity_type="Version",
                    entity_id=created_version["id"],
                    path=thumbnail_path,
                    display_name=display_name
                )
                print("Thumbnail upload complete.")
            except Exception as e:
                print(f"ERROR: Failed to upload thumbnail: {e}")
        
        print(f"Fetching updated data for Version ID {created_version['id']}...")
        # 在获取数据时，也请求新添加的字段，以便在返回值中确认
        fields_to_fetch = ['code', 'id', 'image', 'sg_my_project_path']
        updated_version_data = self.sg.find_one(
            "Version", 
            [["id", "is", created_version["id"]]], 
            fields=fields_to_fetch
        )

        if not updated_version_data:
            print("Warning: Could not re-fetch version data after thumbnail upload. URL will be missing.")
            return created_version

        print("Successfully fetched updated data.")
        return updated_version_data

def get_command():
    """返回命令实现"""
    def _command():
        """创建新的 ShotgunDataManager 实例"""
        global sg_manager
        try:
            if 'sg_manager' in globals():
                print("Updating existing ShotgunDataManager instance")
            sg_manager = ShotgunDataManager()
            print("ShotgunDataManager successfully created")
            return sg_manager
        except Exception as e:
            print(f"Error creating ShotgunDataManager: {str(e)}")
            raise

    # 为了能在模块级别直接访问，先创建一个实例
    sg_manager = ShotgunDataManager()
    return _command

def execute():
    """执行命令"""
    cmd = get_command()
    cmd()

if __name__ == "__main__":
    execute()

# --- 如何使用 (How to Use) ---
#
# 1. 初始化你的 sg_manager (通常在你的工具或脚本开头完成)
#    import SGlogin
#    sg_manager = SGlogin.ShotgunDataManager()
#
# 2. 准备缩略图路径和你的自定义工程文件路径
#    thumbnail_path = "path/to/your/thumbnail.png"
#    project_file_path = "Y:/path/to/your/project/file.hipnc" # 你的自定义路径
#
# 3. 调用 Create_SG_Version 方法，并传入 my_project_path 参数
#
#    - 示例1：添加自定义工程文件路径
#      sg_manager.Create_SG_Version(
#          thumbnail_path=thumbnail_path,
#          my_project_path=project_file_path
#      )
#      # 这将在 Shotgun 中创建一个新的 Version, 并且 'sg_my_project_path' 字段会被设置为 project_file_path 的值
#
#    - 示例2：同时添加自定义后缀和工程文件路径
#      sg_manager.Create_SG_Version(
#          thumbnail_path=thumbnail_path,
#          custom_name_suffix="for_review",
#          my_project_path=project_file_path
#      )
#
#    - 示例3：不添加任何自定义字段 (和以前的用法一样)
#      sg_manager.Create_SG_Version(thumbnail_path=thumbnail_path)
#      # 这将创建一个标准的 Version，'sg_my_project_path' 字段为空