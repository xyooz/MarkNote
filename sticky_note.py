import sys
import os
import winreg  # 添加winreg导入
import win32event
import win32api
import winerror
import markdown
from PyQt5.QtWidgets import (
    QApplication, QTextEdit, QWidget, QVBoxLayout, QSplitter,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QShortcut, QPushButton, QHBoxLayout,
    QColorDialog, QDialog, QLabel, QLineEdit, QDialogButtonBox, QCheckBox, QScrollArea,
    QListWidget, QListWidgetItem, QToolBar, QFontComboBox, QSpinBox, QComboBox, QFileDialog
)
from PyQt5.QtCore import Qt, QSettings, QPoint, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QColor, QCursor, QTextCharFormat, QSyntaxHighlighter
from PyQt5.QtCore import QRegExp
import shutil

note_counter = 0

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class SingleInstanceChecker:
    def __init__(self):
        self.mutexname = "Global\\StickyNoteAppMutex"
        self.mutex = win32event.CreateMutex(None, False, self.mutexname)
        self.last_error = win32api.GetLastError()

    def is_another_instance_running(self):
        return self.last_error == winerror.ERROR_ALREADY_EXISTS

    def __del__(self):
        if self.mutex:
            win32api.CloseHandle(self.mutex)

class TodoItem(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # 减小边距
        layout.setSpacing(4)  # 减小组件之间的间距
        
        checkbox_container = QWidget()
        checkbox_container.setFixedSize(32, 32)
        checkbox_layout = QHBoxLayout(checkbox_container)
        checkbox_layout.setContentsMargins(2, 2, 2, 2)
        checkbox_layout.setSpacing(0)
        
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(28, 28)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 0px;
                padding: 0px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border-radius: 11px;
                border: 2px solid #e0e0e0;
                background-color: transparent;
                margin: 1px;
            }
            QCheckBox::indicator:hover {
                border-color: #4CAF50;
                background-color: rgba(76, 175, 80, 0.1);
            }
            QCheckBox::indicator:pressed {
                border-color: #4CAF50;
                background-color: rgba(76, 175, 80, 0.2);
            }
            QCheckBox::indicator:checked {
                border: none;
                background-color: #4CAF50;
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNCIgaGVpZ2h0PSIxNCIgdmlld0JveD0iMCAwIDE2IDE2Ij48cGF0aCBmaWxsPSJub25lIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBkPSJNMyA4LjVMNiAxMkwxMyA0Ii8+PC9zdmc+);
                background-repeat: no-repeat;
                background-position: center;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #43A047;
            }
            QCheckBox::indicator:checked:pressed {
                background-color: #388E3C;
            }
        """)
        
        checkbox_layout.addWidget(self.checkbox, 0, Qt.AlignCenter)
        
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("输入待办事项...")
        self.text_edit.setFont(QFont("Segoe UI", 11))
        self.text_edit.setStyleSheet("""
            QLineEdit {
                border: none;
                padding: 6px 8px;
                color: #333;
                background-color: transparent;
                border-radius: 4px;
                min-height: 32px;
            }
            QLineEdit:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QLineEdit:focus {
                background-color: rgba(0, 0, 0, 0.08);
            }
        """)
        
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(32, 32)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #bdbdbd;
                border: none;
                border-radius: 16px;
                font-size: 22px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 0.1);
                color: #f44336;
            }
            QPushButton:pressed {
                background-color: rgba(244, 67, 54, 0.2);
                color: #d32f2f;
            }
        """)
        
        layout.addWidget(checkbox_container, 0, Qt.AlignCenter)
        layout.addWidget(self.text_edit, 1)
        layout.addWidget(self.delete_btn, 0, Qt.AlignCenter)
        self.setLayout(layout)
        
        # 连接信号
        self.checkbox.stateChanged.connect(self.on_state_changed)
        self.text_edit.textChanged.connect(self.on_text_changed)
        self.delete_btn.clicked.connect(self.on_delete)

    def on_state_changed(self, state):
        if state == Qt.Checked:
            self.text_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 6px 8px;
                    color: #9e9e9e;
                    text-decoration: line-through;
                    background-color: transparent;
                    border-radius: 4px;
                    min-height: 28px;
                }
                QLineEdit:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
                QLineEdit:focus {
                    background-color: rgba(0, 0, 0, 0.08);
                }
            """)
        else:
            self.text_edit.setStyleSheet("""
                QLineEdit {
                    border: none;
                    padding: 6px 8px;
                    color: #333;
                    background-color: transparent;
                    border-radius: 4px;
                    min-height: 28px;
                }
                QLineEdit:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
                QLineEdit:focus {
                    background-color: rgba(0, 0, 0, 0.08);
                }
            """)
        # 通知父窗口内容已更改
        parent = self.parent()
        while parent:
            if hasattr(parent, 'handle_todo_changed'):
                parent.handle_todo_changed()
                break
            parent = parent.parent()

    def on_text_changed(self, text):
        # 通知父窗口内容已更改
        parent = self.parent()
        while parent:
            if hasattr(parent, 'handle_todo_changed'):
                parent.handle_todo_changed()
                break
            parent = parent.parent()

    def on_delete(self):
        # 通知父窗口内容已更改
        parent = self.parent()
        while parent:
            if hasattr(parent, 'handle_todo_changed'):
                parent.handle_todo_changed()
                break
            parent = parent.parent()
        self.deleteLater()

class FormatToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QToolBar {
                background-color: transparent;
                border: none;
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 4px;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            QToolButton:pressed {
                background-color: rgba(0, 0, 0, 0.1);
            }
            QToolButton:checked {
                background-color: rgba(0, 0, 0, 0.1);
            }
        """)

        # 字体选择
        self.font_combo = QFontComboBox()
        self.font_combo.setFixedWidth(120)
        self.addWidget(self.font_combo)

        # 字号选择
        self.size_combo = QComboBox()
        self.size_combo.setFixedWidth(50)
        sizes = ['8', '9', '10', '11', '12', '14', '16', '18', '20', '22', '24', '26', '28', '36', '48', '72']
        self.size_combo.addItems(sizes)
        self.size_combo.setCurrentText('11')
        self.addWidget(self.size_combo)

        self.addSeparator()

        # 加粗
        self.bold_action = QAction(QIcon(), "B", self)
        self.bold_action.setCheckable(True)
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setToolTip("加粗 (Ctrl+B)")
        self.addAction(self.bold_action)

        # 斜体
        self.italic_action = QAction(QIcon(), "I", self)
        self.italic_action.setCheckable(True)
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setToolTip("斜体 (Ctrl+I)")
        self.addAction(self.italic_action)

        # 下划线
        self.underline_action = QAction(QIcon(), "U", self)
        self.underline_action.setCheckable(True)
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setToolTip("下划线 (Ctrl+U)")
        self.addAction(self.underline_action)

        self.addSeparator()

        # 文字颜色
        self.text_color_action = QAction(QIcon(), "A", self)
        self.text_color_action.setToolTip("文字颜色")
        self.addAction(self.text_color_action)

        # 设置字体样式
        format_font = QFont("Segoe UI", 11)
        format_font.setBold(True)
        self.bold_action.setFont(format_font)
        
        format_font.setBold(False)
        format_font.setItalic(True)
        self.italic_action.setFont(format_font)
        
        format_font.setItalic(False)
        format_font.setUnderline(True)
        self.underline_action.setFont(format_font)
        
        format_font.setUnderline(False)
        self.text_color_action.setFont(format_font)

