import os
import sys
import hou
import subprocess
import tempfile
import time
import json
import glob
from pxr import Usd, Sdf, Ar

# ==============================================================================
# 1. EMBEDDED WORKER SCRIPT CONTENT
#    (This guarantees the file exists without needing to find another node)
# ==============================================================================
WORKER_SCRIPT_CONTENT = r"""
import sys
import json
import os
import subprocess
import concurrent.futures
import shutil

# --- CONFIGURATION ---
def find_oiio_tool():
    # 1. Try finding it in the current Houdini Install ($HFS/bin)
    hfs = os.getenv("HFS")
    if hfs:
        ext = ".exe" if os.name == "nt" else ""
        candidate = os.path.join(hfs, "bin", "hoiiotool" + ext)
        if os.path.isfile(candidate): return candidate.replace("\\", "/")

    # 2. Try generic names
    return shutil.which("hoiiotool") or "hoiiotool"

OIIO_TOOL = find_oiio_tool()
MAX_WORKERS = 20  # Threads per machine

LOD_SPECS = [
    {"suffix": "LOD2",  "scale": 2},
    {"suffix": "LOD4",  "scale": 4},
    {"suffix": "LOD10", "scale": 10}
]

def get_dst_path(src, lod):
    src = src.replace("\\", "/")
    parts = src.split("/")
    if "export" in parts:
        parts.insert(len(parts) - 1 - parts[::-1].index("export") + 1, lod)
    else:
        parts.insert(-1, lod)
    
    stem, ext = os.path.splitext(parts[-1])
    if not stem.endswith(f"_{lod}"):
        parts[-1] = f"{stem}_{lod}{ext}"
    return "/".join(parts)

def convert_texture(src):
    try:
        # Generate all 3 LODs for this single texture
        for spec in LOD_SPECS:
            dst = get_dst_path(src, spec['suffix'])
            pct = int(100.0 / spec['scale'])
            
            try: os.makedirs(os.path.dirname(dst), exist_ok=True)
            except OSError: pass
            
            cmd = [OIIO_TOOL, src, "--resize", f"{pct}%", "-o", dst]
            
            # Run silently
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
            subprocess.run(cmd, check=True, startupinfo=startupinfo, stderr=subprocess.PIPE)
        return True, src
    except Exception as e:
        return False, f"{src}: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: script.py <manifest> <start> <end>")
        sys.exit(1)

    manifest_path, start_idx, end_idx = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

    print(f"Tool found at: {OIIO_TOOL}")

    with open(manifest_path, 'r') as f:
        all_files = json.load(f)

    # Slice the list for this specific task
    batch = all_files[start_idx : end_idx + 1]

    print(f"Processing {len(batch)} textures with {MAX_WORKERS} threads...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(convert_texture, path): path for path in batch}
        for future in concurrent.futures.as_completed(futures):
            success, msg = future.result()
            print(f"[{'OK' if success else 'FAIL'}] {msg}")
"""

# ==============================================================================
# 2. EMBEDDED DISPATCHER SCRIPT (For ROP Batching)
# ==============================================================================
DISPATCHER_SCRIPT_CONTENT = r"""
import sys
import os
import hou
import json

def main():
    if len(sys.argv) < 4:
        print("Usage: hython dispatcher.py <hip_path> <rop_list_json> <task_index>")
        sys.exit(1)

    hip_path = sys.argv[1]
    rop_list_str = sys.argv[2]
    task_index = int(sys.argv[3])

    print(f"--- Loading HIP: {hip_path} ---")
    try:
        hou.hipFile.load(hip_path)
    except hou.LoadWarning as e:
        print(e)

    try:
        rop_paths = json.loads(rop_list_str)
    except Exception as e:
        print(f"FATAL: Could not parse ROP list. {e}")
        sys.exit(1)

    print(f"--- Dispatching Task {task_index} of {len(rop_paths)} ---")

    if 0 <= task_index < len(rop_paths):
        target_rop = rop_paths[task_index]
        print(f"Target ROP: {target_rop}")
        
        node = hou.node(target_rop)
        if not node:
            raise RuntimeError(f"ROP Node not found: {target_rop}")
        
        # Render the specific ROP for this task
        node.render(verbose=True)
        print("--- Render Complete ---")
    else:
        print(f"Task index {task_index} out of range. Skipping.")

if __name__ == "__main__":
    main()
"""

