import PyInstaller.__main__
import os
import shutil
import sys

# 清理之前的构建文件
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# 打包参数
PyInstaller.__main__.run([
    'sticky_note.py',  # 主程序文件
    '--name=StickyNote',  # 生成的exe名称
    '--windowed',  # 使用GUI模式
    '--noconsole',  # 不显示控制台
    '--icon=sticky_note_icon.ico',  # 程序图标
    '--add-data=sticky_note_icon.ico;.',  # 添加图标资源
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不确认覆盖
    '--onefile',  # 打包成单个文件
    '--hidden-import=win32api',
    '--hidden-import=win32event',
    '--hidden-import=winerror',
    '--hidden-import=win32con',
    '--hidden-import=win32gui',
    '--hidden-import=win32process',
    '--hidden-import=win32security',
    '--hidden-import=win32timezone',
    '--hidden-import=markdown',
    '--hidden-import=PyQt5',
    '--hidden-import=PyQt5.QtCore',
    '--hidden-import=PyQt5.QtGui',
    '--hidden-import=PyQt5.QtWidgets',
    '--collect-all=win32api',
    '--collect-all=win32event',
    '--collect-all=win32con',
    '--collect-all=win32gui',
    '--collect-all=win32process',
    '--collect-all=win32security',
    '--collect-all=win32timezone',
])

# 创建数据目录
os.makedirs('dist/data', exist_ok=True)

print("打包完成！") 