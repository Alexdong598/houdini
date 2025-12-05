import shotgun_api3
import hou, re, os, sys, json

if sys.version_info.major < 3:
    from urllib import unquote
else:
    from urllib.parse import unquote


def GetSGFrames():
    sg = shotgun_api3.Shotgun(base_url="https://aivfx.shotgrid.autodesk.com",
            script_name="hal_roxy_templates_rw",
            api_key="cstmibkrtcwqmaz4sjwtexG~s")

    PROJECT_SGID = int(os.environ.get('HAL_PROJECT_SGID'))
    if os.environ.get('HAL_SHOT_SGID') is not None:
        SHOTID = int(os.environ.get('HAL_SHOT_SGID'))
        if SHOTID is None:
            pass
        else:
            data_store = {}
                
            def getSGData(entity_type, entity_id, fields=None):
                # Create unique cache key
                cache_key = f"{entity_type}_{entity_id}"
                
                # Fetch data if not cached
                if cache_key not in data_store:
                    # Default fields if not specified
                    if fields is None:
                        fields = ["code", "sg_cut_in", "sg_cut_out", "sg_head_in", "sg_head_out", "sg_tail_out"]
                    
                    # Fetch data from Shotgun
                    entity_data = sg.find_one(
                        entity_type,
                        [["id", "is", entity_id]],
                        fields=fields
                    )
                    
                    # Store in cache
                    data_store[cache_key] = entity_data or {}
                
                return data_store[cache_key], PROJECT_SGID, SHOTID
                


            shot_data = getSGData("Shot", SHOTID)[0]
            cut_in = shot_data.get('sg_cut_in')
            cut_out = shot_data.get('sg_cut_out')
            head_in = shot_data.get('sg_head_in')
            tail_out = shot_data.get('sg_tail_out')

            return cut_in,cut_out,head_in,tail_out

    
frames = GetSGFrames()

if frames and len(frames) > 0 and frames[0] is not None:
    hou.putenv("HAL_FRAME_START", str(frames[0]))
    
if frames and len(frames) > 1 and frames[1] is not None:
    hou.putenv("HAL_FRAME_END", str(frames[1]))
    
if frames and len(frames) > 2 and frames[2] is not None:
    hou.putenv("HAL_HEAD_IN", str(frames[2]))
    
if frames and len(frames) > 3 and frames[3] is not None:
    hou.putenv("HAL_TAIL_OUT", str(frames[3]))