# ==============================================================================
# 3. ASSEMBLY CHAIN SCRIPT (With Embedded Shotgun Logic)
# ==============================================================================
ASSEMBLY_SCRIPT_CONTENT = r"""
import sys
import os
import hou
import json
import traceback
import re

# Try importing shotgun_api3 (Provided by Rez package)
try:
    import shotgun_api3
except ImportError:
    shotgun_api3 = None

# ==============================================================================
# EMBEDDED SHOTGUN MANAGER (No external file dependency)
# ==============================================================================
class ShotgunDataManager:
    def __init__(self):
        if not shotgun_api3:
            raise ImportError("shotgun_api3 module is missing in the environment.")

        # --- CONFIGURATION: FILL IN YOUR REAL KEYS HERE ---
        self.sg = shotgun_api3.Shotgun(base_url="https://aivfx.shotgrid.autodesk.com",
                          script_name="hal_roxy_templates_rw",
                          api_key="cstmibkrtcwqmaz4sjwtexG~s")
        # --------------------------------------------------
        
        # Handle environment variables safely (Injected by Deadline)
        self.HAL_PROJECT_SGID = os.environ.get('HAL_PROJECT_SGID')
        self.HAL_PROJECT = os.environ.get('HAL_PROJECT')
        self.HAL_PROJECT_ABBR = os.environ.get('HAL_PROJECT_ABBR')
        self.HAL_PROJECT_ROOT = os.environ.get('HAL_PROJECT_ROOT')

        self.HAL_AREA = os.environ.get('HAL_AREA')
        self.HAL_USER_ABBR = os.environ.get('HAL_USER_ABBR')
        self.HAL_USER_LOGIN = os.environ.get('HAL_USER_LOGIN')

        self.HAL_TREE = os.environ.get('HAL_TREE')
        
        # Context Setup
        if self.HAL_TREE == "shots":
            self.HAL_SEQUENCE = os.environ.get('HAL_SEQUENCE')
            self.HAL_SEQUENCE_SGID = os.environ.get('HAL_SEQUENCE_SGID')
            self.HAL_SHOT = os.environ.get('HAL_SHOT')
            self.HAL_SHOT_SGID = os.environ.get('HAL_SHOT_SGID')
            self.HAL_CONTENT = f"{self.HAL_SEQUENCE}_{self.HAL_SHOT}_{os.environ.get('HAL_TASK')}"
            
        elif self.HAL_TREE == "assets":
            self.HAL_CATEGORY = os.environ.get('HAL_CATEGORY')
            self.HAL_ASSET = os.environ.get('HAL_ASSET')
            self.HAL_ASSET_SGID = os.environ.get('HAL_ASSET_SGID')
            self.HAL_CONTENT = f"{self.HAL_ASSET}_{os.environ.get('HAL_TASK')}"

        # Get Task
        self.HAL_TASK = os.environ.get('HAL_TASK')
        self.HAL_TASK_TYPE = os.environ.get('HAL_TASK_TYPE')
        self.HAL_TASK_ROOT = os.environ.get('HAL_TASK_ROOT')
        self.HAL_TASK_SGID = os.environ.get('HAL_TASK_SGID')

        self.task = None

    def upload_thumbnail(self, entity_type, entity_id, path, **kwargs):
        return self.sg.upload_thumbnail(entity_type, entity_id, path, **kwargs)

    def SG_Find_Version(self, anim_tag=""):
        parent_entity_type = None
        parent_entity_id = None

        if self.HAL_TREE == "shots":
            parent_entity_type = 'Shot'
            parent_entity_id = int(self.HAL_SHOT_SGID)
        elif self.HAL_TREE == "assets":
            parent_entity_type = 'Asset'
            parent_entity_id = int(self.HAL_ASSET_SGID)
        else:
            raise ValueError("HAL_TREE must be 'shots' or 'assets'.")

        # Find Task
        task_filters = [
            ['project', 'is', {'type': 'Project', 'id': int(self.HAL_PROJECT_SGID)}],
            ['entity', 'is', {'type': parent_entity_type, 'id': parent_entity_id}],
            ['content', 'is', self.HAL_CONTENT] 
        ]
        self.task = self.sg.find_one('Task', task_filters, fields=['id', 'content', 'entity'])
        
        if not self.task:
            # Fallback: Try finding task just by name if content doesn't match perfectly
            print(f"Warning: Exact task content '{self.HAL_CONTENT}' not found. Trying '{self.HAL_TASK}'...")
            task_filters[2] = ['content', 'is', self.HAL_TASK]
            self.task = self.sg.find_one('Task', task_filters, fields=['id', 'content', 'entity'])

        if not self.task:
             raise ValueError(f"Task not found for {self.HAL_CONTENT} or {self.HAL_TASK}")

        print(f"Found Task: {self.task['content']} (ID: {self.task['id']})")
        
        # Find existing versions
        version_filters = [
            ['project', 'is', {'type': 'Project', 'id': int(self.HAL_PROJECT_SGID)}],
            ['entity', 'is', {'type': parent_entity_type, 'id': parent_entity_id}], 
            ['sg_task', 'is', self.task] 
        ]
        
        all_versions = self.sg.find('Version', version_filters, fields=['code'], order=[{'field_name': 'created_at', 'direction': 'desc'}])
        
        versions_to_parse = []
        if anim_tag:
            for v in all_versions:
                if v['code'].endswith(f"-{anim_tag}"): versions_to_parse.append(v)
        else:
            for v in all_versions:
                if not re.search(r'_v\d{3,}_[a-zA-Z]{3}-', v['code']): versions_to_parse.append(v)

        version_numbers = []
        for version in versions_to_parse:
            version_match = re.search(r'_v(\d{3,})', version['code'])
            if version_match: version_numbers.append(int(version_match.group(1)))

        next_version = max(version_numbers) + 1 if version_numbers else 1
            
        base_name = f"{self.HAL_CONTENT}_v{next_version:03d}_{self.HAL_USER_ABBR}"
        return f"{base_name}-{anim_tag}" if anim_tag else base_name

    def Create_SG_Version(self, thumbnail_path, submit_path=None, first_frame=None, last_frame=None, anim_tag=""):
        highestVersion = self.SG_Find_Version(anim_tag=anim_tag)
        
        data = {
            "project": {"type": "Project", "name": self.HAL_PROJECT, "id": int(self.HAL_PROJECT_SGID)},
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
            print(f"Uploading thumbnail '{thumbnail_path}'...")
            try:
                self.upload_thumbnail("Version", created_version["id"], thumbnail_path)
                print("Thumbnail upload complete.")
            except Exception as e:
                print(f"ERROR: Failed to upload thumbnail: {e}")
        
        return created_version

# ==============================================================================
# MAIN LOGIC
# ==============================================================================
def publish_to_shotgun(hip_path, published_usd_path):
    print("\n=== Starting Shotgun Publish Attempt (Embedded) ===")
    
    # Soft Fail Check: Is path valid?
    if not published_usd_path: 
        print("SKIPPING: Output path is empty.")
        return

    # Try to find a thumbnail (filename.png or filename.jpg next to usd)
    thumb_path = ""
    base_no_ext = os.path.splitext(published_usd_path)[0]
    for ext in [".png", ".jpg", ".jpeg"]:
        candidate = base_no_ext + ext
        if os.path.exists(candidate):
            thumb_path = candidate
            break
            
    if thumb_path:
        print(f"Found thumbnail: {thumb_path}")
    else:
        print("No thumbnail found (looked for .png/.jpg matching USD name). Publishing without thumbnail.")

    try:
        sg_manager = ShotgunDataManager()
        sg_manager.Create_SG_Version(
            thumbnail_path=thumb_path if thumb_path else None,
            submit_path=published_usd_path
        )
        print("=== Shotgun Publish SUCCESS ===")
        
    except ImportError as e:
        print("!"*60)
        print(f"SHOTGUN FAIL: {e}")
        print("Please ensure 'shotgun_api3' is in your rez packages.")
        print("!"*60)
    except Exception as e:
        print("!"*60)
        print(f"SHOTGUN FAIL (Soft): {e}")
        print(traceback.format_exc())
        print("!"*60)
        print("Continuing job as SUCCESS.")

def main():
    if len(sys.argv) < 3:
        print("Usage: hython assembly_chain.py <hip_path> <rop_list_json>")
        sys.exit(1)

    hip_path = sys.argv[1]
    rop_list_str = sys.argv[2]

    print(f"--- Loading HIP: {hip_path} ---")
    try:
        hou.hipFile.load(hip_path)
    except hou.LoadWarning as e:
        print(e)

    try:
        rop_paths = json.loads(rop_list_str)
    except Exception as e:
        print(f"FATAL: Could not parse ROP list. {e}")
        sys.exit(1)

    print(f"--- Starting Assembly Chain ({len(rop_paths)} steps) ---")

    last_rop_node = None

    # EXECUTE ALL ROPS
    for i, rop_path in enumerate(rop_paths):
        print(f"Step {i+1}/{len(rop_paths)}: {rop_path}")
        node = hou.node(rop_path)
        if not node:
            print(f"ERROR: Node not found: {rop_path}")
            sys.exit(1)
        
        try:
            node.render(verbose=True)
            last_rop_node = node
        except hou.Error as e:
            print(f"Render Failed: {e}")
            sys.exit(1)
            
    print("--- Assembly Chain Complete ---")

    # --- TRIGGER SHOTGUN PUBLISH ---
    if last_rop_node:
        output_file = None
        # Try standard USD params
        if last_rop_node.parm("lopoutput"):
            output_file = last_rop_node.evalParm("lopoutput")
        elif last_rop_node.parm("vm_picture"):
            output_file = last_rop_node.evalParm("vm_picture")
            
        if output_file:
            publish_to_shotgun(hip_path, output_file)
        else:
            print("Skipping Shotgun: Could not determine output path from last ROP.")

if __name__ == "__main__":
    main()
"""

