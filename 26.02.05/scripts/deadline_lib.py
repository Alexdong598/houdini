import os
import subprocess
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeadlineSubmitter:
    def __init__(self, deadline_bin=None):
        self.deadline_bin = deadline_bin
        if not self.deadline_bin:
            # 简化逻辑：直接找环境变量或默认路径
            self.deadline_bin = os.environ.get("DEADLINE_PATH", r"C:\Program Files\Thinkbox\Deadline10\bin")
            self.deadline_bin = os.path.join(self.deadline_bin, "deadlinecommand.exe")
        
        if not os.path.exists(self.deadline_bin):
             # 生产环境建议 raise Error，这里仅 log warning
            logger.error(f"Deadline binary not found at {self.deadline_bin}")

    def submit(self, job_info: dict, plugin_info: dict, dependencies=None):
        """
        dependencies: list or string of Job IDs (e.g., ["id1", "id2"] or "id1,id2")
        """
        
        # --- 1. 处理依赖关系 ---
        if dependencies:
            if isinstance(dependencies, list):
                # 过滤掉 None 和空字符串
                valid_deps = [d for d in dependencies if d]
                job_info["JobDependencies"] = ",".join(valid_deps)
            elif isinstance(dependencies, str) and dependencies.strip():
                job_info["JobDependencies"] = dependencies

        # --- 2. 写入临时文件 ---
        job_file = self._write_temp_file(job_info, ".job")
        plugin_file = self._write_temp_file(plugin_info, ".plugin")
        
        cmd = [self.deadline_bin, job_file, plugin_file]
        
        # --- 3. 执行提交 ---
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # 使用 capture_output=True 捕获输出
            result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo)
        except Exception as e:
            self._cleanup(job_file, plugin_file)
            raise RuntimeError(f"Failed to execute deadlinecommand: {e}")

        self._cleanup(job_file, plugin_file)

        if result.returncode != 0:
            raise RuntimeError(f"Deadline submission failed:\n{result.stderr}\n{result.stdout}")

        # --- 4. 解析 Job ID ---
        # Deadline 成功输出通常包含 "JobID=xxxxxx"
        job_id = None
        for line in result.stdout.splitlines():
            if line.strip().startswith("JobID="):
                job_id = line.strip().split("=")[1]
                break
        
        if not job_id:
            # 兜底：如果没有明确的 JobID= 行，打印全部输出以便 Debug
            logger.warning(f"Submission ran but JobID not found. Output:\n{result.stdout}")
            return None

        return job_id

    def _cleanup(self, *files):
        for f in files:
            try:
                os.unlink(f)
            except OSError:
                pass

    @staticmethod
    def _write_temp_file(info_dict, suffix):
        lines = []
        for k, v in info_dict.items():
            if v is not None: # 过滤 None
                lines.append(f"{k}={v}")
        
        # 必须显式关闭文件，Windows 下子进程才能读取
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='w', encoding='utf-8')
        tmp.write("\n".join(lines))
        tmp.close()
        return tmp.name