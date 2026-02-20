"""
Theme support for DXCom GUI application.
Provides light and dark theme stylesheets.
"""


LIGHT_THEME = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    background-color: #ffffff;
    color: #000000;
}

QLabel#header_title {
    color: #000000;
}

QLabel#header_subtitle {
    color: #666666;
}

QLabel#logo_text {
    font-size: 24pt;
    font-weight: bold;
    color: #00a8ff;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #cccccc;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QLineEdit, QTextEdit {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 4px;
    color: #000000;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0078d4;
}

QLineEdit:disabled {
    background-color: #f0f0f0;
    color: #999999;
}

QComboBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 4px;
    color: #000000;
}

QComboBox:hover {
    border: 1px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
}

QCheckBox {
    spacing: 5px;
    color: #000000;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #cccccc;
    border-radius: 3px;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border: 1px solid #0078d4;
}

QMenuBar {
    background-color: #f5f5f5;
    color: #000000;
}

QMenuBar::item:selected {
    background-color: #e5e5e5;
}

QMenu {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    color: #000000;
}

QMenu::item:selected {
    background-color: #e5f3ff;
}

QProgressBar {
    border: 1px solid #cccccc;
    border-radius: 3px;
    text-align: center;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 2px;
}

QStatusBar {
    background-color: #f5f5f5;
    color: #000000;
}

"""


DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QLabel#header_title {
    color: #ffffff;
}

QLabel#header_subtitle {
    color: #aaaaaa;
}

QLabel#logo_text {
    font-size: 24pt;
    font-weight: bold;
    color: #00a8ff;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #3f3f3f;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
    color: #e0e0e0;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 3px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #3f3f3f;
    color: #808080;
}

QLineEdit, QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3f3f3f;
    border-radius: 3px;
    padding: 4px;
    color: #e0e0e0;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0078d4;
}

QLineEdit:disabled {
    background-color: #252525;
    color: #606060;
}

QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #3f3f3f;
    border-radius: 3px;
    padding: 4px;
    color: #e0e0e0;
}

QComboBox:hover {
    border: 1px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #e0e0e0;
    selection-background-color: #0078d4;
}

QCheckBox {
    spacing: 5px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3f3f3f;
    border-radius: 3px;
    background-color: #1e1e1e;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border: 1px solid #0078d4;
}

QMenuBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QMenuBar::item:selected {
    background-color: #3f3f3f;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #3f3f3f;
    color: #e0e0e0;
}

QMenu::item:selected {
    background-color: #0078d4;
}

QProgressBar {
    border: 1px solid #3f3f3f;
    border-radius: 3px;
    text-align: center;
    background-color: #1e1e1e;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 2px;
}

QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QLabel {
    color: #e0e0e0;
}

QDialog {
    background-color: #2d2d2d;
    color: #e0e0e0;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
}

QSpinBox {
    background-color: #1e1e1e;
    border: 1px solid #3f3f3f;
    border-radius: 3px;
    padding: 4px;
    color: #e0e0e0;
}

QSpinBox:focus {
    border: 1px solid #0078d4;
}
"""


def get_theme_stylesheet(theme: str) -> str:
    """Get stylesheet for the specified theme.
    
    Args:
        theme: Theme name ('light' or 'dark')
        
    Returns:
        Theme stylesheet string
    """
    if theme.lower() == 'dark':
        return DARK_THEME
    return LIGHT_THEME