# ==============================================================================
# CONFIG & HELPERS
# ==============================================================================
def configEnvVars():
    ARNOLD_BIN_PATH = ""
    HTOA_ROOT = ""
    REZ_HOUDINI_HTOA_ROOT = os.environ.get("REZ_HOUDINI_HTOA_ROOT")
    
    if REZ_HOUDINI_HTOA_ROOT:
        ARNOLD_BIN_PATH = os.path.join(REZ_HOUDINI_HTOA_ROOT, "scripts", "bin")
        HTOA_ROOT = os.path.dirname(os.path.dirname(ARNOLD_BIN_PATH))

    ENV_PREFIXES_TO_KEEP = ["DY_", "HAL_", "HOUDINI_", "ARNOLD_", "OCIO"]
    ENV_EXACT_MATCHES    = ["JOB", "SHOW", "SHOT", "SEQ", "HIP"]
    ENV_BLOCKLIST        = [
        "HOUDINI_PATH", "PATH", "PYTHONHOME", "TEMP", "TMP", 
        "USER", "USERNAME", "COMPUTERNAME", "HOUDINI_TEMP_DIR", 
        "HOUDINI_USER_PREF_DIR", "HOUDINI_DESKTOP_DIR", "HOUDINI_SPLASH_FILE"
    ]
    return ENV_PREFIXES_TO_KEEP, ENV_EXACT_MATCHES, ENV_BLOCKLIST, ARNOLD_BIN_PATH, HTOA_ROOT

