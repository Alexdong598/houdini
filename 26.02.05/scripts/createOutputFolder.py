def run():
    
    import hou
    import os
    
    node = hou.pwd()
    HDAnode = node.parent()
    
    # USE HOU.GETENV
    # It is safer inside Houdini than os.environ because it handles empty variables better
    # and integrates with Houdini's internal variable mapping.
    dy_dcc_raw = hou.getenv("DY_DCC")
    hal_task_root = hou.getenv("HAL_TASK_ROOT")
    
    # Defensive Check: Ensure variables exist before proceeding
    if not dy_dcc_raw or not hal_task_root:
        print("WARNING: 'DY_DCC' or 'HAL_TASK_ROOT' environment variables are missing on the farm.")
        # Fallback or exit gracefully to avoid crashing with a confusing error
        DY_DCC = "unknown_dcc" 
    else:
        DY_DCC = dy_dcc_raw.lower()
    
    HAL_TASK_ROOT = hal_task_root
    
    # Proceed only if we have valid paths
    if HAL_TASK_ROOT:
        try:
            nextVersionStatic = HDAnode.evalParm("nextVersionStatic")
            # Safety check for input connection
            input_node = node.input(0)
            if input_node:
                root_prim = input_node.evalParm("primpattern")
                
                folderPath = f"{HAL_TASK_ROOT}/_publish/{DY_DCC}{root_prim}/{nextVersionStatic}".replace(os.sep,"/")
    
                if folderPath and not os.path.exists(folderPath):
                    os.makedirs(folderPath)
                    print(f"Created directory: {folderPath}")
            else:
                print("Error: No input connected to node.")
                
        except OSError as e:
            print(f"Error creating directory: {e}")
        except Exception as e:
            print(f"General Script Error: {e}")
    else:
        print("Skipping folder creation: HAL_TASK_ROOT is undefined.")
        
run()