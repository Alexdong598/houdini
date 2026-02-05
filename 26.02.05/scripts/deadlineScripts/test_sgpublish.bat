@echo off
REM =================================================================
REM 测试脚本: 用于模拟 Deadline Worker 节点调用 SGpublish_roxy.py
REM 用途: 验证命令行参数是否能被 Python 脚本正确接收和解析。
REM =================================================================

ECHO.
ECHO --- SGpublish_roxy.py 参数接收测试 ---
ECHO.

REM --- 1. 请根据您的环境修改以下变量 ---

REM hal.cmd 的完整路径
SET HAL_CMD_PATH=\\af\x\hal.cmd

REM SGpublish_roxy.py 脚本的完整路径
SET PYTHON_SCRIPT_TO_TEST=\\af\app_config\release\settings\base\hal_roxy2\templates\_scripts\SGpublish_roxy.py

REM 模拟从 Houdini 传递过来的参数
SET "MOCK_SOURCE_PATH=Y:\penghu_phu-2069\_library\assets\characters\chr_qjsb2\renders\shd\v001\fullres\phu_chr_qjsb2_shd_v001_test.1001.exr"
SET "MOCK_TEMPLATE=penghu_phu-2069/sg-1ookdev_mov_HD"
SET "MOCK_JOB_ID=63e5a1b2c3d4e5f6a7b8c9d0"

REM --- 2. 构建将要执行的完整命令 ---
REM    注意：这里的结构和您在Houdini提交脚本中构建的 "post_job_arguments" 是一致的。
SET "FULL_COMMAND=%HAL_CMD_PATH% roxy --run-by-tool +p python-2 run python "%PYTHON_SCRIPT_TO_TEST%" --source "%MOCK_SOURCE_PATH%" --template "%MOCK_TEMPLATE%" --job-id "%MOCK_JOB_ID%""


REM --- 3. 执行并显示结果 ---
ECHO 将要执行的完整命令是:
ECHO %FULL_COMMAND%
ECHO.
ECHO -------------------- Python 脚本输出开始 --------------------
ECHO.

REM 执行命令
%FULL_COMMAND%

ECHO.
ECHO -------------------- Python 脚本输出结束 --------------------
ECHO.
ECHO 测试完成。
ECHO.

REM 暂停窗口，方便查看输出结果
pause