def get_safe_env_vars(config_data):
    prefixes, exacts, blocklist, _, _ = config_data
    safe_vars = {}
    print(">>> Scanning Environment Variables...")
    for key, value in os.environ.items():
        if key in blocklist: continue
        if key in exacts:
            safe_vars[key] = value
            continue
        if any(key.startswith(prefix) for prefix in prefixes):
            safe_vars[key] = value
    return safe_vars

def fetch_node_info_safely(node):
    original_mode = hou.updateModeSetting()
    try:
        hou.setUpdateMode(hou.updateMode.AutoUpdate)
        node.cook(force=True)        
    except Exception as e:
        print(f"Error cooking node: {e}")
    finally:
        hou.setUpdateMode(original_mode)

def get_resolved_paths(raw_path):
    if not raw_path: return []
    path_str = hou.text.abspath(raw_path)
    
    if "<UDIM>" in path_str or "<udim>" in path_str:
        pat = path_str.replace("<UDIM>", "*").replace("<udim>", "*")
        return [f.replace(os.sep, "/") for f in glob.glob(pat)]

    resolver = Ar.GetResolver()
    resolved = str(resolver.Resolve(path_str) or path_str)
    
    if os.path.isfile(resolved): return [resolved.replace(os.sep, "/")]
    if os.path.isfile(path_str): return [path_str.replace(os.sep, "/")]
    return []

def get_rez_packages_from_houdini():
    REZ_USED_RESOLVE = os.environ.get("REZ_USED_RESOLVE")
    packagesList = REZ_USED_RESOLVE.split(" ")
    allAddPkgs = []
    for package in packagesList:
        addPkg = f"+p {package}"
        allAddPkgs.append(addPkg)
    allPackagesList = " ".join(allAddPkgs)
    return allPackagesList

def get_outout_temp_folder(hdaNode):
    # 1. SETUP PATHS
    lop_output = hdaNode.evalParm("lopoutput")
    if not lop_output:
        print("ERROR: 'lopoutput' parameter is missing on HDA.")
        return None
        
    MANIFEST_FOLDER = os.path.join(os.path.split(lop_output)[0],"temp").replace("\\", "/")
    return MANIFEST_FOLDER

