"""
main.py - 卫星遥测数据分析系统主程序入口
功能：直接启动图形用户界面
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))


def check_dependencies():
    """检查必要的依赖包"""
    required = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'yaml': 'PyYAML'  # 导入名: 安装包名
    }
    missing = []

    for import_name, package_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append((import_name, package_name))

    if missing:
        print("缺少必要的依赖包:")
        for import_name, package_name in missing:
            print(f"  - {package_name} (导入名: {import_name})")
        print("\n请使用以下命令安装:")
        print("pip install " + " ".join(package_name for _, package_name in missing))
        return False
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("卫星遥测数据分析系统 v1.0")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        input("按 Enter 键退出...")
        sys.exit(1)

    try:
        # 尝试导入GUI模块
        from gui.main_gui import main as gui_main

        print("正在启动图形界面...")
        print("-" * 50)

        # 启动GUI
        gui_main()

    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请确保所有模块文件都存在且路径正确")
        input("按 Enter 键退出...")
        sys.exit(1)
    except Exception as e:
        print(f"启动失败: {e}")
        input("按 Enter 键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()