class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 标题格式
        h1_format = QTextCharFormat()
        h1_format.setFontWeight(QFont.Bold)
        h1_format.setFontPointSize(20)
        self.highlighting_rules.append((QRegExp("^#\\s.*$"), h1_format))

        h2_format = QTextCharFormat()
        h2_format.setFontWeight(QFont.Bold)
        h2_format.setFontPointSize(16)
        self.highlighting_rules.append((QRegExp("^##\\s.*$"), h2_format))

        h3_format = QTextCharFormat()
        h3_format.setFontWeight(QFont.Bold)
        h3_format.setFontPointSize(14)
        self.highlighting_rules.append((QRegExp("^###\\s.*$"), h3_format))

        # 粗体格式
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegExp("\\*\\*.*\\*\\*"), bold_format))
        self.highlighting_rules.append((QRegExp("__.*__"), bold_format))

        # 斜体格式
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("\\*.*\\*"), italic_format))
        self.highlighting_rules.append((QRegExp("_.*_"), italic_format))

        # 代码块格式
        code_format = QTextCharFormat()
        code_format.setFontFamily("Consolas")
        code_format.setBackground(QColor("#f6f8fa"))
        self.highlighting_rules.append((QRegExp("`.*`"), code_format))

        # 列表格式
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#0366d6"))
        self.highlighting_rules.append((QRegExp("^\\s*[\\*\\-\\+]\\s"), list_format))
        self.highlighting_rules.append((QRegExp("^\\s*\\d+\\.\\s"), list_format))

        # 引用格式
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#6a737d"))
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("^>\\s.*$"), quote_format))

        # 链接格式
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#0366d6"))
        link_format.setUnderlineStyle(QTextCharFormat.SingleUnderline)
        self.highlighting_rules.append((QRegExp("\\[.*\\]\\(.*\\)"), link_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

class MarkdownEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = MarkdownHighlighter(self.document())
        self.setFont(QFont("Segoe UI", 11))
        self.setAcceptRichText(False)  # 只接受纯文本
        self.setPlaceholderText("写点什么吧……")  # 添加占位文本
        self.is_preview_mode = False
        self.last_content = ""
        self.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                padding: 8px;
            }
        """)
        
        # 设置tab键为4个空格
        self.setTabStopWidth(self.fontMetrics().width(' ') * 4)

    def insertFromMimeData(self, source):
        """重写此方法以确保粘贴时只插入纯文本"""
        self.insertPlainText(source.text())

    def toggle_preview(self):
        """切换预览模式"""
        if self.is_preview_mode:
            # 从预览模式切换回编辑模式
            self.setHtml("")  # 清除HTML内容
            self.setPlainText(self.last_content)
            self.setReadOnly(False)
            self.is_preview_mode = False
        else:
            # 从编辑模式切换到预览模式
            self.last_content = self.toPlainText()
            html = self.convert_to_html(self.last_content)
            self.setHtml(html)
            self.setReadOnly(True)
            self.is_preview_mode = True

    def convert_to_html(self, content):
        """将Markdown内容转换为HTML"""
        html = markdown.markdown(
            content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        return f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
                margin: 0;
                padding: 0;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #2c3e50;
                font-weight: 600;
            }}
            h1 {{ font-size: 2em; }}
            h2 {{ font-size: 1.5em; }}
            h3 {{ font-size: 1.17em; }}
            p {{ margin: 1em 0; }}
            code {{
                background-color: #f6f8fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
                margin: 1em 0;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
                border-radius: 0;
            }}
            blockquote {{
                border-left: 4px solid #dfe2e5;
                margin: 1em 0;
                padding-left: 1em;
                color: #6a737d;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #dfe2e5;
                padding: 6px 13px;
            }}
            th {{
                background-color: #f6f8fa;
            }}
            ul, ol {{
                margin: 1em 0;
                padding-left: 2em;
            }}
            li {{
                margin: 0.5em 0;
            }}
            hr {{
                border: none;
                border-top: 1px solid #dfe2e5;
                margin: 1em 0;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
        </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """

class MarkdownPreview(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Segoe UI", 11))
        self.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
            }
        """)

    def update_preview(self, markdown_text):
        html = markdown.markdown(
            markdown_text,
            extensions=[
                'tables',
                'fenced_code',
                'nl2br'
            ]
        )
        self.setHtml(html)

class StickyNote(QWidget):
    def __init__(self, id):
        super().__init__()
        self.id = id
        self.is_modified = False
        self.setWindowTitle(f"📝 便签 {id}")
        
        # 设置默认大小
        self.default_size = QSize(450, 600)
        # 强制设置初始大小
        self.resize(self.default_size)
        
        self.setWindowFlags(Qt.WindowStaysOnBottomHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(300, 250)
        self.setMaximumSize(900, 1500)
        self.setMouseTracking(True)

        # 添加Ctrl+S快捷键
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.manual_save)

        # 获取保存路径
        app_settings = QSettings("MyCompany", "StickyNoteApp")
        save_path = app_settings.value("save_path", os.path.join(os.path.expanduser("~"), "StickyNotes"))
        os.makedirs(save_path, exist_ok=True)
        
        # 修改设置保存路径
        self.settings = QSettings(
            os.path.join(save_path, f"DesktopNote{id}.ini"),
            QSettings.IniFormat
        )
        self.settings.setFallbacksEnabled(False)  # 禁用回退机制
        
        self.resize_margin = 8
        self.corner_size = 16
        self.is_dragging = False
        self.is_resizing = False
        self.resize_cursor = None
        self.resize_start_pos = None
        self.resize_start_geometry = None
        self.drag_pos = None
        self.last_pos = None
        self.is_position_fixed = self.settings.value("is_position_fixed", False, type=bool)
        self.auto_save_timer = None  # 自动保存计时器
        self.bg_color = self.settings.value("bg_color", "#fefae0")

        # 创建主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建顶部按钮区域
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(40)
        self.top_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {self.bg_color};
                border-bottom: 1px solid rgba(0, 0, 0, 0.08);
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(14, 0, 14, 0)
        top_bar_layout.setSpacing(14)

        # 创建标题标签
        self.title_label = QLabel(f"📝 便签 {id}")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 18px;
                font-weight: 500;
            }
        """)
        top_bar_layout.addWidget(self.title_label)

        # 添加保存状态标签
        self.save_status = QLabel("")
        self.save_status.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 18px;
            }
        """)
        top_bar_layout.addWidget(self.save_status)

        top_bar_layout.addStretch()

        # 添加待办按钮
        self.todo_btn = QPushButton("✓")
        self.todo_btn.setFixedSize(28, 28)
        self.todo_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-radius: 14px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
                color: #4CAF50;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
        """)
        self.todo_btn.clicked.connect(self.insert_todo_item)
        self.todo_btn.setToolTip("添加待办事项")
        top_bar_layout.addWidget(self.todo_btn)

        # 添加固定按钮
        self.pin_btn = QPushButton("📌")
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-radius: 14px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
                color: #007acc;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
            QPushButton:checked {
                background-color: #007acc;
                color: white;
            }
        """)
        self.pin_btn.setCheckable(True)
        self.pin_btn.setChecked(self.is_position_fixed)
        self.pin_btn.clicked.connect(self.toggle_position_fixed)
        self.update_pin_button_text()
        top_bar_layout.addWidget(self.pin_btn)

        # 添加关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-radius: 14px;
                font-size: 22px;
            }
            QPushButton:hover {
                background-color: rgba(244, 67, 54, 0.1);
                color: #f44336;
            }
            QPushButton:pressed {
                background-color: rgba(244, 67, 54, 0.2);
                color: #d32f2f;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        top_bar_layout.addWidget(self.close_btn)

        # 添加预览切换按钮
        self.preview_btn = QPushButton("👁")
        self.preview_btn.setFixedSize(28, 28)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                border-radius: 14px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.08);
                color: #007acc;
            }
            QPushButton:pressed {
                background-color: rgba(0, 0, 0, 0.12);
            }
        """)
        self.preview_btn.clicked.connect(self.toggle_preview)
        self.preview_btn.setToolTip("切换预览 (Ctrl+E)")
        top_bar_layout.addWidget(self.preview_btn)

        # 添加预览快捷键
        self.preview_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        self.preview_shortcut.activated.connect(self.toggle_preview)

        self.top_bar.setLayout(top_bar_layout)
        main_layout.addWidget(self.top_bar)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background-color: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 0, 0, 0.2);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(0, 0, 0, 0.4);
            }
            QScrollBar:horizontal {
                border: none;
                background-color: transparent;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(0, 0, 0, 0.2);
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(0, 0, 0, 0.3);
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: rgba(0, 0, 0, 0.4);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
            }
        """)

        # 创建内容容器
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {self.bg_color};")
        
        # 创建内容布局
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(4)  # 减小间距
        
        # 创建编辑器
        self.text_edit = MarkdownEditor()
        content_layout.addWidget(self.text_edit)
        
        # 创建待办事项容器
        self.todo_container = QWidget()
        self.todo_layout = QVBoxLayout(self.todo_container)
        self.todo_layout.setContentsMargins(0, 0, 0, 0)
        self.todo_layout.setSpacing(2)  # 减小待办事项之间的间距
        content_layout.addWidget(self.todo_container)
        
        # 设置滚动区域的内容
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)
        
        self.setLayout(main_layout)
        
        # 连接信号
        self.text_edit.textChanged.connect(self.handle_content_changed)
        
        # 先设置自动保存计时器
        self.setup_auto_save_timer()
        # 再加载设置，避免加载时触发保存
        self.load_settings()
        
        # 更新文本样式
        self.update_text_style()

    def get_resize_cursor(self, pos):
        x = pos.x()
        y = pos.y()
        width = self.width()
        height = self.height()

        # 顶部栏区域显示默认光标
        if y < 40:  # 调整为顶部栏实际高度
            return Qt.ArrowCursor

        # 边界区域的判断
        in_right_border = x > width - self.resize_margin
        in_bottom_border = y > height - self.resize_margin
        in_corner = x > width - self.corner_size and y > height - self.corner_size

        # 右下角区域
        if in_corner:
            return Qt.SizeFDiagCursor

        # 右边界区域
        if in_right_border:
            return Qt.SizeHorCursor

        # 下边界区域
        if in_bottom_border:
            return Qt.SizeVerCursor

        # 非边界区域显示默认光标
        return Qt.ArrowCursor

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 如果便签已固定，只允许点击按钮和编辑文本，不允许移动和调整大小
            if self.is_position_fixed:
                event.accept()
                return

            # 如果点击在顶部栏，处理窗口移动
            if event.pos().y() < 40:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                self.is_resizing = False
                self.is_dragging = True
                self.setCursor(Qt.SizeAllCursor)
                event.accept()
                return

            # 如果点击在调整区域，开始调整大小
            if self.get_resize_cursor(event.pos()) != Qt.ArrowCursor:
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                self.is_resizing = True
                self.is_dragging = False
                self.resize_cursor = self.get_resize_cursor(event.pos())
                self.last_pos = event.globalPos()
                event.accept()
                return

            # 检查是否点击在文本编辑区域内
            if self.text_edit.rect().contains(event.pos()):
                # 获取点击位置对应的文本位置
                cursor = self.text_edit.textCursor()
                cursor.movePosition(cursor.StartOfLine)
                line_text = cursor.block().text()
                
                # 检查是否点击了复选框
                if line_text.startswith("☐") or line_text.startswith("☑"):
                    # 获取当前行的起始位置
                    cursor.movePosition(cursor.StartOfLine)
                    cursor.movePosition(cursor.Right, cursor.KeepAnchor, 1)  # 选中复选框字符
                    self.text_edit.setTextCursor(cursor)
                    
                    # 切换复选框状态
                    if line_text.startswith("☐"):
                        self.text_edit.insertPlainText("☑")
                        # 设置选中文本的样式
                        format = self.text_edit.currentCharFormat()
                        format.setForeground(QColor("#007acc"))
                        self.text_edit.setCurrentCharFormat(format)
                    else:
                        self.text_edit.insertPlainText("☐")
                        # 设置选中文本的样式
                        format = self.text_edit.currentCharFormat()
                        format.setForeground(QColor("#333"))
                        self.text_edit.setCurrentCharFormat(format)
                    
                    # 将光标移动到行尾
                    cursor.movePosition(cursor.EndOfLine)
                    self.text_edit.setTextCursor(cursor)
                    event.accept()
                    return

            # 移除其他区域的移动功能
            event.accept()

    def mouseMoveEvent(self, event):
        # 如果便签已固定，不允许移动和调整大小
        if self.is_position_fixed:
            # 仍然允许检查复选框的悬停效果
            if self.text_edit.rect().contains(event.pos()):
                cursor = self.text_edit.textCursor()
                cursor.movePosition(cursor.StartOfLine)
                line_text = cursor.block().text()
                if line_text.startswith("☐") or line_text.startswith("☑"):
                    self.setCursor(Qt.PointingHandCursor)
                    event.accept()
                    return
            self.setCursor(Qt.ArrowCursor)
            return

        if event.buttons() == Qt.LeftButton:
            if self.is_resizing:
                # 调整大小
                current_pos = event.globalPos()
                if self.last_pos is None:
                    self.last_pos = current_pos
                    return
                
                # 计算实际移动距离
                delta = current_pos - self.last_pos
                new_geometry = self.geometry()
                
                if self.resize_cursor == Qt.SizeHorCursor:  # 右边界
                    new_width = min(self.maximumWidth(),
                                  max(self.minimumWidth(), 
                                      new_geometry.width() + delta.x()))
                    new_geometry.setWidth(new_width)
                elif self.resize_cursor == Qt.SizeVerCursor:  # 下边界
                    new_height = min(self.maximumHeight(),
                                   max(self.minimumHeight(), 
                                       new_geometry.height() + delta.y()))
                    new_geometry.setHeight(new_height)
                elif self.resize_cursor == Qt.SizeFDiagCursor:  # 右下角
                    new_width = min(self.maximumWidth(),
                                  max(self.minimumWidth(), 
                                      new_geometry.width() + delta.x()))
                    new_height = min(self.maximumHeight(),
                                   max(self.minimumHeight(), 
                                       new_geometry.height() + delta.y()))
                    new_geometry.setWidth(new_width)
                    new_geometry.setHeight(new_height)
                
                self.setGeometry(new_geometry)
                self.last_pos = current_pos
            elif self.is_dragging:
                # 移动窗口
                self.move(event.globalPos() - self.drag_pos)
        
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 重置所有状态
            self.is_resizing = False
            self.is_dragging = False
            self.resize_cursor = None
            self.resize_start_pos = None
            self.resize_start_geometry = None
            self.drag_pos = None
            self.last_pos = None
            
            # 恢复默认指针
            self.setCursor(Qt.ArrowCursor)
            
            event.accept()

    def show_custom_menu(self, pos):
        menu = QMenu(self)
        add_todo_action = QAction("添加待办项", self)
        add_todo_action.triggered.connect(self.insert_todo_item)
        menu.addAction(add_todo_action)
        menu.exec_(self.text_edit.mapToGlobal(pos))

    def insert_todo_item(self):
        """插入待办事项"""
        todo_item = TodoItem(self.todo_container)
        todo_item.delete_btn.clicked.connect(lambda: self.handle_todo_changed())
        todo_item.checkbox.stateChanged.connect(lambda: self.handle_todo_changed())
        todo_item.text_edit.textChanged.connect(lambda: self.handle_todo_changed())
        self.todo_layout.addWidget(todo_item)
        todo_item.text_edit.setFocus()
        self.handle_todo_changed()

    def update_text_style(self):
        # 更新所有组件的背景色
        self.content_widget.setStyleSheet(f"background-color: {self.bg_color};")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: none;
                padding: 12px;
                color: #333;
                border-radius: 0px;
                background-color: {self.bg_color};
            }}
            
            /* Markdown 样式 */
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1em;
                margin-bottom: 0.5em;
                color: #2c3e50;
            }}
            h1 {{ font-size: 2em; }}
            h2 {{ font-size: 1.5em; }}
            h3 {{ font-size: 1.17em; }}
            code {{
                background-color: #f6f8fa;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, monospace;
            }}
            pre {{
                background-color: #f6f8fa;
                padding: 1em;
                border-radius: 5px;
                overflow-x: auto;
            }}
            blockquote {{
                border-left: 4px solid #dfe2e5;
                margin: 0;
                padding-left: 1em;
                color: #6a737d;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            th, td {{
                border: 1px solid #dfe2e5;
                padding: 6px 13px;
            }}
            th {{
                background-color: #f6f8fa;
            }}
        """)
        
        # 更新顶部栏的背景色
        if hasattr(self, 'top_bar'):
            self.top_bar.setStyleSheet(f"""
                QWidget {{
                    background-color: {self.bg_color};
                    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }}
            """)
        
        # 更新待办事项容器的背景色
        self.todo_container.setStyleSheet(f"background-color: {self.bg_color};")

    def change_bg_color(self):
        color = QColorDialog.getColor(QColor(self.bg_color), self, "选择背景颜色")
        if color.isValid():
            self.bg_color = color.name()
            self.settings.setValue("bg_color", self.bg_color)
            self.update_text_style()

    def closeEvent(self, event):
        # 确保关闭前保存
        if self.is_modified:
            self.save_content()
        event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                self.hide()
        super().changeEvent(event)

    def load_settings(self):
        """加载设置"""
        try:
            # 加载文本内容
            text_content = self.settings.value('text_content', '')
            if text_content:
                self.text_edit.setPlainText(text_content)
            
            # 加载待办事项
            todo_items = self.settings.value('todo_items', [])
            if todo_items:
                for item in todo_items:
                    todo_item = TodoItem(self.todo_container)
                    todo_item.checkbox.setChecked(item.get('checked', False))
                    todo_item.text_edit.setText(item.get('text', ''))
                    self.todo_layout.addWidget(todo_item)
            
            # 加载位置和其他设置
            if self.is_position_fixed:
                pos = self.settings.value('pos', QPoint(100 + 30 * self.id, 100 + 30 * self.id))
            else:
                pos = self.settings.value('pos', QPoint(100 + 30 * self.id, 100 + 30 * self.id))
            
            size = self.settings.value('size', self.default_size)
            if isinstance(size, str) or not size:
                size = self.default_size
            
            self.move(pos)
            self.resize(size)
            self.bg_color = self.settings.value('bg_color', self.bg_color)
            self.is_position_fixed = self.settings.value('is_position_fixed', False, type=bool)
            
            self.update_text_style()
            
            # 重置修改状态
            self.is_modified = False
            self.update_title()
            
            # 打印调试信息
            print(f"加载成功 - 便签 {self.id}")
            print(f"加载路径: {self.settings.fileName()}")
            print(f"文本内容长度: {len(text_content)}")
            print(f"待办事项数量: {len(todo_items)}")
        except Exception as e:
            print(f"加载失败 - 便签 {self.id}: {str(e)}")

    def adjust_size(self):
        pass

    def toggle_position_fixed(self):
        self.is_position_fixed = self.pin_btn.isChecked()
        self.settings.setValue("is_position_fixed", self.is_position_fixed)
        self.update_pin_button_text()  # 更新按钮文本

    def update_pin_button_text(self):
        # 根据固定状态更新按钮文本和提示
        if self.is_position_fixed:
            self.pin_btn.setText("📍")  # 使用不同的图标表示已固定
            self.pin_btn.setToolTip("已固定位置 (点击解除固定)")
        else:
            self.pin_btn.setText("📌")  # 使用原始图标表示未固定
            self.pin_btn.setToolTip("点击固定位置")

    def handle_content_changed(self):
        """处理内容变化"""
        if not self.is_modified:
            self.is_modified = True
            self.update_title()
        
        # 重置自动保存计时器
        if self.auto_save_timer:
            self.auto_save_timer.stop()
            self.auto_save_timer.start(3000)  # 3秒后自动保存

    def setup_auto_save_timer(self):
        self.auto_save_timer = QTimer()
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.save_content)

    def update_title(self):
        if self.is_modified:
            self.save_status.setText("●")
            self.save_status.setStyleSheet("""
                QLabel {
                    color: #007acc;
                    font-size: 18px;
                }
            """)
            # 添加提示文本
            self.save_status.setToolTip("有未保存的更改 (Ctrl+S 保存)")
        else:
            self.save_status.setText("")
            self.save_status.setToolTip("")

    def save_content(self):
        """保存便签内容"""
        try:
            settings_dict = {}
            
            # 保存文本内容
            text_content = self.text_edit.toPlainText()
            settings_dict['text_content'] = text_content
            
            # 保存待办事项列表
            todo_items = []
            for i in range(self.todo_layout.count()):
                widget = self.todo_layout.itemAt(i).widget()
                if isinstance(widget, TodoItem):
                    todo_text = widget.text_edit.text().strip()
                    if todo_text:  # 只保存非空的待办事项
                        todo_items.append({
                            'text': todo_text,
                            'checked': widget.checkbox.isChecked()
                        })
            settings_dict['todo_items'] = todo_items
            
            # 保存位置和大小
            if not self.is_position_fixed:
                settings_dict['pos'] = self.pos()
            settings_dict['size'] = self.size()
            settings_dict['bg_color'] = self.bg_color
            settings_dict['is_position_fixed'] = self.is_position_fixed
            
            # 保存所有设置
            for key, value in settings_dict.items():
                self.settings.setValue(key, value)
            
            # 强制同步设置
            self.settings.sync()
            
            self.is_modified = False
            self.update_title()
            
            # 打印调试信息
            print(f"保存成功 - 便签 {self.id}")
            print(f"保存路径: {self.settings.fileName()}")
            print(f"文本内容长度: {len(text_content)}")
            print(f"待办事项数量: {len(todo_items)}")
        except Exception as e:
            print(f"保存失败 - 便签 {self.id}: {str(e)}")

    def manual_save(self):
        """手动保存内容"""
        self.save_content()
        # 显示保存成功提示
        original_text = self.save_status.text()
        original_style = self.save_status.styleSheet()
        
        self.save_status.setText("已保存")
        self.save_status.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 18px;
            }
        """)
        
        # 2秒后恢复原始状态
        QTimer.singleShot(2000, lambda: self.restore_save_status(original_text, original_style))

    def restore_save_status(self, text, style):
        """恢复保存状态显示"""
        self.save_status.setText(text)
        self.save_status.setStyleSheet(style)

    def toggle_preview(self):
        """切换预览模式"""
        self.text_edit.toggle_preview()
        if self.text_edit.is_preview_mode:
            self.preview_btn.setText("✎")  # 切换为编辑图标
            self.preview_btn.setToolTip("切换编辑 (Ctrl+E)")
        else:
            self.preview_btn.setText("👁")  # 切换为预览图标
            self.preview_btn.setToolTip("切换预览 (Ctrl+E)")

    def handle_todo_changed(self):
        """处理待办事项变化"""
        self.handle_content_changed()

    def update_save_path(self, new_path):
        """更新保存路径"""
        try:
            # 保存当前内容
            current_content = {}
            for key in self.settings.allKeys():
                current_content[key] = self.settings.value(key)
            
            # 创建新的设置对象
            new_settings = QSettings(
                os.path.join(new_path, f"DesktopNote{self.id}.ini"),
                QSettings.IniFormat
            )
            new_settings.setFallbacksEnabled(False)
            
            # 转移所有设置到新路径
            for key, value in current_content.items():
                new_settings.setValue(key, value)
            
            # 更新设置对象
            self.settings = new_settings
            
            print(f"便签 {self.id} 的保存路径已更新到: {new_path}")
        except Exception as e:
            print(f"更新便签 {self.id} 的保存路径时出错: {str(e)}")

class SettingsDialog(QDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("设置")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        # 开机启动设置
        self.autostart_checkbox = QCheckBox("开机启动", self)
        self.autostart_checkbox.setChecked(self.is_autostart_enabled())
        layout.addWidget(self.autostart_checkbox)

        # 数据保存路径设置
        path_group = QWidget()
        path_layout = QHBoxLayout(path_group)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        path_label = QLabel("数据保存路径：")
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.get_current_save_path())
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_save_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_edit, 1)
        path_layout.addWidget(browse_btn)
        
        layout.addWidget(path_group)

        # 添加说明文本
        note_label = QLabel("注意：更改保存路径后，现有的便签数据将被移动到新路径")
        note_label.setStyleSheet("color: #666; font-size: 10pt;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)

        layout.addStretch()

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_current_save_path(self):
        """获取当前保存路径"""
        settings = QSettings("MyCompany", "StickyNoteApp")
        default_path = os.path.join(os.path.expanduser("~"), "StickyNotes")
        return settings.value("save_path", default_path)

    def browse_save_path(self):
        """浏览并选择新的保存路径"""
        current_path = self.path_edit.text()
        new_path = QFileDialog.getExistingDirectory(
            self,
            "选择保存路径",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if new_path:
            self.path_edit.setText(new_path)

    def move_data_to_new_path(self, old_path, new_path):
        """移动数据到新路径"""
        try:
            # 确保新路径存在
            os.makedirs(new_path, exist_ok=True)
            
            # 获取所有便签数据文件
            if os.path.exists(old_path):
                for filename in os.listdir(old_path):
                    if filename.startswith("DesktopNote"):
                        old_file = os.path.join(old_path, filename)
                        new_file = os.path.join(new_path, filename)
                        # 移动文件
                        if os.path.exists(old_file):
                            shutil.move(old_file, new_file)
            
            return True
        except Exception as e:
            print(f"移动数据失败: {str(e)}")
            return False

    def save(self):
        # 保存开机启动设置
        self.set_autostart(self.autostart_checkbox.isChecked())
        
        # 保存路径设置
        new_path = self.path_edit.text()
        settings = QSettings("MyCompany", "StickyNoteApp")
        old_path = settings.value("save_path", os.path.join(os.path.expanduser("~"), "StickyNotes"))
        
        if new_path != old_path:
            # 询问用户是否确认更改
            reply = QMessageBox.question(
                self,
                "确认更改",
                "更改保存路径将移动所有便签数据到新位置，是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 移动数据
                if self.move_data_to_new_path(old_path, new_path):
                    settings.setValue("save_path", new_path)
                    # 更新所有便签的保存路径
                    for note in self.app.notes:
                        note.update_save_path(new_path)
                    QMessageBox.information(self, "成功", "保存路径已更改，数据已移动到新位置")
                else:
                    QMessageBox.warning(self, "错误", "移动数据失败，保存路径未更改")
                    return
        
        self.accept()

    def is_autostart_enabled(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            try:
                value, _ = winreg.QueryValueEx(key, "StickyNote")
                winreg.CloseKey(key)
                return True
            except WindowsError:
                winreg.CloseKey(key)
                return False
        except WindowsError:
            return False

    def set_autostart(self, enable):
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        try:
            if enable:
                # 获取当前程序的路径
                app_path = sys.executable
                if hasattr(sys, '_MEIPASS'):  # 如果是打包后的程序
                    app_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(
                    key,
                    "StickyNote",
                    0,
                    winreg.REG_SZ,
                    f'"{app_path}"'
                )
            else:
                try:
                    winreg.DeleteValue(key, "StickyNote")
                except WindowsError:
                    pass
        finally:
            winreg.CloseKey(key)

class StickyNoteApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.notes = []
        
        # 设置默认的便签大小
        self.default_note_size = QSize(450, 600)
        
        # 创建一个隐藏的窗口作为系统托盘菜单的父窗口
        self.tray_menu_host = QWidget()
        self.tray_menu_host.hide()

        icon_path = resource_path("sticky_note_icon.ico")
        icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon(icon, self.tray_menu_host)
        self.setWindowIcon(icon)
        self.tray.setVisible(True)
        self.menu = QMenu(self.tray_menu_host)

        new_action = QAction("新建便签", self.tray_menu_host)
        new_action.triggered.connect(self.create_note)
        self.menu.addAction(new_action)

        restore_action = QAction("显示所有便签", self.tray_menu_host)
        restore_action.triggered.connect(self.show_all_notes)
        self.menu.addAction(restore_action)

        hide_action = QAction("隐藏所有便签", self.tray_menu_host)
        hide_action.triggered.connect(self.hide_all_notes)
        self.menu.addAction(hide_action)

        self.menu.addSeparator()

        setting_action = QAction("设置", self.tray_menu_host)
        setting_action.triggered.connect(self.show_settings)
        self.menu.addAction(setting_action)

        quit_action = QAction("退出", self.tray_menu_host)
        quit_action.triggered.connect(self.quit_app)  # 修改为自定义的退出函数
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("桌面便签")
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

        self.notes_visible = True
        self.create_note()

    def create_note(self):
        global note_counter
        note = StickyNote(note_counter)
        # 强制设置初始大小
        note.resize(self.default_note_size)
        note.setWindowIcon(QIcon(resource_path("sticky_note_icon.ico")))
        note.show()
        self.notes.append(note)
        note_counter += 1

    def show_all_notes(self):
        for note in self.notes:
            note.showNormal()
            note.activateWindow()
        self.notes_visible = True

    def hide_all_notes(self):
        for note in self.notes:
            note.hide()
        self.notes_visible = False

    def toggle_notes_visibility(self):
        if self.notes_visible:
            self.hide_all_notes()
        else:
            self.show_all_notes()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_notes_visibility()
        elif reason == QSystemTrayIcon.Context:
            self.menu.popup(QCursor.pos())

    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

    def quit_app(self):
        """自定义退出函数，确保保存所有便签内容"""
        try:
            # 保存所有便签的内容
            for note in self.notes:
                if note.is_modified:
                    note.save_content()
            print("所有便签内容已保存")
        except Exception as e:
            print(f"保存便签内容时出错: {str(e)}")
        finally:
            self.quit()

if __name__ == '__main__':
    # 检查是否已有实例在运行
    instance_checker = SingleInstanceChecker()
    if instance_checker.is_another_instance_running():
        # 如果已经有实例在运行，显示提示消息并退出
        app = QApplication(sys.argv)
        QMessageBox.information(None, "提示", "便签程序已经在运行中")
        sys.exit(0)
    else:
        # 如果是第一个实例，正常运行程序
        app = StickyNoteApp(sys.argv)
        sys.exit(app.exec_())