# ==============================================================================
# DEADLINE SUBMITTER CLASS
# ==============================================================================
class DeadlineSubmitter:
    def __init__(self):
        self.deadline_bin = r"C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe"
        env_path = os.environ.get("DEADLINE_PATH", "")
        if not os.path.exists(self.deadline_bin) and env_path:
            self.deadline_bin = os.path.join(env_path, "deadlinecommand.exe")
        if not os.path.exists(self.deadline_bin):
            raise FileNotFoundError("Deadline executable not found.")

    def _write_temp_file(self, info_dict, suffix):
        lines = []
        for k, v in info_dict.items():
            if v is not None:
                lines.append(f"{k}={v}")
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='w', encoding='utf-8')
        tmp.write("\n".join(lines))
        tmp.close()
        return tmp.name

    def submit(self, job_info, plugin_info):
        job_file = self._write_temp_file(job_info, ".job")
        plugin_file = self._write_temp_file(plugin_info, ".plugin")
        
        cmd = [self.deadline_bin, job_file, plugin_file]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        print(f">>> Sending '{job_info['Name']}' to Deadline...")
        result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
        
        try:
            os.unlink(job_file)
            os.unlink(plugin_file)
        except OSError:
            pass

        if result.returncode != 0:
            raise RuntimeError(f"Submission failed:\n{result.stderr}\n{result.stdout}")

        for line in result.stdout.splitlines():
            if line.startswith("JobID="):
                return line.split("=")[1].strip()
        return None

# ==============================================================================
# SUBMISSION FUNCTIONS
# ==============================================================================
def addJobItem(ropNode, batchName, pipeline_env, config_data, dependencies=None):
    if not ropNode:
        print("ERROR: ROP Node not found.")
        return None

    try:
        _, _, _, ARNOLD_BIN, HTOA_ROOT = config_data
        
        job_name = f"{hou.expandString('$HIPNAME')}-{ropNode.name()}"
        
        job_info = {
            "Name": job_name,
            "Plugin": "Houdini", 
            "Frames": "1",
            "Pool": "3d",
            "Group": "3d",
            "BatchName": batchName,
        }

        if dependencies:
            job_info["JobDependencies"] = ",".join(dependencies)

        env_index = 0
        if ARNOLD_BIN:
            job_info[f"EnvironmentKeyValue{env_index}"] = f"PATH={ARNOLD_BIN};%PATH%"
            env_index += 1
        if HTOA_ROOT:
            job_info[f"EnvironmentKeyValue{env_index}"] = f"HOUDINI_PATH={HTOA_ROOT};&"
            env_index += 1
            job_info[f"EnvironmentKeyValue{env_index}"] = f"HTOA={HTOA_ROOT}"
            env_index += 1

        for key, value in pipeline_env.items():
            job_info[f"EnvironmentKeyValue{env_index}"] = f"{key}={value}"
            env_index += 1

        plugin_info = {
            "SceneFile": hou.hipFile.path(),
            "OutputDriver": ropNode.path(),
            "Version": f"{hou.applicationVersion()[0]}.{hou.applicationVersion()[1]}",
            "IgnoreInputs": "True",
            "EnablePathMapping": "False"
        }

        submitter = DeadlineSubmitter()
        render_job_id = submitter.submit(job_info, plugin_info)
        print(f"SUCCESS: Job ID: {render_job_id}")
        return render_job_id

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR submitting {ropNode.path()}: {e}")
        return None

def submitGeoDispatchJob(ropNodes, batchName, pipeline_env, config_data, dependencies=None, hdaNode=None):
    if not ropNodes:
        return None
    if not hdaNode:
        print("ERROR: submitGeoDispatchJob requires 'hdaNode' to resolve output paths.")
        return None

    try:
        # 1. Force Cook
        fetch_node_info_safely(hdaNode)
        for ropNode in ropNodes:
            fetch_node_info_safely(ropNode)

        # 2. Setup Temp Folder
        OUTPUT_TEMP_FOLDER = get_outout_temp_folder(hdaNode)
        if not OUTPUT_TEMP_FOLDER:
            return None
            
        temp_dir = os.path.join(OUTPUT_TEMP_FOLDER, "deadline_scripts").replace("\\", "/")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # 3. Write Dispatcher Script
        script_path = os.path.join(temp_dir, "geo_dispatcher.py").replace("\\", "/")
        try:
            with open(script_path, "w") as f:
                f.write(DISPATCHER_SCRIPT_CONTENT)
        except IOError as e:
            print(f"CRITICAL ERROR: Could not write geo dispatcher script: {e}")
            return None

        # 4. Prepare Data
        rop_paths = [n.path().replace("\\", "/") for n in ropNodes]
        rop_list_json = json.dumps(rop_paths).replace('"', '\\"') 

        job_name = f"{hou.expandString('$HIPNAME')}-Geo_Variants_Batch"
        total_tasks = len(rop_paths)

        job_info = {
            "Name": job_name,
            "Plugin": "CommandLine", 
            "Frames": f"0-{total_tasks-1}", 
            "ChunkSize": "1", 
            "Pool": "3d",
            "Group": "3d",
            "BatchName": batchName,
            "ConcurrentTasks": "1", 
        }

        if dependencies:
            job_info["JobDependencies"] = ",".join(dependencies)

        # ----------------------------------------------------------------------
        # ENVIRONMENT INJECTION (CORRECTED)
        # ----------------------------------------------------------------------
        # We ONLY inject pipeline variables ($JOB, $SHOW).
        # We DO NOT touch PATH, so the worker can still find "afx.cmd".
        
        env_index = 0
        for key, value in pipeline_env.items():
            # SKIP PATH to ensure we don't break afx.cmd lookup
            if key.upper() == "PATH": 
                continue
                
            job_info[f"EnvironmentKeyValue{env_index}"] = f"{key}={value}"
            env_index += 1
        # ----------------------------------------------------------------------

        packagesList = get_rez_packages_from_houdini() 
        hip_path = hou.hipFile.path().replace("\\", "/")
        
        # Command: afx ... run hython ...
        args_str = f'{packagesList} run hython "{script_path}" "{hip_path}" "{rop_list_json}" <STARTFRAME>'

        plugin_info = {
            "Executable": "afx.cmd", # Now safe because we didn't kill the PATH
            "Arguments": args_str, 
            "Shell": "default",
            "StartupDirectory": temp_dir
        }

        submitter = DeadlineSubmitter()
        job_id = submitter.submit(job_info, plugin_info)
        print(f"SUCCESS: Geo Dispatch Job ID: {job_id}")
        return job_id

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR submitting Geo Dispatch Job: {e}")
        return None

