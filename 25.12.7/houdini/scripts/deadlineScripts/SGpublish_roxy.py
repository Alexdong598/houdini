# -*- coding: utf-8 -*-
import subprocess
import sys
import argparse # 导入 argparse 模块用于解析命令行参数

def main():
    """
    主执行函数，用于调用外部命令行工具。
    现在它会从命令行接收参数，而不是使用硬编码的路径。
    """
    print("--- Starting SGpublish_roxy.py ---")

    # ================================================================
    # 1. 设置命令行参数解析器
    # ================================================================
    parser = argparse.ArgumentParser(description="A post-render script to run the 'hal roxy' command.")
    parser.add_argument("--source", required=True, help="The source file path for the roxy command.")
    parser.add_argument("--template", required=True, help="The template string for the roxy command.")
    
    # 解析从命令行传递过来的参数
    # sys.argv[1:] 会忽略脚本名称本身，只解析后面的参数
    try:
        # 在复杂的命令行调用中，未知参数可能导致argparse失败
        # 使用 parse_known_args 更稳健
        args, unknown = parser.parse_known_args(sys.argv[1:])
        if unknown:
            print(f"警告：发现未知参数: {unknown}")
    except SystemExit:
        # 如果 argparse 发现参数不匹配（例如缺少--source），它会打印帮助信息并退出
        # 我们在这里捕获它，以确保脚本以错误码退出
        print("[ERROR] Failed to parse command-line arguments.")
        sys.exit(1)


    print(f"Received source path: {args.source}")
    print(f"Received template: {args.template}")

    # ================================================================
    # 2. 使用解析到的参数来构建命令列表
    # ================================================================
    command_list = [
        r"\\af\x\hal.cmd",
        "roxy",
        "--ignore-standard-args",
        "--source",
        args.source,      # 使用从命令行获取的 source 路径
        "--template",
        args.template     # 使用从命令行获取的 template
    ]

    # 为了日志清晰，打印出将要执行的命令
    print(f"Executing command: {' '.join(command_list)}")

    try:
        # ================================================================
        # 执行外部命令 (这部分逻辑保持不变)
        # ================================================================
        result = subprocess.run(
            command_list, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            shell=False 
        )

        print("\n--- Command executed successfully! ---")
        print("\n--- STDOUT (标准输出) ---")
        print(result.stdout)
        
        if result.stderr:
            print("\n--- STDERR (标准错误/警告) ---")
            print(result.stderr)

    except FileNotFoundError:
        print(f"\n[ERROR] The command '{command_list[0]}' was not found.")
        print("Please ensure the path is correct and accessible from the Deadline worker machine.")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] An error occurred while executing the command. Return code: {e.returncode}")
        print("\n--- STDOUT (标准输出) ---")
        print(e.stdout)
        print("\n--- STDERR (标准错误) ---")
        print(e.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}")
        sys.exit(1)

    print("\n--- Finished SGpublish_roxy.py ---")

if __name__ == "__main__":
    main()