class ShotgunDataManager:
    def __init__(self):
        self.sg = shotgun_api3.Shotgun(base_url="https://aivfx.shotgrid.autodesk.com",
                          script_name="hal_roxy_templates_rw",
                          api_key="cstmibkrtcwqmaz4sjwtexG~s")

        self.HAL_PROJECT_SGID = os.environ.get('HAL_PROJECT_SGID')
        self.HAL_PROJECT = os.environ.get('HAL_PROJECT')
        self.HAL_PROJECT_ABBR = os.environ.get('HAL_PROJECT_ABBR')
        self.HAL_PROJECT_ROOT = os.environ.get('HAL_PROJECT_ROOT')

        self.HAL_AREA = os.environ.get('HAL_AREA')
        self.HAL_USER_ABBR = os.environ.get('HAL_USER_ABBR')
        self.HAL_USER_LOGIN = os.environ.get('HAL_USER_LOGIN')

        self.HAL_TREE = os.environ.get('HAL_TREE')
        if self.HAL_TREE == "shots":
            self.HAL_SEQUENCE = os.environ.get('HAL_SEQUENCE')
            self.HAL_SEQUENCE_SGID = os.environ.get('HAL_SEQUENCE_SGID')
            self.HAL_SEQUENCE_ROOT = os.environ.get('HAL_SEQUENCE_ROOT')

            self.HAL_SHOT = os.environ.get('HAL_SHOT')
            self.HAL_SHOT_SGID = os.environ.get('HAL_SHOT_SGID')
            self.HAL_SHOT_ROOT = os.environ.get('HAL_SHOT_ROOT')
            
        if self.HAL_TREE == "assets":
            self.HAL_CATEGORY = os.environ.get('HAL_CATEGORY')
            self.HAL_CATEGORY_ROOT = os.environ.get('HAL_CATEGORY_ROOT')

            self.HAL_ASSET = os.environ.get('HAL_ASSET')
            self.HAL_ASSET_SGID = os.environ.get('HAL_ASSET_SGID')
            self.HAL_ASSET_ROOT = os.environ.get('HAL_ASSET_ROOT')

        self.HAL_TASK = os.environ.get('HAL_TASK')
        self.HAL_TASK_TYPE = os.environ.get('HAL_TASK_TYPE')
        self.HAL_TASK_ROOT = os.environ.get('HAL_TASK_ROOT')
        self.HAL_TASK_SGID = os.environ.get('HAL_TASK_SGID')
        self.HAL_TASK_OUTPUT_ROOT = os.environ.get('HAL_TASK_OUTPUT_ROOT') 
        self.HAL_TASK_ROOT = os.environ.get('HAL_TASK_ROOT') 

        self.data_store = {} 

    def _get_project_context_filter(self):
        project_id = self.HAL_PROJECT_SGID
        if not project_id:
            print("Error: HAL_PROJECT_SGID is not set. Cannot establish project context.")
            return None
        try:
            project_id = int(project_id) # 确保是整数
        except ValueError:
            print(f"Error: Invalid HAL_PROJECT_SGID value '{project_id}'. Must be an integer.")
            return None
            
        return ['project', 'is', {'type': 'Project', 'id': project_id}]

    def SG_Find_Sequence(self):

        project_filter = self._get_project_context_filter()
        if not project_filter:
            return []

        # print(f"Fetching sequences for Project ID: {self.HAL_PROJECT_SGID} (Name: {self.HAL_PROJECT})...")

        sequence_fields = [
            'id',
            'code',
            'sg_status_list',
            'description'
        ]
        
        found_sequences = []
        try:
            all_sequences = self.sg.find("Sequence", [project_filter], sequence_fields)
            # print(f"\nFound {len(all_sequences)} sequences in Project '{self.HAL_PROJECT}':")
            for seq in all_sequences:
                seq_id = seq['id']
                seq_code = seq['code']
                seq_status = seq.get('sg_status_list', 'N/A')
                seq_description = seq.get('description', '')
                found_sequences.append({
                    'id': seq_id,
                    'code': seq_code,
                    'status': seq_status,
                    'description': seq_description
                })
                # print(f"  - Sequence: {seq_code} (ID: {seq_id}, Status: {seq_status})")

        except Exception as e:
            print(f"Error fetching sequences: {e}")
        
        # 将查询结果存储在 self.data_store 中（可选）
        self.data_store['sequences'] = found_sequences
        
        return found_sequences

    def SG_Find_Shot(self, sequence_id=None):
        """
        查找当前项目下，特定序列（如果提供了 sequence_id）或所有序列下的所有镜头。
        
        Args:
            sequence_id (int, optional): 要查找镜头的序列ID。如果为 None，则查找项目下所有镜头。
        """
        project_filter = self._get_project_context_filter()
        if not project_filter:
            return []
        
        filters = [project_filter]

        if sequence_id:
            try:
                sequence_id = int(sequence_id)
            except ValueError:
                print(f"Error: Invalid sequence_id value '{sequence_id}'. Must be an integer.")
                return []
            
            sequence_filter = ['sg_sequence', 'is', {'type': 'Sequence', 'id': sequence_id}]
            filters.append(sequence_filter)

        shot_fields = [
            'id',
            'code',
            'sg_status_list',   
            'description',
            'sg_sequence',
            'sg_sequence.Sequence.code'
        ]

        found_shots = []
        try:
            all_shots = self.sg.find("Shot", filters, shot_fields)

            for shot in all_shots:
                shot_id = shot['id']
                shot_code = shot['code']
                shot_status = shot.get('sg_status_list', 'N/A')
                shot_description = shot.get('description', '')
                
                sequence_info_link = shot.get('sg_sequence')
                sequence_linked_id = sequence_info_link['id'] if sequence_info_link else None
                sequence_linked_code = shot.get('sg_sequence.Sequence.code', 'No Sequence')

                found_shots.append({
                    'id': shot_id,
                    'code': shot_code,
                    'status': shot_status,
                    'description': shot_description,
                    'sequence': {
                        'id': sequence_linked_id,
                        'code': sequence_linked_code
                    }
                })

        except Exception as e:
            print(f"Error fetching shots: {e}")
        
        if sequence_id:
            if 'shots_by_sequence' not in self.data_store:
                self.data_store['shots_by_sequence'] = {}
            self.data_store['shots_by_sequence'][sequence_id] = found_shots
        else:
            self.data_store['all_project_shots'] = found_shots
        
        return found_shots

    # def Store_Env_Variables(self):
    #     all_sequences = self.SG_Find_Sequence()
    #     all_shots = self.SG_Find_Shot()

    #     os.en

manager = ShotgunDataManager()
all_sequences = manager.SG_Find_Sequence()
all_shots = manager.SG_Find_Shot()
os.environ['SG_Find_Sequence'] = str(all_sequences)   
os.environ['SG_Find_Shot'] = str(all_shots)   