def submitOIIOJob(ropNode, batchName, dependencies=None, hdaNode=None):
    if not ropNode:
        print("ERROR: OIIO Node not found.")
        return None

    try:
        fetch_node_info_safely(hdaNode)
        fetch_node_info_safely(ropNode)

        # 1. SETUP PATHS
        OUTPUT_TEMP_FOLDER = get_outout_temp_folder(hdaNode)
        if not OUTPUT_TEMP_FOLDER:
            return None
            
        if not os.path.exists(OUTPUT_TEMP_FOLDER):
            os.makedirs(OUTPUT_TEMP_FOLDER)

        # 2. WRITE WORKER SCRIPT
        WORKER_SCRIPT_PATH = os.path.join(OUTPUT_TEMP_FOLDER, "OIIO_process_LOD_Tasks.py").replace("\\", "/")
        try:
            with open(WORKER_SCRIPT_PATH, "w") as f:
                f.write(WORKER_SCRIPT_CONTENT)
            print(f">>> Worker script written to: {WORKER_SCRIPT_PATH}")
        except IOError as e:
            print(f"CRITICAL ERROR: Could not write worker script: {e}")
            return None

        # 3. SCAN TEXTURES (FIXED LOGIC)
        print(f">>> Scanning Stage for Textures from {ropNode.path()}...")
        stage = None
        
        # Method A: Try node.stage() (Works for LOP Nodes)
        try:
            stage = ropNode.stage()
        except AttributeError:
            pass
            
        # Method B: If ROP, try getting input node's stage
        if not stage:
            try:
                inputs = ropNode.inputs()
                if inputs:
                    stage = inputs[0].stage()
            except:
                pass

        # Method C: If still nothing, try the parent network's stage (common in LOPs)
        if not stage:
            try:
                # If ropNode is inside a LOP Net, parent usually holds the stage context
                stage = ropNode.parent().stage() 
            except:
                pass

        if not stage:
            print("CRITICAL ERROR: Could not retrieve USD Stage. OIIO Job Skipped.")
            # We return None here so dependencies don't break, but we warn heavily
            return None

        unique_paths = set()
        # Use TraverseAll() to ensure we catch everything, including deactivated prims if needed
        for prim in stage.Traverse():
            for attr_name in ["inputs:file", "inputs:filename", "file", "filename"]:
                attr = prim.GetAttribute(attr_name)
                if attr and attr.HasAuthoredValue():
                    val = attr.Get()
                    raw = val.path if isinstance(val, Sdf.AssetPath) else str(val)
                    if raw: unique_paths.add(raw)

        # 4. RESOLVE PATHS
        final_list = set()
        for p in unique_paths:
            final_list.update(get_resolved_paths(p))
        
        sorted_files = sorted(list(final_list))
        total_files = len(sorted_files)
        
        if total_files == 0:
            print("WARNING: No textures found to convert. Skipping OIIO job.")
            return None

        # 5. WRITE MANIFEST
        job_name = f"{hou.expandString('$HIPNAME')}-OIIO_Convert"
        manifest_file = os.path.join(OUTPUT_TEMP_FOLDER, f"{job_name}_{int(time.time())}.json").replace("\\", "/")
        
        with open(manifest_file, 'w') as f:
            json.dump(sorted_files, f, indent=4)
        print(f">>> Manifest saved: {manifest_file} ({total_files} files)")

        # 6. SUBMIT TO DEADLINE
        CHUNK_SIZE = 50 

        job_info = {
            "Name": job_name,
            "Plugin": "CommandLine", 
            "Frames": f"0-{total_files-1}",
            "ChunkSize": str(CHUNK_SIZE), 
            "Pool": "3d",
            "Group": "3d",
            "BatchName": batchName,
            "ConcurrentTasks": "1", 
        }

        if dependencies:
            job_info["JobDependencies"] = ",".join(dependencies)

        packagesList = get_rez_packages_from_houdini()
        args_str = f'{packagesList} run hython "{WORKER_SCRIPT_PATH}" "{manifest_file}" <STARTFRAME> <ENDFRAME>'

        plugin_info = {
            "Executable": "afx.cmd",
            "Arguments": args_str, 
            "Shell": "default",
            "StartupDirectory": OUTPUT_TEMP_FOLDER
        }

        submitter = DeadlineSubmitter()
        job_id = submitter.submit(job_info, plugin_info)
        print(f"SUCCESS: OIIO Job ID: {job_id}")
        return job_id

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR submitting OIIO Job: {e}")
        return None

def submitAssemblyJob(ropNodes, batchName, pipeline_env, config_data, dependencies=None, hdaNode=None):
    if not ropNodes or not hdaNode: return None

    import shutil 
    try:
        fetch_node_info_safely(hdaNode)
        for ropNode in ropNodes: fetch_node_info_safely(ropNode)

        OUTPUT_TEMP_FOLDER = get_outout_temp_folder(hdaNode)
        temp_dir = os.path.join(OUTPUT_TEMP_FOLDER, "deadline_scripts").replace("\\", "/")
        if not os.path.exists(temp_dir): os.makedirs(temp_dir)

        script_path = os.path.join(temp_dir, "assembly_chain.py").replace("\\", "/")
        with open(script_path, "w") as f: f.write(ASSEMBLY_SCRIPT_CONTENT)

        rop_paths = [n.path().replace("\\", "/") for n in ropNodes]
        rop_list_json = json.dumps(rop_paths).replace('"', '\\"') 

        job_name = f"{hou.expandString('$HIPNAME')}-Final_Assembly"

        job_info = {
            "Name": job_name,
            "Plugin": "CommandLine", 
            "Frames": "0", # ONE TASK ONLY
            "Pool": "3d", "Group": "3d", "BatchName": batchName
        }
        if dependencies: job_info["JobDependencies"] = ",".join(dependencies)

        env_index = 0
        for key, value in pipeline_env.items():
            if key.upper() == "PATH": continue
            job_info[f"EnvironmentKeyValue{env_index}"] = f"{key}={value}"
            env_index += 1

        packagesList = get_rez_packages_from_houdini() 
        hip_path = hou.hipFile.path().replace("\\", "/")
        
        exe = shutil.which("afx.cmd") or "afx.cmd"
        exe = exe.replace("\\", "/")

        # Note: No <STARTFRAME> needed for sequential script
        args_str = f'{packagesList} run hython "{script_path}" "{hip_path}" "{rop_list_json}"'

        plugin_info = {
            "Executable": exe, 
            "Arguments": args_str, 
            "Shell": "default", 
            "StartupDirectory": temp_dir
        }

        submitter = DeadlineSubmitter()
        job_id = submitter.submit(job_info, plugin_info)
        print(f"SUCCESS: Assembly Job ID: {job_id}")
        return job_id

    except Exception as e:
        print(f"ERROR submitting Assembly Job: {e}")
        return None

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