def dropAccept(files):
    """
    This function is now a smart handler that can process drops from
    the Shotgun Library tool OR standard texture file drops.
    """
    pane = hou.ui.paneTabUnderCursor()
    if not pane:
        return False
        
    # --- Handler for Shotgun Library Tool ---
    # First, check if the drop contains our custom data
    try:
        # We use a special global variable that the UI script will set during the drag
        if hasattr(hou.session, 'shotgun_library_drop_data'):
            print("Shotgun Library drop detected.")
            data = hou.session.shotgun_library_drop_data
            
            # Delete the global variable to clean up
            del hou.session.shotgun_library_drop_data
            
            # Execute the node creation logic
            create_node_from_sg_data(pane, data)
            
            # Signal that we have handled the drop
            return True
    except Exception as e:
        print(f"Error processing Shotgun Library drop: {e}")
        traceback.print_exc()
        if hasattr(hou.session, 'shotgun_library_drop_data'):
            del hou.session.shotgun_library_drop_data

    # --- Fallback to your Original Texture Importer Logic ---
    # If it wasn't a Shotgun drop, run the texture logic
    if pane.type().name() != "NetworkEditor":
        return False

    network_node = pane.pwd()
    net_type_name = network_node.type().name()
    
    if net_type_name == "subnet":
        parent = network_node.parent()
        while parent.type().name() == "subnet":
            parent = parent.parent()
        net_type_name = parent.type().name()

    inMatNet = net_type_name in ("mat", "matnet", "materiallibrary")
    allFileIsTex = True
    for file_uri in files:
        file_path = unquote(file_uri)
        file_ext = os.path.splitext(os.path.basename(file_path))[1].lower()
        if file_ext not in [".png",".jpg",".jpeg",".tiff",".tif",".exr",".tga",".psd",".bmp"]:
            allFileIsTex = False
            print(f"Info: Drop includes non-image file, skipping texture import logic: {file_path}")
            break
            
    if allFileIsTex and inMatNet:
        print("Handling drop as a texture import.")
        create_material_from_textures(pane, files)
        return True # Signal that we handled the drop

    # If neither handler caught it, let Houdini do its default action
    return False

def create_node_from_sg_data(pane, data):
    """
    This function contains the node creation logic for the Shotgun Library.
    """
    try:
        pwd = pane.pwd()
        node_name = data.get('version_name')
        file_path = data.get('file_path')
        file_format = data.get('format')
        usd_import_method = data.get('houdini_usd_import_method')
        node = None
        context_type = pwd.type().name()

        if context_type in ('stage', 'lopnet'):
            if file_format in ('usdc', 'usda'):
                node = pwd.createNode(usd_import_method, node_name); node.parm("filepath1").set(file_path); node.setDisplayFlag(True)
            elif file_format == 'abc':
                node = pwd.createNode('sopcreate', node_name); alembic_sop = node.node('sopnet/create').createNode('alembic', 'import'); alembic_sop.parm('fileName').set(file_path); alembic_sop.setDisplayFlag(True); node.setDisplayFlag(True)
            elif file_format == 'bgeo.sc':
                node = pwd.createNode('sopcreate', node_name); filecache_sop = node.node('sopnet/create').createNode('filecache::2.0', 'import'); filecache_sop.parm('loadfromdisk').set(1); filecache_sop.parm('filemethod').set('explicit'); filecache_sop.parm('file').set(file_path); filecache_sop.setDisplayFlag(True); node.setDisplayFlag(True)
        elif context_type in ('geo', 'sopnet'):
            if file_format in ('usdc', 'usda'):
                node = pwd.createNode('usdimport', node_name); node.parm('filepath1').set(file_path); node.parm('purpose').set(2); node.setDisplayFlag(True)
            elif file_format == 'abc':
                node = pwd.createNode('alembic', node_name); node.parm('fileName').set(file_path); node.setDisplayFlag(True)
            elif file_format == 'bgeo.sc':
                node = pwd.createNode('filecache::2.0', node_name); node.parm('loadfromdisk').set(1); node.parm('filemethod').set('explicit'); node.parm('file').set(file_path); node.setDisplayFlag(True)
        
        if node:
            node.moveToGoodPosition()
            print(f"SUCCESS: Created node at {node.path()}")
        else:
            hou.ui.displayMessage(f"Unsupported drop context '{context_type}' or format '{file_format}'.", severity=hou.severityType.Warning)
    except Exception as e:
        hou.ui.displayMessage(f"Failed to create node: {e}", severity=hou.severityType.Error)
        traceback.print_exc()


def create_material_from_textures(pane, files):
    """
    This is your original texture importer logic, now as a separate function.
    """
    # This is a simplified version of your texture script for demonstration
    print("Creating material from textures...")
    network_node = pane.pwd()
    # In a real scenario, you would paste your full texture creation logic here.
    # For now, we just create a placeholder.
    mat_builder = network_node.createNode("mtlxsubnet", "texture_material")
    mat_builder.moveToGoodPosition()
    hou.ui.displayMessage(f"Created material for {len(files)} textures.")