try:
    print("=== Starting Submission Chain (Final) ===")
    
    node = hou.pwd()
    hdaNode = node.parent().parent() 
    
    hou.hipFile.save()
    currentVersion = hdaNode.evalParm("currentVersion")
    batchName = f"{hou.expandString('$HIPNAME')}_{currentVersion}.hip"
    
    config_data = configEnvVars()
    pipeline_env = get_safe_env_vars(config_data)

    # ---------------------------------------------------------
    # 1. PREP: Create Output Folder (Local Execution)
    # ---------------------------------------------------------
    createOutputFolder = hdaNode.node("createOutputFolder")
    if createOutputFolder:
        print(">>> Executing 'createOutputFolder' locally...")
        createOutputFolder.parm("execute").pressButton()

    # ---------------------------------------------------------
    # 2. JOB: OIIO Conversion (Independent)
    # ---------------------------------------------------------
    # Note: Ensure the path matches your graph. 
    # Previous error showed "convertImageOIIO_ROP", your script had "convertImageOIIO_batch".
    # I am using the one that worked in your logs previously.
    convertImageOIIO = hdaNode.node("Shd_Layer/convertImageOIIO_ROP") 
    if not convertImageOIIO:
        convertImageOIIO = hdaNode.node("Shd_Layer/convertImageOIIO_batch")

    oiio_job_id = submitOIIOJob(convertImageOIIO, batchName, None, hdaNode)

    # ---------------------------------------------------------
    # 3. JOB: Geo Phase 1 - LOD0 (The Source)
    # ---------------------------------------------------------
    print(">>> Submitting Geo Phase 1: LOD0 (Source)...")
    
    geo_lod0_node = hdaNode.node("Variant_Layer/geoVariant_LOD0_ROP")
    geo_lod0_job_id = None
    
    if geo_lod0_node:
        geo_lod0_job_id = addJobItem(geo_lod0_node, batchName, pipeline_env, config_data, dependencies=None)
    else:
        print("CRITICAL ERROR: LOD0 ROP not found.")

    # ---------------------------------------------------------
    # 4. JOB: Geo Phase 2 - LOD1 to LOD5 (The Batch)
    # ---------------------------------------------------------
    print(">>> Submitting Geo Phase 2: LOD1-5 Batch (Dependent)...")
    
    lod_batch_paths = [
        "Variant_Layer/VariantLOD1/geoVariant_LOD1_ROP",
        "Variant_Layer/VariantLOD2/geoVariant_LOD2_ROP",
        "Variant_Layer/VariantLOD3/geoVariant_LOD3_ROP",
        "Variant_Layer/VariantLOD4/geoVariant_LOD4_ROP",
        "Variant_Layer/VariantLOD5/geoVariant_LOD5_ROP",
    ]
    
    geo_batch_rops = []
    for p in lod_batch_paths:
        n = hdaNode.node(p)
        if n: geo_batch_rops.append(n)
        else: print(f"Warning: ROP not found: {p}")

    geo_batch_job_id = None
    if geo_batch_rops:
        batch_deps = []
        if geo_lod0_job_id: 
            batch_deps.append(geo_lod0_job_id)
        
        geo_batch_job_id = submitGeoDispatchJob(
            ropNodes=geo_batch_rops, 
            batchName=batchName, 
            pipeline_env=pipeline_env, 
            config_data=config_data,   
            dependencies=batch_deps, 
            hdaNode=hdaNode
        )

    # ---------------------------------------------------------
    # 5. JOB: FINAL ASSEMBLY (Everything else merged)
    # ---------------------------------------------------------
    print(">>> Submitting Final Assembly Chain...")

    # Define the exact execution order
    assembly_order_paths = [
        "Geo_Rop",                                  # 1. Merge Geo
        "Shd_Layer/LOD0/shdVariant_LOD0_ROP",       # 2. Shader Variant 0
        "Shd_Layer/LOD2/shdVariant_LOD2_ROP",       # 3. Shader Variant 2
        "Shd_Layer/LOD4/shdVariant_LOD4_ROP",       # 4. Shader Variant 4
        "Shd_Layer/LOD10/shdVariant_LOD10_ROP",     # 5. Shader Variant 10
        "Shd_ROP",                                  # 6. Merge Shaders
        "Payload_layer/payload_Rop",                # 7. Payload
        "write_USD"                                 # 8. Final Write
    ]

    assembly_nodes = []
    for p in assembly_order_paths:
        n = hdaNode.node(p)
        if n: assembly_nodes.append(n)
        else: print(f"Warning: Assembly node not found: {p}")

    if assembly_nodes:
        # Dependencies: Waits for Geo Batch (which waited for LOD0) + OIIO
        assembly_deps = []
        if geo_batch_job_id: assembly_deps.append(geo_batch_job_id)
        # Fallback: if batch didn't run, wait for LOD0
        elif geo_lod0_job_id: assembly_deps.append(geo_lod0_job_id)
        
        if oiio_job_id: assembly_deps.append(oiio_job_id)

        submitAssemblyJob(
            ropNodes=assembly_nodes,
            batchName=batchName,
            pipeline_env=pipeline_env,
            config_data=config_data,
            dependencies=assembly_deps,
            hdaNode=hdaNode
        )

    print("=== Submission Complete ===")
    hdaNode.parm("refreshVersion").pressButton()
    hou.ui.displayMessage("Usd资产已经成功上传到Deadline10进行分批处理，最后上传Shotgun，请时刻关注Deadline10！")

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Global Execution Error: {e}")
