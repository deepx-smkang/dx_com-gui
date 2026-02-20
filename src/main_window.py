"""
Main window for DXCom GUI application.
"""
import os
import json
import time
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QSplitter, QMessageBox,
    QLineEdit, QFileDialog, QCheckBox, QComboBox, QGridLayout, QTextEdit,
    QProgressBar, QTabWidget, QRadioButton, QButtonGroup, QSpinBox, QFormLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QAction, QTextCursor, QTextCharFormat, QColor, QKeySequence, QPixmap
from enum import Enum
from .dxcom_detector import check_dxcom_available, get_dxcom_status
from .environment_validator import validate_environment, validate_for_compilation
from .dxcom_wrapper import DXComWrapper
from .settings_manager import SettingsManager
from .settings_dialog import SettingsDialog
from .themes import get_theme_stylesheet
from .python_script_dialog import PythonScriptDialog


class CompilationStatus(Enum):
    """Enumeration of compilation states."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MainWindow(QMainWindow):
    """Main application window for DXCom GUI."""
    
    VERSION = "0.1.0"
    COMPANY = "DEEPX"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DXCom GUI - ONNX to DXNN Compiler")
        self.setMinimumSize(900, 1400)  # Increased height for all sections

        # Set initial size to fit within available screen height
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        initial_height = min(1600, available.height() - 50)
        self.resize(1050, initial_height)
        
        # Settings manager
        self.settings_manager = SettingsManager()
        
        # State variables
        self.input_model_path = ""
        self.output_model_path = ""
        self.config_file_path = ""

        # Default loader widget references
        self.default_loader_group = None
        self.dataset_path_field = None
        self.file_extensions_field = None
        self.convert_color_combo = None
        self.resize_field = None
        self.centercrop_field = None
        self.transpose_field = None
        self.expand_dim_field = None
        self.normalize_field = None
        self.mul_field = None
        self.add_field = None
        self.subtract_field = None
        self.div_field = None
        
        # Set default browse directory - prefer settings default, then common locations
        default_model_dirs = [
            os.path.expanduser("~/workspace/onnx/"),
            os.path.expanduser("~/models"),
            os.path.expanduser("~")
        ]
        self.last_browse_directory = os.path.expanduser("~")
        for directory in default_model_dirs:
            if os.path.isdir(directory):
                self.last_browse_directory = directory
                break
        # Override with user-configured default input path from settings
        _default_input = self.settings_manager.get('default_input_path', '')
        if _default_input and os.path.isdir(_default_input):
            self.last_browse_directory = _default_input
        
        # Batch processing
        self.batch_mode = False
        self.batch_files = []
        
        # Compiler option widgets (to be created in _create_compiler_options)
        self.config_path_field = None
        self.browse_config_button = None
        self.edit_config_button = None
        self.gen_log_checkbox = None
        self.aggressive_partitioning_checkbox = None
        self.compile_input_nodes_field = None
        self.compile_output_nodes_field = None
        self.opt_level_combo = None
        
        # Execution mode (CLI or Python)
        self.execution_mode = "python"  # "cli" or "python" - default to python since it's the first tab
        self.python_mode_btn = None
        self.cli_mode_btn = None
        
        # Header separator (for theme updates)
        self.header_separator = None
        
        # Logo label (for theme updates if using text fallback)
        self.logo_label = None
        
        # Toggle button group container (for theme updates)
        self.mode_btn_container = None
        
        # Python mode: config vs dataloader
        self.python_data_source = "config"  # "config" or "dataloader"
        self.config_radio = None
        self.dataloader_radio = None
        self.python_data_source_group = None
        self.data_src_btn_container = None
        self.config_src_btn = None
        self.dataloader_src_btn = None
        
        # Saved Python script path (for reusing user-edited scripts)
        self.saved_python_script_path = None
        
        # Validation state
        self.validation_errors = {}
        
        # Compilation status tracking
        self.compilation_status = CompilationStatus.IDLE
        
        # Compile button reference (set in _setup_ui)
        self.compile_button = None
        
        # Cancel button reference (set in _setup_ui)
        self.cancel_button = None
        
        # Status label for compilation state
        self.status_label = None
        
        # DXCom availability
        self.dxcom_available = False
        
        # DXCom wrapper and executor for compilation
        self.dxcom_wrapper = DXComWrapper()
        self.current_executor = None
        self.compilation_start_time = None  # Track compilation duration
        
        # Log text area (set in _create_log_viewer)
        self.log_text_area = None
        
        # Progress bar (set in _create_log_viewer)
        self.progress_bar = None
        
        # Always start with light theme regardless of saved settings
        current_theme = 'light'
        self.settings_manager.set('theme', 'light')
        self.apply_theme(current_theme)
        
        self._set_window_icon()
        self._create_menu_bar()
        self._setup_ui()
        self._setup_status_bar()
        self._check_dxcom_availability()
        
        # Re-apply theme AFTER creating UI to ensure all widgets are styled
        self.apply_theme(current_theme)
        
        # Defer one more tab style refresh to after the event loop starts,
        # so Qt's initial repaint cycle doesn't override the container stylesheet
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._update_tab_styles(current_theme))
        
        # Initialize status label to IDLE
        self._set_compilation_status(CompilationStatus.IDLE)
    
    def _set_window_icon(self):
        """Set the application window icon with multiple sizes."""
        from PySide6.QtGui import QIcon
        
        icon = QIcon()
        icon_sizes = ['deepx_16.png', 'deepx_32.png', 'deepx_64.png', 'deepx_128.png']
        
        # Icons live in src/resources/ (installed as src.resources package data)
        base_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'),
        ]
        
        for base_path in base_paths:
            for icon_file in icon_sizes:
                icon_path = os.path.join(base_path, icon_file)
                if os.path.exists(icon_path):
                    icon.addFile(icon_path)
            
            if not icon.isNull():
                self.setWindowIcon(icon)
                return
    
    def _create_header(self):
        """Create the header section with logo and title."""
        from PySide6.QtGui import QPixmap
        
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(15)
        
        # Load and display DEEPX logo
        self.logo_label = QLabel()
        
        # Try to find logo
        logo_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'deepx.png'),
        ]
        
        logo_loaded = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                # Scale logo to reasonable size while maintaining aspect ratio
                scaled_pixmap = pixmap.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
                self.logo_label.setPixmap(scaled_pixmap)
                logo_loaded = True
                break
        
        if not logo_loaded:
            # Fallback if logo not found - use text
            self.logo_label.setText("DEEPX")
            self.logo_label.setObjectName("logo_text")
            # Style will be set by theme
        
        header_layout.addWidget(self.logo_label)
        
        # Title text (without hardcoded color - will use theme color)
        title_label = QLabel("DXCom GUI")
        title_label.setStyleSheet("""
            font-size: 24pt;
            font-weight: bold;
        """)
        title_label.setObjectName("header_title")
        header_layout.addWidget(title_label)
        
        # Subtitle (without hardcoded color - will use theme color)
        subtitle_label = QLabel("ONNX to DXNN Compiler Interface")
        subtitle_label.setStyleSheet("""
            font-size: 10pt;
            margin-top: 8px;
        """)
        subtitle_label.setObjectName("header_subtitle")
        header_layout.addWidget(subtitle_label, 0, Qt.AlignmentFlag.AlignBottom)
        
        header_layout.addStretch()
        
        # Add separator line
        self.header_separator = QWidget()
        self.header_separator.setFixedHeight(2)
        self.header_separator.setStyleSheet("background: transparent; border: none;")
        # Separator visibility and color will be set by theme
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)
        container_layout.addWidget(header_widget)
        container_layout.addWidget(self.header_separator)
        
        return container
    
    def _create_mode_selector(self):
        """Create the execution mode selector (CLI vs Python) as a toggle button group."""
        mode_widget = QWidget()
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setContentsMargins(10, 0, 10, 5)
        mode_layout.setSpacing(6)

        # ── Row 1: Execution Mode ──────────────────────────────────
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)

        mode_label = QLabel("Execution Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        row1_layout.addWidget(mode_label)

        # Toggle button group container
        self.mode_btn_container = QWidget()
        self.mode_btn_container.setObjectName("modeBtnContainer")
        btn_layout = QHBoxLayout(self.mode_btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(0)

        # Python mode button (left)
        self.python_mode_btn = QPushButton("Python (dx_com.compile)")
        self.python_mode_btn.setObjectName("modeToggleLeft")
        self.python_mode_btn.setCheckable(True)
        self.python_mode_btn.setChecked(True)  # Default: Python selected
        self.python_mode_btn.setFixedHeight(32)
        self.python_mode_btn.clicked.connect(lambda: self._on_mode_changed(0))
        btn_layout.addWidget(self.python_mode_btn)

        # CLI mode button (right)
        self.cli_mode_btn = QPushButton("CLI (dxcom)")
        self.cli_mode_btn.setObjectName("modeToggleRight")
        self.cli_mode_btn.setCheckable(True)
        self.cli_mode_btn.setChecked(False)
        self.cli_mode_btn.setFixedHeight(32)
        self.cli_mode_btn.clicked.connect(lambda: self._on_mode_changed(1))
        btn_layout.addWidget(self.cli_mode_btn)

        row1_layout.addWidget(self.mode_btn_container)
        row1_layout.addStretch()
        mode_layout.addWidget(row1)

        # ── Row 2: Data Source (Python mode only) ──────────────────
        self.python_data_source_group = QWidget()
        row2_layout = QHBoxLayout(self.python_data_source_group)
        row2_layout.setContentsMargins(0, 0, 0, 0)

        ds_label = QLabel("Data Source:")
        ds_label.setStyleSheet("font-weight: bold;")
        row2_layout.addWidget(ds_label)

        self.data_src_btn_container = QWidget()
        self.data_src_btn_container.setObjectName("dataSrcBtnContainer")
        ds_btn_layout = QHBoxLayout(self.data_src_btn_container)
        ds_btn_layout.setContentsMargins(0, 0, 0, 0)
        ds_btn_layout.setSpacing(0)

        self.config_src_btn = QPushButton("Config File")
        self.config_src_btn.setObjectName("dataToggleLeft")
        self.config_src_btn.setCheckable(True)
        self.config_src_btn.setChecked(True)
        self.config_src_btn.setFixedHeight(32)
        self.config_src_btn.clicked.connect(lambda: self._on_data_source_btn_changed(0))
        ds_btn_layout.addWidget(self.config_src_btn)

        self.dataloader_src_btn = QPushButton("PyTorch DataLoader")
        self.dataloader_src_btn.setObjectName("dataToggleRight")
        self.dataloader_src_btn.setCheckable(True)
        self.dataloader_src_btn.setChecked(False)
        self.dataloader_src_btn.setFixedHeight(32)
        self.dataloader_src_btn.clicked.connect(lambda: self._on_data_source_btn_changed(1))
        ds_btn_layout.addWidget(self.dataloader_src_btn)

        row2_layout.addWidget(self.data_src_btn_container)
        row2_layout.addStretch()
        self.python_data_source_group.setVisible(False)  # Hidden until Python mode
        mode_layout.addWidget(self.python_data_source_group)

        # Apply initial styles based on current theme
        current_theme = self.settings_manager.get('theme', 'light')
        self._update_tab_styles(current_theme)

        return mode_widget
    
    def _on_mode_changed(self, index):
        """Handle execution mode change."""
        # Update button checked states
        if hasattr(self, 'python_mode_btn') and self.python_mode_btn is not None:
            self.python_mode_btn.setChecked(index == 0)
            self.cli_mode_btn.setChecked(index == 1)
        
        if index == 0:
            # Tab 0: Python mode
            self.execution_mode = "python"
            self.set_status_message("Execution mode: Python (dx_com.compile)", 2000)
            # Show Python-specific options
            if self.python_data_source_group:
                self.python_data_source_group.setVisible(True)
            if hasattr(self, 'python_calib_method_label'):
                self.python_calib_method_label.setVisible(True)
            if hasattr(self, 'python_calib_method_group'):
                self.python_calib_method_group.setVisible(True)
            if hasattr(self, 'python_calib_num_label'):
                self.python_calib_num_label.setVisible(True)
            if hasattr(self, 'python_calib_num_group'):
                self.python_calib_num_group.setVisible(True)
            if hasattr(self, 'python_quant_device_label'):
                self.python_quant_device_label.setVisible(True)
            if hasattr(self, 'python_quant_device_group'):
                self.python_quant_device_group.setVisible(True)
            if hasattr(self, 'python_enhanced_scheme_label'):
                self.python_enhanced_scheme_label.setVisible(True)
            if hasattr(self, 'python_enhanced_scheme_group'):
                self.python_enhanced_scheme_group.setVisible(True)
            # Show Generate Python Script button
            if hasattr(self, 'gen_python_button'):
                self.gen_python_button.setVisible(True)
        else:
            # Tab 1: CLI mode
            self.execution_mode = "cli"
            self.set_status_message("Execution mode: CLI (dxcom command)", 2000)
            # Hide Python-specific options
            if self.python_data_source_group:
                self.python_data_source_group.setVisible(False)
            if hasattr(self, 'python_quant_device_label'):
                self.python_quant_device_label.setVisible(False)
            if hasattr(self, 'python_quant_device_group'):
                self.python_quant_device_group.setVisible(False)
            if hasattr(self, 'python_enhanced_scheme_label'):
                self.python_enhanced_scheme_label.setVisible(False)
            if hasattr(self, 'python_enhanced_scheme_group'):
                self.python_enhanced_scheme_group.setVisible(False)
            # Hide Generate Python Script button in CLI mode
            if hasattr(self, 'gen_python_button'):
                self.gen_python_button.setVisible(False)
                self.python_enhanced_scheme_group.setVisible(False)
        
        # Update config field enable/disable based on data source
        self._update_config_field_state()
        
        # Update command preview
        self._update_command_preview()
        
        # Update button states
        self._update_compile_button_state()
    
    def _on_data_source_btn_changed(self, index):
        """Handle data source toggle button change."""
        if hasattr(self, 'config_src_btn'):
            self.config_src_btn.setChecked(index == 0)
            self.dataloader_src_btn.setChecked(index == 1)
        if index == 0:
            self.python_data_source = "config"
            self.set_status_message("Data source: Config file", 2000)
        else:
            self.python_data_source = "dataloader"
            self.set_status_message("Data source: PyTorch DataLoader", 2000)
        self._update_config_field_state()
        self._update_command_preview()
        self._update_compile_button_state()

    def _on_data_source_changed(self):
        """Handle data source change (config vs dataloader) — legacy radio path."""
        if self.config_src_btn and self.config_src_btn.isChecked():
            self.python_data_source = "config"
            self.set_status_message("Data source: Config file", 2000)
        else:
            self.python_data_source = "dataloader"
            self.set_status_message("Data source: PyTorch DataLoader", 2000)
        
        # Update config field enable/disable
        self._update_config_field_state()
        
        # Update command preview
        self._update_command_preview()
        
        # Update button states
        self._update_compile_button_state()
    
    def _update_config_field_state(self):
        """Enable/disable config file selection based on mode and data source."""
        if not self.config_path_field or not self.browse_config_button:
            return
        
        # In CLI mode or Python mode with config, enable config file selection
        # In Python mode with dataloader, disable config file selection
        if self.execution_mode == "python" and self.python_data_source == "dataloader":
            self.config_path_field.setEnabled(False)
            self.browse_config_button.setEnabled(False)
            self.edit_config_button.setEnabled(False)
            self.config_path_field.setPlaceholderText("PyTorch DataLoader will be used (config not needed)")
            if self.default_loader_group:
                self.default_loader_group.setVisible(False)
        else:
            self.config_path_field.setEnabled(True)
            self.browse_config_button.setEnabled(True)
            # Edit button enabled only if config file is loaded
            if self.config_file_path:
                self.edit_config_button.setEnabled(True)
            self.config_path_field.setPlaceholderText("Select configuration JSON file...")
            if self.default_loader_group:
                self.default_loader_group.setVisible(True)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # Open (with keyboard shortcut)
        open_action = QAction("&Open ONNX File...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._on_browse_input_file)
        file_menu.addAction(open_action)
        
        # Open JSON Config File
        open_json_action = QAction("Open &JSON Config...", self)
        open_json_action.setShortcut(QKeySequence("Ctrl+J"))
        open_json_action.triggered.connect(self._on_browse_config_file)
        file_menu.addAction(open_json_action)
        
        file_menu.addSeparator()
        
        # Recent Files submenu
        self.recent_files_menu = file_menu.addMenu("Recent Files")
        self._update_recent_files_menu()
        
        file_menu.addSeparator()
        
        # Exit (functional)
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Settings
        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._on_settings)
        edit_menu.addAction(settings_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Theme toggle
        self.theme_action = QAction("Switch to &Dark Theme", self)
        self.theme_action.setShortcut(QKeySequence("Ctrl+T"))
        self.theme_action.triggered.connect(self._on_toggle_theme)
        view_menu.addAction(self.theme_action)
        
        # Compilation Menu
        compile_menu = menubar.addMenu("&Compile")
        
        # Run Compilation
        run_compile_action = QAction("&Run Compilation", self)
        run_compile_action.setShortcut(QKeySequence("Ctrl+R"))
        run_compile_action.triggered.connect(self._on_compile_clicked)
        compile_menu.addAction(run_compile_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # Check DXCom Status
        check_dxcom_action = QAction("Check &DXCom Status", self)
        check_dxcom_action.triggered.connect(self._on_check_dxcom_status)
        help_menu.addAction(check_dxcom_action)
        
        # Keyboard Shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut(QKeySequence("F1"))
        shortcuts_action.triggered.connect(self._on_show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # About (functional)
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_ui(self):
        """Set up the user interface layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Fixed header (title + logo) — not scrollable
        header_widget = self._create_header()
        main_layout.addWidget(header_widget)

        # Fixed mode selector — not scrollable
        mode_selector = self._create_mode_selector()
        main_layout.addWidget(mode_selector)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section: Input/Output configuration and compiler options (scrollable)
        config_widget = self._create_configuration_section()
        config_scroll = QScrollArea()
        config_scroll.setWidget(config_widget)
        config_scroll.setWidgetResizable(True)
        config_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        config_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        splitter.addWidget(config_scroll)

        # Bottom section: Log viewer
        log_widget = self._create_log_section()
        splitter.addWidget(log_widget)

        # Set initial splitter sizes
        splitter.setSizes([1000, 300])
        
        main_layout.addWidget(splitter)
        
        # Button row at the bottom (Compile and Cancel)
        button_layout = QHBoxLayout()
        
        # Status label to show compilation state
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        button_layout.addWidget(self.status_label)
        
        button_layout.addStretch()
        
        # Cancel button (hidden initially)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setVisible(False)  # Hidden until compilation starts
        self.cancel_button.setToolTip("Cancel the running compilation")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        # Compile button
        self.compile_button = QPushButton("Compile")
        self.compile_button.setMinimumHeight(40)
        self.compile_button.setMinimumWidth(150)
        self.compile_button.setEnabled(False)  # Disabled until inputs are valid
        self.compile_button.setToolTip("Configure required inputs to enable compilation")
        self.compile_button.clicked.connect(self._on_compile_clicked)
        button_layout.addWidget(self.compile_button)
        
        # Generate Python Script button
        self.gen_python_button = QPushButton("Generate Python Script")
        self.gen_python_button.setMinimumHeight(40)
        self.gen_python_button.setMinimumWidth(180)
        self.gen_python_button.setEnabled(False)  # Disabled until inputs are valid
        self.gen_python_button.setToolTip("Generate a Python script using dx_com.compile() API")
        self.gen_python_button.clicked.connect(self._on_generate_python_script)
        button_layout.addWidget(self.gen_python_button)
        
        main_layout.addLayout(button_layout)
        
        # Command preview section
        command_preview_layout = self._create_command_preview()
        main_layout.addLayout(command_preview_layout)
    
    def _create_configuration_section(self):
        """Create the scrollable configuration section (groups only)."""
        config_container = QWidget()
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(10, 0, 10, 10)
        config_layout.setSpacing(0)
        
        # Input/Output file paths group
        io_group = QGroupBox("Input/Output Configuration")
        io_layout = QVBoxLayout()
        io_layout.setContentsMargins(12, 10, 12, 10)
        io_layout.setSpacing(8)
        
        # Input ONNX model file selection
        input_row = QHBoxLayout()
        input_label = QLabel("Input ONNX Model:")
        input_label.setMinimumWidth(130)
        
        self.input_path_field = QLineEdit()
        self.input_path_field.setPlaceholderText("Select an ONNX model file...")
        self.input_path_field.setReadOnly(True)
        self.input_path_field.textChanged.connect(self._on_input_path_changed)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setMaximumWidth(100)
        self.browse_button.clicked.connect(self._on_browse_input_file)
        
        input_row.addWidget(input_label)
        input_row.addWidget(self.input_path_field)
        input_row.addWidget(self.browse_button)
        io_layout.addLayout(input_row)
        
        # Output directory selection
        output_row = QHBoxLayout()
        output_label = QLabel("Output Directory:")
        output_label.setMinimumWidth(130)
        
        self.output_path_field = QLineEdit()
        self.output_path_field.setPlaceholderText("Select output directory...")
        self.output_path_field.textChanged.connect(self._on_output_path_changed)
        
        self.browse_output_button = QPushButton("Browse...")
        self.browse_output_button.setMaximumWidth(100)
        self.browse_output_button.clicked.connect(self._on_browse_output_file)
        
        output_row.addWidget(output_label)
        output_row.addWidget(self.output_path_field)
        output_row.addWidget(self.browse_output_button)
        io_layout.addLayout(output_row)
        
        io_group.setLayout(io_layout)
        config_layout.addWidget(io_group)
        config_layout.addSpacing(16)

        # Compiler options group
        compiler_group = QGroupBox("Compiler Configuration")
        compiler_layout = QVBoxLayout()
        compiler_layout.setContentsMargins(12, 10, 12, 10)

        # Create compiler options UI
        self._create_compiler_options(compiler_layout)

        compiler_group.setLayout(compiler_layout)
        config_layout.addWidget(compiler_group)
        config_layout.addSpacing(16)

        # Default Loader Configuration section
        self.default_loader_group = self._create_default_loader_section()
        config_layout.addWidget(self.default_loader_group)
        config_layout.addSpacing(16)

        # Add stretch to push content to top
        config_layout.addStretch()
        
        return config_container
    
    def _create_default_loader_section(self):
        """Create the Default Loader Configuration group box."""
        group = QGroupBox("Default Loader Configuration")
        grid = QGridLayout()
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        row = 0

        # ── Dataset Path ──────────────────────────────────────────
        ds_label = QLabel("Dataset Path:")
        ds_label.setMinimumWidth(130)
        ds_label.setToolTip("Path to the calibration dataset directory")
        self.dataset_path_field = QLineEdit()
        self.dataset_path_field.setPlaceholderText("/path/to/calibration_dataset")
        self.dataset_path_field.textChanged.connect(self._on_default_loader_changed)
        ds_browse = QPushButton("Browse...")
        ds_browse.setMaximumWidth(100)
        ds_browse.clicked.connect(self._on_browse_dataset_path)
        grid.addWidget(ds_label, row, 0)
        grid.addWidget(self.dataset_path_field, row, 1)
        grid.addWidget(ds_browse, row, 2)
        row += 1

        # ── File Extensions ───────────────────────────────────────
        ext_label = QLabel("File Extensions:")
        ext_label.setMinimumWidth(130)
        ext_label.setToolTip('JSON array of accepted file extensions, e.g. ["jpeg","jpg","png","JPEG"]')
        self.file_extensions_field = QLineEdit()
        self.file_extensions_field.setPlaceholderText('["jpeg", "jpg", "png", "JPEG"]')
        self.file_extensions_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(ext_label, row, 0)
        grid.addWidget(self.file_extensions_field, row, 1, 1, 2)
        row += 1

        # ── Preprocessing header ──────────────────────────────────
        pre_header = QLabel("Preprocessing:")
        pre_header.setMinimumWidth(130)
        pre_header.setStyleSheet("font-weight: bold; margin-top: 18px; margin-bottom: 4px;")
        grid.addWidget(pre_header, row, 0, 1, 3)
        row += 1

        # convertColor
        cc_label = QLabel("  Convert Color:")
        cc_label.setMinimumWidth(130)
        cc_label.setToolTip("Color space conversion applied to input images")
        self.convert_color_combo = QComboBox()
        self.convert_color_combo.addItem("None (no conversion)", "")
        for cs in ["RGB2BGR", "BGR2RGB", "RGB2GRAY", "BGR2GRAY",
                   "RGB2YCrCb", "BGR2YCrCb", "RGB2YUV", "BGR2YUV",
                   "RGB2HSV", "BGR2HSV", "RGB2LAB", "BGR2LAB"]:
            self.convert_color_combo.addItem(cs, cs)
        self.convert_color_combo.currentIndexChanged.connect(self._on_default_loader_changed)
        grid.addWidget(cc_label, row, 0)
        grid.addWidget(self.convert_color_combo, row, 1, 1, 2)
        row += 1

        # resize
        rs_label = QLabel("  Resize:")
        rs_label.setMinimumWidth(130)
        rs_label.setToolTip('e.g. {"mode":"default","width":224,"height":224,"interpolation":"LINEAR"}')
        self.resize_field = QLineEdit()
        self.resize_field.setPlaceholderText('{"mode": "default", "width": 224, "height": 224, "interpolation": "LINEAR"}')
        self.resize_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(rs_label, row, 0)
        grid.addWidget(self.resize_field, row, 1, 1, 2)
        row += 1

        # centercrop
        cc2_label = QLabel("  Center Crop:")
        cc2_label.setMinimumWidth(130)
        cc2_label.setToolTip('e.g. {"width": 224, "height": 224}  — leave empty to omit')
        self.centercrop_field = QLineEdit()
        self.centercrop_field.setPlaceholderText('{"width": 224, "height": 224}  (optional)')
        self.centercrop_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(cc2_label, row, 0)
        grid.addWidget(self.centercrop_field, row, 1, 1, 2)
        row += 1

        # transpose
        tr_label = QLabel("  Transpose:")
        tr_label.setMinimumWidth(130)
        tr_label.setToolTip('e.g. {"axis": [0, 2, 3, 1]}  — leave empty to omit')
        self.transpose_field = QLineEdit()
        self.transpose_field.setPlaceholderText('{"axis": [0, 2, 3, 1]}  (optional)')
        self.transpose_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(tr_label, row, 0)
        grid.addWidget(self.transpose_field, row, 1, 1, 2)
        row += 1

        # expandDim
        ed_label = QLabel("  Expand Dim:")
        ed_label.setMinimumWidth(130)
        ed_label.setToolTip('e.g. {"axis": 0}  — leave empty to omit')
        self.expand_dim_field = QLineEdit()
        self.expand_dim_field.setPlaceholderText('{"axis": 0}  (optional)')
        self.expand_dim_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(ed_label, row, 0)
        grid.addWidget(self.expand_dim_field, row, 1, 1, 2)
        row += 1

        # normalize
        nm_label = QLabel("  Normalize:")
        nm_label.setMinimumWidth(130)
        nm_label.setToolTip('e.g. {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}  — leave empty to omit')
        self.normalize_field = QLineEdit()
        self.normalize_field.setPlaceholderText('{"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}  (optional)')
        self.normalize_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(nm_label, row, 0)
        grid.addWidget(self.normalize_field, row, 1, 1, 2)
        row += 1

        # mul
        mul_label = QLabel("  Mul:")
        mul_label.setMinimumWidth(130)
        mul_label.setToolTip('e.g. {"x": 255}  — leave empty to omit')
        self.mul_field = QLineEdit()
        self.mul_field.setPlaceholderText('{"x": 255}  (optional)')
        self.mul_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(mul_label, row, 0)
        grid.addWidget(self.mul_field, row, 1, 1, 2)
        row += 1

        # add
        add_label = QLabel("  Add:")
        add_label.setMinimumWidth(130)
        add_label.setToolTip('e.g. {"x": 128}  — leave empty to omit')
        self.add_field = QLineEdit()
        self.add_field.setPlaceholderText('{"x": 128}  (optional)')
        self.add_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(add_label, row, 0)
        grid.addWidget(self.add_field, row, 1, 1, 2)
        row += 1

        # subtract
        sub_label = QLabel("  Subtract:")
        sub_label.setMinimumWidth(130)
        sub_label.setToolTip('e.g. {"x": 127}  — leave empty to omit')
        self.subtract_field = QLineEdit()
        self.subtract_field.setPlaceholderText('{"x": 127}  (optional)')
        self.subtract_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(sub_label, row, 0)
        grid.addWidget(self.subtract_field, row, 1, 1, 2)
        row += 1

        # div
        div_label = QLabel("  Div:")
        div_label.setMinimumWidth(130)
        div_label.setToolTip('e.g. {"x": 255}  — leave empty to omit')
        self.div_field = QLineEdit()
        self.div_field.setPlaceholderText('{"x": 255}  (optional)')
        self.div_field.textChanged.connect(self._on_default_loader_changed)
        grid.addWidget(div_label, row, 0)
        grid.addWidget(self.div_field, row, 1, 1, 2)

        group.setLayout(grid)
        return group

    def _on_browse_dataset_path(self):
        """Browse for calibration dataset directory."""
        _default_ds = self.settings_manager.get('default_dataset_path', '')
        initial = (self.dataset_path_field.text()
                   or (_default_ds if _default_ds and os.path.isdir(_default_ds) else self.last_browse_directory))
        directory = QFileDialog.getExistingDirectory(
            self, "Select Calibration Dataset Directory", initial
        )
        if directory:
            self.dataset_path_field.setText(directory)

    def _on_default_loader_changed(self):
        """Write default_loader fields to the JSON config file on any change."""
        self._write_default_loader_to_config()

    def _write_default_loader_to_config(self):
        """Persist the Default Loader section into the JSON config file."""
        if not self.config_file_path or not os.path.isfile(self.config_file_path):
            return
        try:
            with open(self.config_file_path, 'r') as _f:
                cfg = json.load(_f)

            dl = cfg.get('default_loader', {})

            # dataset_path
            ds = self.dataset_path_field.text().strip() if self.dataset_path_field else ''
            if ds:
                dl['dataset_path'] = ds

            # file_extensions
            ext_text = self.file_extensions_field.text().strip() if self.file_extensions_field else ''
            if ext_text:
                try:
                    dl['file_extensions'] = json.loads(ext_text)
                except Exception:
                    pass  # keep existing value if JSON is malformed

            # preprocessings — rebuild ordered list from each field
            preprocessings = []
            # convertColor
            if self.convert_color_combo:
                color_val = self.convert_color_combo.currentData()
                if color_val:
                    preprocessings.append({"convertColor": {"form": color_val}})
            # resize
            _rs = self.resize_field.text().strip() if self.resize_field else ''
            if _rs:
                try:
                    preprocessings.append({"resize": json.loads(_rs)})
                except Exception:
                    pass
            # centercrop
            _cc = self.centercrop_field.text().strip() if self.centercrop_field else ''
            if _cc:
                try:
                    preprocessings.append({"centercrop": json.loads(_cc)})
                except Exception:
                    pass
            # transpose
            _tr = self.transpose_field.text().strip() if self.transpose_field else ''
            if _tr:
                try:
                    preprocessings.append({"transpose": json.loads(_tr)})
                except Exception:
                    pass
            # expandDim
            _ed = self.expand_dim_field.text().strip() if self.expand_dim_field else ''
            if _ed:
                try:
                    preprocessings.append({"expandDim": json.loads(_ed)})
                except Exception:
                    pass
            # normalize
            _nm = self.normalize_field.text().strip() if self.normalize_field else ''
            if _nm:
                try:
                    preprocessings.append({"normalize": json.loads(_nm)})
                except Exception:
                    pass
            # mul
            _mul = self.mul_field.text().strip() if self.mul_field else ''
            if _mul:
                try:
                    preprocessings.append({"mul": json.loads(_mul)})
                except Exception:
                    pass
            # add
            _add = self.add_field.text().strip() if self.add_field else ''
            if _add:
                try:
                    preprocessings.append({"add": json.loads(_add)})
                except Exception:
                    pass
            # subtract
            _sub = self.subtract_field.text().strip() if self.subtract_field else ''
            if _sub:
                try:
                    preprocessings.append({"subtract": json.loads(_sub)})
                except Exception:
                    pass
            # div
            _div = self.div_field.text().strip() if self.div_field else ''
            if _div:
                try:
                    preprocessings.append({"div": json.loads(_div)})
                except Exception:
                    pass

            dl['preprocessings'] = preprocessings
            cfg['default_loader'] = dl

            with open(self.config_file_path, 'w') as _f:
                json.dump(cfg, _f, indent=2)
        except Exception as _e:
            self.set_status_message(f"Warning: could not update default_loader: {_e}", 3000)

    def _load_default_loader_from_config(self):
        """Read default_loader from JSON config and populate the UI widgets."""
        if not self.config_file_path or not os.path.isfile(self.config_file_path):
            return
        try:
            with open(self.config_file_path, 'r') as _f:
                cfg = json.load(_f)
            dl = cfg.get('default_loader', {})

            def _set(widget, value):
                widget.blockSignals(True)
                widget.setText(str(value) if value is not None else '')
                widget.blockSignals(False)

            # dataset_path
            if self.dataset_path_field:
                _set(self.dataset_path_field, dl.get('dataset_path', ''))

            # file_extensions
            if self.file_extensions_field:
                exts = dl.get('file_extensions', [])
                _set(self.file_extensions_field, json.dumps(exts) if exts else '')

            # Reset preprocessing fields
            for fld in [self.resize_field, self.centercrop_field,
                        self.transpose_field, self.expand_dim_field, self.normalize_field,
                        self.mul_field, self.add_field, self.subtract_field, self.div_field]:
                if fld:
                    fld.blockSignals(True)
                    fld.setText('')
                    fld.blockSignals(False)
            if self.convert_color_combo:
                self.convert_color_combo.blockSignals(True)
                self.convert_color_combo.setCurrentIndex(0)
                self.convert_color_combo.blockSignals(False)

            # Populate from preprocessings list
            for prep in dl.get('preprocessings', []):
                if 'convertColor' in prep and self.convert_color_combo:
                    form = prep['convertColor'].get('form', '')
                    idx = self.convert_color_combo.findData(form)
                    if idx >= 0:
                        self.convert_color_combo.blockSignals(True)
                        self.convert_color_combo.setCurrentIndex(idx)
                        self.convert_color_combo.blockSignals(False)
                elif 'resize' in prep and self.resize_field:
                    self.resize_field.blockSignals(True)
                    self.resize_field.setText(json.dumps(prep['resize']))
                    self.resize_field.blockSignals(False)
                elif 'centercrop' in prep and self.centercrop_field:
                    self.centercrop_field.blockSignals(True)
                    self.centercrop_field.setText(json.dumps(prep['centercrop']))
                    self.centercrop_field.blockSignals(False)
                elif 'transpose' in prep and self.transpose_field:
                    self.transpose_field.blockSignals(True)
                    self.transpose_field.setText(json.dumps(prep['transpose']))
                    self.transpose_field.blockSignals(False)
                elif 'expandDim' in prep and self.expand_dim_field:
                    self.expand_dim_field.blockSignals(True)
                    self.expand_dim_field.setText(json.dumps(prep['expandDim']))
                    self.expand_dim_field.blockSignals(False)
                elif 'normalize' in prep and self.normalize_field:
                    self.normalize_field.blockSignals(True)
                    self.normalize_field.setText(json.dumps(prep['normalize']))
                    self.normalize_field.blockSignals(False)
                elif 'mul' in prep and self.mul_field:
                    self.mul_field.blockSignals(True)
                    self.mul_field.setText(json.dumps(prep['mul']))
                    self.mul_field.blockSignals(False)
                elif 'add' in prep and self.add_field:
                    self.add_field.blockSignals(True)
                    self.add_field.setText(json.dumps(prep['add']))
                    self.add_field.blockSignals(False)
                elif 'subtract' in prep and self.subtract_field:
                    self.subtract_field.blockSignals(True)
                    self.subtract_field.setText(json.dumps(prep['subtract']))
                    self.subtract_field.blockSignals(False)
                elif 'div' in prep and self.div_field:
                    self.div_field.blockSignals(True)
                    self.div_field.setText(json.dumps(prep['div']))
                    self.div_field.blockSignals(False)
        except Exception:
            pass

    def _create_compiler_options(self, parent_layout):
        """
        Create compiler configuration options UI.
        
        Based on dxcom help output:
        - Config file path (required)
        - Generate log file (--gen_log)
        - Aggressive partitioning (--aggressive_partitioning)
        - Compile input nodes (--compile_input_nodes)
        - Compile output nodes (--compile_output_nodes)
        - Optimization level (--opt_level)
        """
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(12, 10, 12, 10)
        grid_layout.setColumnStretch(1, 1)  # Make middle column expandable
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(8)
        
        row = 0

        # Config file path (required parameter like -c/--config_path)
        config_label = QLabel("Config File:")
        config_label.setMinimumWidth(130)
        config_label.setToolTip("Path to the Model Configuration JSON file (*.json). [Required]")
        
        self.config_path_field = QLineEdit()
        self.config_path_field.setPlaceholderText("Select configuration JSON file...")
        self.config_path_field.setReadOnly(True)
        self.config_path_field.textChanged.connect(self._on_config_path_changed)
        
        config_button_layout = QHBoxLayout()
        config_button_layout.setSpacing(5)
        
        self.browse_config_button = QPushButton("Browse...")
        self.browse_config_button.setMaximumWidth(100)
        self.browse_config_button.clicked.connect(self._on_browse_config_file)
        config_button_layout.addWidget(self.browse_config_button)
        
        self.edit_config_button = QPushButton("Edit JSON...")
        self.edit_config_button.setMinimumWidth(110)
        self.edit_config_button.setMaximumWidth(120)
        self.edit_config_button.setEnabled(False)
        self.edit_config_button.setToolTip("Open JSON editor to view/edit configuration")
        self.edit_config_button.clicked.connect(self._on_edit_config_file)
        config_button_layout.addWidget(self.edit_config_button)
        
        grid_layout.addWidget(config_label, row, 0)
        grid_layout.addWidget(self.config_path_field, row, 1)
        grid_layout.addLayout(config_button_layout, row, 2)
        row += 1

        # Optimization level (--opt_level {0,1})
        opt_label = QLabel("Optimization Level:")
        opt_label.setMinimumWidth(130)
        opt_label.setToolTip("Higher levels improve performance but increase compilation time. Default: 1")

        self.opt_level_combo = QComboBox()
        self.opt_level_combo.addItem("Level 0 (Faster compilation)", 0)
        self.opt_level_combo.addItem("Level 1 (Better performance) [Default]", 1)
        self.opt_level_combo.setCurrentIndex(1)  # Default to level 1
        self.opt_level_combo.currentIndexChanged.connect(self._update_command_preview)

        grid_layout.addWidget(opt_label, row, 0)
        grid_layout.addWidget(self.opt_level_combo, row, 1, 1, 2)
        row += 1

        # Python-specific calibration options
        # Calibration Method
        self.python_calib_method_label = QLabel("Calibration Method:")
        self.python_calib_method_label.setMinimumWidth(130)
        self.python_calib_method_label.setToolTip("Calibration method for quantization: ema (Exponential Moving Average), minmax (Min-Max method)")
        self.python_calib_method_label.setVisible(False)  # Hidden by default
        
        self.calib_method_combo = QComboBox()
        self.calib_method_combo.addItem("ema (Exponential Moving Average)", "ema")
        self.calib_method_combo.addItem("minmax (Min-Max method)", "minmax")
        self.calib_method_combo.setToolTip("ema: Exponential Moving Average (default)\nminmax: Min-Max method")
        self.calib_method_combo.currentIndexChanged.connect(self._on_calib_setting_changed)
        
        self.python_calib_method_group = QWidget()
        calib_method_layout = QHBoxLayout()
        calib_method_layout.setContentsMargins(0, 0, 0, 0)
        calib_method_layout.addWidget(self.calib_method_combo)
        calib_method_layout.addStretch()
        self.python_calib_method_group.setLayout(calib_method_layout)
        self.python_calib_method_group.setVisible(False)  # Hidden by default (CLI mode)
        
        grid_layout.addWidget(self.python_calib_method_label, row, 0)
        grid_layout.addWidget(self.python_calib_method_group, row, 1, 1, 2)
        row += 1
        
        # Calibration Number
        self.python_calib_num_label = QLabel("Calibration Samples:")
        self.python_calib_num_label.setMinimumWidth(130)
        self.python_calib_num_label.setToolTip("Number of calibration samples for quantization (Python mode only)")
        self.python_calib_num_label.setVisible(False)  # Hidden by default
        
        self.calib_num_spinbox = QSpinBox()
        self.calib_num_spinbox.setRange(1, 10000)
        self.calib_num_spinbox.setValue(100)
        self.calib_num_spinbox.setToolTip("Default: 100 samples")
        self.calib_num_spinbox.valueChanged.connect(self._on_calib_setting_changed)
        
        self.python_calib_num_group = QWidget()
        calib_num_layout = QHBoxLayout()
        calib_num_layout.setContentsMargins(0, 0, 0, 0)
        calib_num_layout.addWidget(self.calib_num_spinbox)
        calib_num_layout.addStretch()
        self.python_calib_num_group.setLayout(calib_num_layout)
        self.python_calib_num_group.setVisible(False)  # Hidden by default (CLI mode)
        
        grid_layout.addWidget(self.python_calib_num_label, row, 0)
        grid_layout.addWidget(self.python_calib_num_group, row, 1, 1, 2)
        row += 1
        
        # Quantization Device
        self.python_quant_device_label = QLabel("Quantization Device:")
        self.python_quant_device_label.setMinimumWidth(130)
        self.python_quant_device_label.setToolTip("Device for quantization computation: cpu, cuda, cuda:0, cuda:1, etc.")
        self.python_quant_device_label.setVisible(False)  # Hidden by default
        
        self.quant_device_combo = QComboBox()
        self.quant_device_combo.setEditable(True)  # Allow custom text input
        self.quant_device_combo.addItems(["cpu", "cuda", "cuda:0", "cuda:1", "cuda:2", "cuda:3"])
        self.quant_device_combo.setToolTip("cpu, cuda, or specific GPU (e.g., cuda:0, cuda:1)\nYou can type custom values")
        
        self.python_quant_device_group = QWidget()
        quant_device_layout = QHBoxLayout()
        quant_device_layout.setContentsMargins(0, 0, 0, 0)
        quant_device_layout.addWidget(self.quant_device_combo)
        quant_device_layout.addStretch()
        self.python_quant_device_group.setLayout(quant_device_layout)
        self.python_quant_device_group.setVisible(False)  # Hidden by default (CLI mode)
        
        grid_layout.addWidget(self.python_quant_device_label, row, 0)
        grid_layout.addWidget(self.python_quant_device_group, row, 1, 1, 2)
        row += 1
        
        # Generate log file (--gen_log)
        gen_log_label = QLabel("Generate log file:")
        gen_log_label.setMinimumWidth(130)
        gen_log_label.setToolTip("Collect all logs into compiler.log file in output directory")
        self.gen_log_checkbox = QCheckBox()
        self.gen_log_checkbox.setToolTip("Collect all logs into compiler.log file in output directory")
        self.gen_log_checkbox.setChecked(False)
        self.gen_log_checkbox.toggled.connect(self._update_command_preview)
        grid_layout.addWidget(gen_log_label, row, 0)
        grid_layout.addWidget(self.gen_log_checkbox, row, 1, 1, 2)
        row += 1

        # Aggressive partitioning (--aggressive_partitioning)
        aggr_label = QLabel("Aggressive partitioning:")
        aggr_label.setMinimumWidth(130)
        aggr_label.setToolTip("Maximize operations executed on NPU")
        self.aggressive_partitioning_checkbox = QCheckBox()
        self.aggressive_partitioning_checkbox.setToolTip("Maximize operations executed on NPU")
        self.aggressive_partitioning_checkbox.setChecked(False)
        self.aggressive_partitioning_checkbox.toggled.connect(self._update_command_preview)
        grid_layout.addWidget(aggr_label, row, 0)
        grid_layout.addWidget(self.aggressive_partitioning_checkbox, row, 1, 1, 2)
        row += 1

        # Optional section header
        optional_label = QLabel("Optional:")
        optional_label.setMinimumWidth(130)
        optional_label.setStyleSheet("font-weight: bold; margin-top: 18px; margin-bottom: 4px;")
        grid_layout.addWidget(optional_label, row, 0, 1, 3)
        row += 1

        # Compile input nodes (--compile_input_nodes)
        input_nodes_label = QLabel("  Input Nodes:")
        input_nodes_label.setMinimumWidth(130)
        input_nodes_label.setToolTip("Comma-separated list of node names to compile from (optional)")

        self.compile_input_nodes_field = QLineEdit()
        self.compile_input_nodes_field.setPlaceholderText("e.g., node1,node2,node3 (optional)")
        self.compile_input_nodes_field.textChanged.connect(self._on_input_nodes_changed)

        grid_layout.addWidget(input_nodes_label, row, 0)
        grid_layout.addWidget(self.compile_input_nodes_field, row, 1, 1, 2)
        row += 1

        # Compile output nodes (--compile_output_nodes)
        output_nodes_label = QLabel("  Output Nodes:")
        output_nodes_label.setMinimumWidth(130)
        output_nodes_label.setToolTip("Comma-separated list of node names to compile up to (optional)")

        self.compile_output_nodes_field = QLineEdit()
        self.compile_output_nodes_field.setPlaceholderText("e.g., node1,node2,node3 (optional)")
        self.compile_output_nodes_field.textChanged.connect(self._on_output_nodes_changed)

        grid_layout.addWidget(output_nodes_label, row, 0)
        grid_layout.addWidget(self.compile_output_nodes_field, row, 1, 1, 2)
        row += 1

        # Enhanced Scheme
        self.python_enhanced_scheme_label = QLabel("  Enhanced Scheme:")
        self.python_enhanced_scheme_label.setMinimumWidth(130)
        self.python_enhanced_scheme_label.setToolTip("Advanced quantization scheme (Python mode only, JSON format)")
        self.python_enhanced_scheme_label.setVisible(False)  # Hidden by default

        self.enhanced_scheme_field = QLineEdit()
        self.enhanced_scheme_field.setPlaceholderText('e.g., {"DXQ-P0": {"alpha": 0.5}} (optional)')
        self.enhanced_scheme_field.setToolTip("Advanced quantization scheme in JSON format (not supported for multi-input models)")

        self.python_enhanced_scheme_group = QWidget()
        enhanced_scheme_layout = QHBoxLayout()
        enhanced_scheme_layout.setContentsMargins(0, 0, 0, 0)
        enhanced_scheme_layout.addWidget(self.enhanced_scheme_field)
        self.python_enhanced_scheme_group.setLayout(enhanced_scheme_layout)
        self.python_enhanced_scheme_group.setVisible(False)  # Hidden by default (CLI mode)

        grid_layout.addWidget(self.python_enhanced_scheme_label, row, 0)
        grid_layout.addWidget(self.python_enhanced_scheme_group, row, 1, 1, 2)
        row += 1

        parent_layout.addLayout(grid_layout)
    
    def _create_command_preview(self):
        """Create the command preview section."""
        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(5)
        
        # Command label
        command_label = QLabel("Command Preview:")
        command_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        preview_layout.addWidget(command_label)
        
        # Command text area with copy button
        command_row = QHBoxLayout()
        
        self.command_preview_field = QLineEdit()
        self.command_preview_field.setReadOnly(True)
        self.command_preview_field.setPlaceholderText("Configure inputs to see the command...")
        self.command_preview_field.setStyleSheet("""
            QLineEdit {
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                background-color: #2a2a2a;
                color: #00ff00;
                padding: 8px;
                border: 1px solid #555;
                border-radius: 3px;
            }
        """)
        command_row.addWidget(self.command_preview_field)
        
        # Copy button
        copy_button = QPushButton("Copy")
        copy_button.setMaximumWidth(80)
        copy_button.setToolTip("Copy command to clipboard")
        copy_button.clicked.connect(self._on_copy_command)
        command_row.addWidget(copy_button)
        
        preview_layout.addLayout(command_row)
        
        return preview_layout
    
    def _create_log_section(self):
        """Create the log viewer section."""
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(5)
        
        # Log viewer group
        log_group = QGroupBox("Compilation Log")
        log_group_layout = QVBoxLayout()
        
        # Real-time log text area
        self.log_text_area = QTextEdit()
        self.log_text_area.setReadOnly(True)
        self.log_text_area.setPlaceholderText("Compilation output will appear here...")
        self.log_text_area.setMinimumHeight(200)
        # Use monospace font for better log readability
        font = self.log_text_area.font()
        font.setFamily("Monospace")
        font.setStyleHint(font.StyleHint.TypeWriter)
        self.log_text_area.setFont(font)
        # Set dark background for better color visibility
        self.log_text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e6e6e6;
                border: 1px solid #555;
            }
        """)
        
        log_group_layout.addWidget(self.log_text_area)
        
        # Progress bar for compilation progress
        progress_layout = QHBoxLayout()
        progress_label = QLabel("Progress:")
        progress_label.setMaximumWidth(60)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        log_group_layout.addLayout(progress_layout)
        
        log_group.setLayout(log_group_layout)
        log_layout.addWidget(log_group)
        
        return log_container
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()
        self.set_status_message("Ready")
    
    def _check_dxcom_availability(self):
        """Check if dxcom compiler is available and validate environment."""
        # First check basic dxcom availability
        dxcom_info = check_dxcom_available()
        self.dxcom_available = dxcom_info.is_valid()
        
        if self.dxcom_available:
            # Success - run comprehensive environment validation
            validation = validate_environment()
            
            if validation.overall_valid:
                status_type, status_msg = get_dxcom_status()
                self.set_status_message(status_msg)
                
                # Show warnings if any
                if validation.warnings:
                    warning_text = "Environment validation passed with warnings:\n\n"
                    warning_text += "\n".join(f"• {w.message}" for w in validation.warnings)
                    QMessageBox.warning(
                        self,
                        "Environment Warnings",
                        warning_text,
                        QMessageBox.StandardButton.Ok
                    )
            else:
                # Environment validation failed
                error_text = "Environment validation failed:\n\n"
                error_text += "\n".join(f"• {e.message}" for e in validation.errors)
                error_text += "\n\nPlease resolve these issues before compiling."
                
                QMessageBox.critical(
                    self,
                    "Environment Validation Failed",
                    error_text,
                    QMessageBox.StandardButton.Ok
                )
                self.dxcom_available = False  # Disable compilation
                self.set_status_message("Error: Environment validation failed")
        else:
            # Error - show warning dialog
            QMessageBox.warning(
                self,
                "DXCom Not Found",
                f"{dxcom_info.error_message}\n\n"
                "The compiler will not be available until dxcom is installed.\n\n"
                "Please install the DEEPX dxcom compiler and ensure it is in your system PATH.",
                QMessageBox.StandardButton.Ok
            )
            self.set_status_message("Warning: dxcom compiler not found")
            
        # Update compile button state
        if self.compile_button:
            if not self.dxcom_available:
                self.compile_button.setEnabled(False)
                self.compile_button.setToolTip("dxcom compiler not found - please install dxcom")
            else:
                self._update_compile_button_state()
        
        # Initialize UI state based on default mode (Python tab is first/default)
        self._on_mode_changed(0)
    
    # Public API
    
    def set_status_message(self, message, timeout=0):
        """
        Display a message in the status bar.
        
        Args:
            message (str): The message to display
            timeout (int): Time in milliseconds to show the message. 
                          0 means permanent until next message (default)
        """
        self.status_bar.showMessage(message, timeout)
    
    def _set_compilation_status(self, status: CompilationStatus):
        """
        Update the compilation status and UI elements.
        
        Args:
            status: CompilationStatus enum value
        """
        self.compilation_status = status
        
        # Update status label with color coding
        status_text = {
            CompilationStatus.IDLE: ("Status: Ready", "#888888"),
            CompilationStatus.RUNNING: ("Status: Compiling...", "#FFB84D"),  # Orange
            CompilationStatus.SUCCESS: ("Status: Completed", "#57FF57"),  # Green
            CompilationStatus.FAILED: ("Status: Failed", "#FF5555"),  # Red
            CompilationStatus.CANCELLED: ("Status: Cancelled", "#888888")  # Gray
        }
        
        text, color = status_text[status]
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-weight: bold; padding: 5px; color: {color};")
    
    def _append_log_message(self, message: str, level: str = "default"):
        """
        Append a message to the log viewer with appropriate formatting.
        
        Args:
            message: Message to append
            level: Message level (info, warning, error, success, default)
        """
        # Move cursor to end
        self.log_text_area.moveCursor(QTextCursor.MoveOperation.End)
        
        # Create text format based on level
        text_format = QTextCharFormat()
        color_map = {
            "info": QColor(100, 200, 255),  # Light blue
            "warning": QColor(255, 200, 87),  # Yellow
            "error": QColor(255, 85, 85),  # Light red
            "success": QColor(87, 255, 87),  # Light green
            "default": QColor(230, 230, 230)  # Off-white
        }
        text_format.setForeground(color_map.get(level, color_map["default"]))
        
        # Insert text with formatting
        cursor = self.log_text_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(message, text_format)
        
        # Auto-scroll to bottom
        self.log_text_area.moveCursor(QTextCursor.MoveOperation.End)
    
    def log(self, message: str, level: str = "default"):
        """
        Convenience method for logging messages (wrapper for _append_log_message).
        
        Args:
            message: Message to log
            level: Message level (info, warning, error, success, default)
        """
        self._append_log_message(message, level)
    
    def get_compiler_options(self):
        """
        Get current compiler configuration values.
        
        Returns:
            dict: Dictionary containing all compiler option values:
                - config_path: str - Path to configuration JSON file
                - opt_level: int - Optimization level (0 or 1)
                - gen_log: bool - Generate log file
                - aggressive_partitioning: bool - Enable aggressive partitioning
                - compile_input_nodes: str - Comma-separated input node names (may be empty)
                - compile_output_nodes: str - Comma-separated output node names (may be empty)
        """
        return {
            'config_path': self.config_file_path,
            'opt_level': self.opt_level_combo.currentData(),
            'gen_log': self.gen_log_checkbox.isChecked(),
            'aggressive_partitioning': self.aggressive_partitioning_checkbox.isChecked(),
            'compile_input_nodes': self.compile_input_nodes_field.text().strip(),
            'compile_output_nodes': self.compile_output_nodes_field.text().strip(),
            'calib_method': self.calib_method_combo.currentData() if hasattr(self, 'calib_method_combo') else 'ema',
            'calib_num': self.calib_num_spinbox.value() if hasattr(self, 'calib_num_spinbox') else 100,
        }
    
    # Event handlers
    
    def _on_compile_clicked(self):
        """Handle Compile button click - validate environment and start compilation."""
        # Perform comprehensive environment validation before compilation
        validation = validate_for_compilation(self.output_model_path)
        
        if not validation.overall_valid:
            # Show validation errors
            error_text = "Cannot start compilation. Environment validation failed:\n\n"
            error_text += "\n".join(f"• {e.message}" for e in validation.errors)
            error_text += "\n\nPlease resolve these issues before compiling."
            
            if validation.warnings:
                error_text += "\n\nWarnings:\n"
                error_text += "\n".join(f"• {w.message}" for w in validation.warnings)
            
            QMessageBox.critical(
                self,
                "Environment Validation Failed",
                error_text,
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Show warnings if any (but allow compilation to proceed)
        if validation.warnings:
            warning_text = "Environment validation passed with warnings:\n\n"
            warning_text += "\n".join(f"• {w.message}" for w in validation.warnings)
            warning_text += "\n\nDo you want to proceed with compilation?"
            
            result = QMessageBox.warning(
                self,
                "Environment Warnings",
                warning_text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Environment is valid - start actual compilation
        self._start_compilation()
    
    def _start_compilation(self):
        """Start the actual compilation process."""
        # Check if batch mode
        if self.batch_mode and len(self.batch_files) > 1:
            self._start_batch_compilation()
            return
        
        # Record start time
        self.compilation_start_time = time.time()
        
        # Update compilation status
        self._set_compilation_status(CompilationStatus.RUNNING)
        
        # Clear the log area and reset progress bar
        self.log_text_area.clear()
        self.progress_bar.setValue(0)
        
        # Get compiler options
        compiler_options = self.get_compiler_options()
        
        # Check execution mode
        if self.execution_mode == "python":
            # Python mode: generate and run Python script
            self._run_python_compilation(compiler_options)
        else:
            # CLI mode: run dxcom command directly
            self._run_cli_compilation(compiler_options)
    
    def _apply_calib_to_config(self, compiler_options):
        """
        If a config file is set, write calibration_method and calibration_num
        into the JSON and return options with calib keys removed (so the
        dxcom wrapper won't also add --calib_method / --calib_num CLI flags).
        Otherwise return options unchanged.
        """
        if compiler_options.get('config_path') and os.path.isfile(compiler_options['config_path']):
            try:
                import json as _json
                with open(compiler_options['config_path'], 'r') as _f:
                    _cfg = _json.load(_f)
                _cfg['calibration_method'] = compiler_options.get('calib_method', 'ema')
                _cfg['calibration_num'] = compiler_options.get('calib_num', 100)
                with open(compiler_options['config_path'], 'w') as _f:
                    _json.dump(_cfg, _f, indent=2)
                self.log(f"[Config] Updated calibration_method={_cfg['calibration_method']}, "
                         f"calibration_num={_cfg['calibration_num']} in "
                         f"{os.path.basename(compiler_options['config_path'])}\n")
            except Exception as _e:
                self.log(f"[Warning] Could not update config file: {_e}\n")
            # Return a copy without calib keys so wrapper won't emit CLI flags
            compiler_options = dict(compiler_options)
            compiler_options.pop('calib_method', None)
            compiler_options.pop('calib_num', None)
        return compiler_options

    def _run_cli_compilation(self, compiler_options):
        """Run compilation using CLI dxcom command."""
        # When a config file is set, write calib settings into the JSON
        compiler_options = self._apply_calib_to_config(compiler_options)

        # Construct output file path from output directory + input model base name
        base_name = os.path.splitext(os.path.basename(self.input_model_path))[0]
        output_dir = self.output_model_path or os.path.dirname(self.input_model_path)
        output_file = os.path.join(output_dir, f"{base_name}.dxnn")

        # Create executor
        self.current_executor = self.dxcom_wrapper.compile(
            input_path=self.input_model_path,
            output_path=output_file,
            compiler_options=compiler_options
        )
        
        # Connect signals to slots
        self.current_executor.output_received.connect(self._on_output_received)
        self.current_executor.progress_updated.connect(self._on_progress_updated)
        self.current_executor.compilation_finished.connect(self._on_compilation_finished)
        self.current_executor.error_occurred.connect(self._on_error_occurred)
        
        # Update UI for running state
        self.compile_button.setEnabled(False)
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        
        # Update status
        self.set_status_message("Compilation started (CLI mode)...")
        
        # Start the compilation thread
        self.current_executor.start()
    
    def _run_python_compilation(self, compiler_options):
        """Run compilation using Python dx_com.compile() script."""
        import os
        
        # Check if user has saved a custom script
        if self.saved_python_script_path and os.path.exists(self.saved_python_script_path):
            # Use the saved script
            script_path = self.saved_python_script_path
            self._append_log_message(f"Using saved Python script: {script_path}\n", "info")
        else:
            # Generate temporary Python script with fixed path
            script_content = self._generate_python_script_content(compiler_options)
            
            # Use fixed temp file path
            script_path = "/tmp/tmp_dx_com.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self._append_log_message(f"Generated temporary Python script: {script_path}\n", "info")
        
        # Create executor using Python script
        self.current_executor = self.dxcom_wrapper.compile_with_python(
            script_path=script_path,
            input_path=self.input_model_path,
            output_path=self.output_model_path
        )
        
        # Connect signals to slots
        self.current_executor.output_received.connect(self._on_output_received)
        self.current_executor.progress_updated.connect(self._on_progress_updated)
        self.current_executor.compilation_finished.connect(self._on_compilation_finished)
        self.current_executor.error_occurred.connect(self._on_error_occurred)
        
        # Update UI for running state
        self.compile_button.setEnabled(False)
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        
        # Update status
        self.set_status_message("Compilation started (Python mode)...")
        
        # Start the compilation thread
        self.current_executor.start()
    
    def _generate_python_script_content(self, compiler_options):
        """Generate Python script content for dx_com.compile()."""
        script_lines = [
            '#!/usr/bin/env python3',
            '"""',
            'DX-COM Compilation Script',
            'Generated by DXCom GUI',
            '',
            'This script uses the dx_com Python wheel package to compile an ONNX model.',
            'Install dx_com first: pip install <path-to-dx_com-wheel.whl>',
            '"""',
            '',
            'import dx_com',
            'import os',
            '',
            f'MODEL_PATH = r"{self.input_model_path}"',
            f'OUTPUT_DIR = r"{self.output_model_path}"',
            f'OUTPUT_FILE = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(MODEL_PATH))[0] + ".dxnn")',
        ]
        
        # Check if using dataloader or config
        if self.python_data_source == "dataloader":
            # DataLoader mode
            script_lines.extend([
                '',
                '# Custom DataLoader for calibration data',
                'from torch.utils.data import Dataset, DataLoader',
                '',
                'class CustomDataset(Dataset):',
                '    def __init__(self):',
                '        # Initialize your dataset - example with dummy data',
                '        # Replace this with your actual data loading logic',
                '        import numpy as np',
                '        # Example: Create 10 dummy samples with shape (3, 224, 224)',
                '        # DataLoader will add batch dimension to make it (batch_size, 3, 224, 224)',
                '        self.data = [np.random.randn(3, 224, 224).astype(np.float32) for _ in range(10)]',
                '    ',
                '    def __len__(self):',
                '        return len(self.data)',
                '    ',
                '    def __getitem__(self, idx):',
                '        # Return single sample or tuple of samples for multi-input models',
                '        # For single-input: return self.data[idx]',
                '        # For multi-input: return (input1[idx], input2[idx], ...)',
                '        return self.data[idx]',
                '',
                'dataset = CustomDataset()',
                'dataloader = DataLoader(dataset, batch_size=1, shuffle=True)',
                '',
            ])
        else:
            # Config mode
            script_lines.append(f'CONFIG_PATH = r"{self.config_file_path}"')
            script_lines.append('')
        
        # Compiler options
        script_lines.extend([
            f'OPT_LEVEL = {compiler_options["opt_level"]}',
            f'AGGRESSIVE_PARTITIONING = {compiler_options["aggressive_partitioning"]}',
            f'GEN_LOG = {compiler_options["gen_log"]}',
        ])
        
        # Python-specific options
        if hasattr(self, 'calib_method_combo'):
            script_lines.append(f'CALIBRATION_METHOD = "{self.calib_method_combo.currentData()}"')
        if hasattr(self, 'calib_num_spinbox'):
            script_lines.append(f'CALIBRATION_NUM = {self.calib_num_spinbox.value()}')
        if hasattr(self, 'quant_device_combo'):
            script_lines.append(f'QUANTIZATION_DEVICE = "{self.quant_device_combo.currentText()}"')
        
        script_lines.append('')
        
        # Add input/output nodes if specified
        if compiler_options['compile_input_nodes']:
            input_nodes = [n.strip() for n in compiler_options['compile_input_nodes'].split(',')]
            script_lines.append(f'INPUT_NODES = {input_nodes}')
        else:
            script_lines.append('INPUT_NODES = None')
        
        if compiler_options['compile_output_nodes']:
            output_nodes = [n.strip() for n in compiler_options['compile_output_nodes'].split(',')]
            script_lines.append(f'OUTPUT_NODES = {output_nodes}')
        else:
            script_lines.append('OUTPUT_NODES = None')
        
        script_lines.extend([
            '',
            'print("Starting DX-COM compilation...")',
            'print(f"Model: {MODEL_PATH}")',
        ])
        
        if self.python_data_source == "config":
            script_lines.append('print(f"Config: {CONFIG_PATH}")')
        else:
            script_lines.append('print("Using PyTorch DataLoader")')
        
        script_lines.extend([
            'print(f"Output: {OUTPUT_DIR}")',
            'print()',
            '',
            'os.makedirs(OUTPUT_DIR, exist_ok=True)',
            '',
            'dx_com.compile(',
            '    model=MODEL_PATH,',
            '    output_dir=OUTPUT_DIR,',
        ])
        
        # Config or dataloader parameter
        if self.python_data_source == "config":
            script_lines.append('    config=CONFIG_PATH,')
        else:
            script_lines.append('    dataloader=dataloader,')
        
        script_lines.extend([
            '    opt_level=OPT_LEVEL,',
            '    aggressive_partitioning=AGGRESSIVE_PARTITIONING,',
            '    gen_log=GEN_LOG,',
        ])
        
        # Add Python-specific parameters
        if hasattr(self, 'calib_method_combo'):
            script_lines.append('    calibration_method=CALIBRATION_METHOD,')
        if hasattr(self, 'calib_num_spinbox'):
            script_lines.append('    calibration_num=CALIBRATION_NUM,')
        if hasattr(self, 'quant_device_combo'):
            script_lines.append('    quantization_device=QUANTIZATION_DEVICE,')
        
        # Add enhanced_scheme if provided
        if hasattr(self, 'enhanced_scheme_field') and self.enhanced_scheme_field.text().strip():
            try:
                # Validate JSON format
                import json
                enhanced_scheme = json.loads(self.enhanced_scheme_field.text().strip())
                script_lines.append(f'    enhanced_scheme={enhanced_scheme},')
            except:
                # If invalid JSON, add as comment
                script_lines.append(f'    # enhanced_scheme: Invalid JSON format')
        
        if compiler_options['compile_input_nodes']:
            script_lines.append('    input_nodes=INPUT_NODES,')
        if compiler_options['compile_output_nodes']:
            script_lines.append('    output_nodes=OUTPUT_NODES,')
        
        script_lines.extend([
            ')',
            '',
            'print()',
            'print("Compilation completed successfully!")',
            'print(f"Output DXNN file saved to: {OUTPUT_FILE}")',
        ])
        
        return '\n'.join(script_lines)
    
    def _start_batch_compilation(self):
        """Start batch compilation of multiple files."""
        # Record start time for batch
        self.compilation_start_time = time.time()
        
        self._set_compilation_status(CompilationStatus.RUNNING)
        self.log_text_area.clear()
        self.progress_bar.setValue(0)
        
        self.log("Starting batch compilation...")
        self.log(f"Total files: {len(self.batch_files)}\n")
        
        # Track batch state
        self.batch_current_index = 0
        self.batch_success_count = 0
        self.batch_failed_count = 0
        
        # Update UI
        self.compile_button.setEnabled(False)
        self.cancel_button.setVisible(True)
        self.cancel_button.setEnabled(True)
        
        # Start first file
        self._compile_next_batch_file()
    
    def _compile_next_batch_file(self):
        """Compile the next file in batch mode."""
        if self.batch_current_index >= len(self.batch_files):
            # All files done
            self._finish_batch_compilation()
            return
        
        # Get current file
        current_file = self.batch_files[self.batch_current_index]
        file_num = self.batch_current_index + 1
        total_files = len(self.batch_files)
        
        self.log(f"\n{'='*60}")
        self.log(f"[{file_num}/{total_files}] Compiling: {os.path.basename(current_file)}")
        self.log(f"{'='*60}\n")
        
        # Generate output path for this file
        base_name = os.path.splitext(os.path.basename(current_file))[0]
        output_dir = self.output_model_path or os.path.dirname(current_file)
        output_file = os.path.join(output_dir, f"{base_name}.dxnn")
        
        # Get compiler options
        compiler_options = self.get_compiler_options()
        compiler_options = self._apply_calib_to_config(compiler_options)

        # Create executor
        self.current_executor = self.dxcom_wrapper.compile(
            input_path=current_file,
            output_path=output_file,
            compiler_options=compiler_options
        )
        
        # Connect signals
        self.current_executor.output_received.connect(self._on_output_received)
        self.current_executor.progress_updated.connect(self._on_batch_progress_updated)
        self.current_executor.compilation_finished.connect(self._on_batch_file_finished)
        self.current_executor.error_occurred.connect(self._on_error_occurred)
        
        # Start compilation
        self.current_executor.start()
    
    @Slot(int)
    def _on_batch_progress_updated(self, progress: int):
        """Handle progress update in batch mode."""
        # Calculate overall progress across all files
        file_progress = (self.batch_current_index * 100 + progress) / len(self.batch_files)
        self.progress_bar.setValue(int(file_progress))
    
    @Slot(bool, str)
    def _on_batch_file_finished(self, success: bool, message: str):
        """Handle completion of one file in batch mode."""
        if success:
            self.batch_success_count += 1
            self.log(f"\n✓ File {self.batch_current_index + 1} completed successfully\n")
        else:
            self.batch_failed_count += 1
            self.log(f"\n✗ File {self.batch_current_index + 1} failed: {message}\n")
        
        # Move to next file
        self.batch_current_index += 1
        
        # Continue with next file
        self._compile_next_batch_file()
    
    def _finish_batch_compilation(self):
        """Finish batch compilation and show results."""
        self._set_compilation_status(CompilationStatus.SUCCESS if self.batch_failed_count == 0 else CompilationStatus.FAILED)
        
        # Calculate total batch time
        duration_text = ""
        if self.compilation_start_time:
            duration = time.time() - self.compilation_start_time
            if duration < 60:
                duration_text = f"\nTotal time: {duration:.2f} seconds"
            else:
                minutes = int(duration // 60)
                seconds = duration % 60
                duration_text = f"\nTotal time: {minutes}m {seconds:.1f}s"
        
        # Update UI
        self.compile_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.progress_bar.setValue(100)
        
        # Show summary
        summary = f"""
Batch Compilation Complete!

Total Files: {len(self.batch_files)}
Successful: {self.batch_success_count}
Failed: {self.batch_failed_count}{duration_text}
"""
        self.log("\n" + "="*60)
        self.log(summary)
        self.log("="*60)
        
        # Show message box
        if self.batch_failed_count == 0:
            QMessageBox.information(
                self, "Batch Compilation Complete",
                f"All {self.batch_success_count} files compiled successfully!{duration_text}"
            )
        else:
            QMessageBox.warning(
                self, "Batch Compilation Complete",
                f"Batch compilation finished.\n\n"
                f"Successful: {self.batch_success_count}\n"
                f"Failed: {self.batch_failed_count}{duration_text}\n\n"
                f"Check the log for details."
            )
        
        # Reset batch mode
        self.batch_mode = False
        self.batch_files = []
        self.compile_button.setText("Compile")
    
    @Slot(str)
    def _on_output_received(self, line: str):
        """Handle output received from dxcom with syntax highlighting."""
        # Move cursor to end
        self.log_text_area.moveCursor(QTextCursor.MoveOperation.End)
        
        # Create text format based on log level
        text_format = QTextCharFormat()
        line_lower = line.lower()
        
        # Color coding for different log types
        if "error" in line_lower or "fail" in line_lower or "fatal" in line_lower:
            # Error messages in red
            text_format.setForeground(QColor(255, 85, 85))  # Light red
        elif "warn" in line_lower or "warning" in line_lower:
            # Warnings in yellow
            text_format.setForeground(QColor(255, 200, 87))  # Yellow
        elif "success" in line_lower or "complete" in line_lower or "done" in line_lower:
            # Success messages in green
            text_format.setForeground(QColor(87, 255, 87))  # Light green
        elif "info" in line_lower or "loading" in line_lower or "starting" in line_lower:
            # Info messages in cyan
            text_format.setForeground(QColor(100, 200, 255))  # Light blue
        elif line_lower.startswith("  ") or line_lower.startswith("\t"):
            # Indented/detail lines in gray
            text_format.setForeground(QColor(180, 180, 180))  # Light gray
        else:
            # Default text in white
            text_format.setForeground(QColor(230, 230, 230))  # Off-white
        
        # Insert text with formatting
        cursor = self.log_text_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line, text_format)
        
        # Auto-scroll to bottom
        self.log_text_area.moveCursor(QTextCursor.MoveOperation.End)
    
    @Slot(int, str)
    def _on_progress_updated(self, percentage: int, message: str):
        """Handle progress updates from dxcom."""
        self.set_status_message(f"Compiling: {percentage}% - {message}")
        # Update progress bar
        self.progress_bar.setValue(percentage)
    
    @Slot(bool, str)
    def _on_compilation_finished(self, success: bool, message: str):
        """Handle compilation completion."""
        # Update compilation status
        if "cancel" in message.lower():
            self._set_compilation_status(CompilationStatus.CANCELLED)
        elif success:
            self._set_compilation_status(CompilationStatus.SUCCESS)
        else:
            self._set_compilation_status(CompilationStatus.FAILED)
        
        # Re-enable compile button and reset cancel button
        self.compile_button.setEnabled(True)
        self.cancel_button.setVisible(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
        
        # Set progress bar to 100% if successful
        if success:
            self.progress_bar.setValue(100)
            self.set_status_message("Compilation completed successfully")
            
            # Calculate compilation time
            duration_text = ""
            if self.compilation_start_time:
                duration = time.time() - self.compilation_start_time
                if duration < 60:
                    duration_text = f"\n\nCompilation time: {duration:.2f} seconds"
                else:
                    minutes = int(duration // 60)
                    seconds = duration % 60
                    duration_text = f"\n\nCompilation time: {minutes}m {seconds:.1f}s"
            
            # Derive the actual .dxnn output file path
            output_base = os.path.splitext(os.path.basename(self.input_model_path))[0]
            output_dir = self.output_model_path or os.path.dirname(self.input_model_path)
            output_dxnn_file = os.path.join(output_dir, f"{output_base}.dxnn")

            QMessageBox.information(
                self,
                "Compilation Complete",
                f"Compilation completed successfully!\n\nOutput: {output_dxnn_file}{duration_text}",
                QMessageBox.StandardButton.Ok
            )
        elif "cancel" in message.lower():
            self.set_status_message("Compilation cancelled by user")
        else:
            self.set_status_message(f"Compilation failed: {message}")
    
    @Slot(str)
    def _on_error_occurred(self, error_message: str):
        """Handle errors during compilation."""
        # Error is already displayed in the log via output_received
        # Just update the status bar
        self.set_status_message(f"Error: {error_message}")
    
    def _on_cancel_clicked(self):
        """Handle Cancel button click - stop the running compilation."""
        if self.current_executor and self.current_executor.isRunning():
            # Confirm cancellation
            result = QMessageBox.question(
                self,
                "Cancel Compilation",
                "Are you sure you want to cancel the running compilation?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # Request cancellation
                self.current_executor.stop()
                self.cancel_button.setEnabled(False)
                self.cancel_button.setText("Cancelling...")
                self.set_status_message("Cancelling compilation...")
                self._append_log_message("\n[User requested cancellation]\n", "info")
    
    def _on_browse_input_file(self):
        """Handle Browse button click for input ONNX file selection."""
        # Determine initial directory: settings default > last browse > ~
        _default_input = self.settings_manager.get('default_input_path', '')
        if _default_input and os.path.isdir(_default_input):
            initial_dir = _default_input
        else:
            initial_dir = self.last_browse_directory

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ONNX Model File",
            initial_dir,
            "ONNX Model Files (*.onnx);;All Files (*)"
        )
        
        if file_path:
            self.batch_mode = False
            self.batch_files = []
            self.input_model_path = file_path
            self.input_path_field.setText(file_path)
            
            # Remember the directory for next time
            self.last_browse_directory = os.path.dirname(file_path)
            
            # Add to recent files
            self.settings_manager.add_recent_file(file_path)
            self._update_recent_files_menu()
            
            # Auto-suggest output path based on input file
            self._suggest_output_path(file_path)
            
            # Validate the input file
            self._validate_input_file(file_path)
            
            # Update status bar
            self.set_status_message(f"Selected input model: {os.path.basename(file_path)}")
            
            # Reset compile button text if it was in batch mode
            if self.compile_button:
                self.compile_button.setText("Compile")
    
    def _on_browse_config_file(self):
        """Handle Browse button click for config JSON file selection."""
        _default_json = self.settings_manager.get('default_json_path', '')
        initial_dir = _default_json if _default_json and os.path.isdir(_default_json) else self.last_browse_directory

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration JSON File",
            initial_dir,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            self.config_file_path = file_path
            self.config_path_field.setText(file_path)
            
            # Remember the directory for next time
            self.last_browse_directory = os.path.dirname(file_path)
            
            # Add to recent files
            self.settings_manager.add_recent_file(file_path)
            self._update_recent_files_menu()
            
            # Validate the config file
            self._validate_config_file(file_path)

            # Sync calib widgets to values already in the JSON
            try:
                import json as _json
                with open(file_path, 'r') as _f:
                    _cfg = _json.load(_f)
                _method = _cfg.get('calibration_method', 'ema')
                _idx = self.calib_method_combo.findData(_method)
                if _idx >= 0:
                    self.calib_method_combo.blockSignals(True)
                    self.calib_method_combo.setCurrentIndex(_idx)
                    self.calib_method_combo.blockSignals(False)
                _num = _cfg.get('calibration_num', 100)
                self.calib_num_spinbox.blockSignals(True)
                self.calib_num_spinbox.setValue(int(_num))
                self.calib_num_spinbox.blockSignals(False)
            except Exception:
                pass

            # Sync default_loader widgets
            self._load_default_loader_from_config()

            # Update status bar
            self.set_status_message(f"Selected config file: {os.path.basename(file_path)}")
    
    def _on_browse_output_file(self):
        """Handle Browse button click for output directory selection."""
        # Determine initial directory
        _default_output = self.settings_manager.get('default_output_path', '')
        if self.output_model_path and os.path.isdir(self.output_model_path):
            initial_dir = self.output_model_path
        elif self.input_model_path:
            initial_dir = os.path.dirname(self.input_model_path)
        elif _default_output and os.path.isdir(_default_output):
            initial_dir = _default_output
        else:
            initial_dir = self.last_browse_directory
        
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            initial_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if dir_path:
            # Validate the output directory
            validation_result = self._validate_output_path(dir_path)
            if validation_result is True:
                self.output_model_path = dir_path
                self.output_path_field.setText(dir_path)
                self.set_status_message(f"Output directory set to: {dir_path}")
            else:
                # Show error message
                QMessageBox.warning(
                    self,
                    "Invalid Output Directory",
                    validation_result
                )
                self.set_status_message("Output directory validation failed")
    
    def _on_output_path_changed(self):
        """Handle manual changes to output directory field."""
        path = self.output_path_field.text()
        if path:
            # Validate on manual entry
            validation_result = self._validate_output_path(path)
            if validation_result is True:
                self.output_model_path = path
                # Clear any previous error styling
                self.output_path_field.setStyleSheet("")
            else:
                # Visual feedback for invalid path
                self.output_path_field.setStyleSheet("border: 1px solid #ff6b6b;")
        else:
            self.output_model_path = ""
            self.output_path_field.setStyleSheet("")
        self._update_command_preview()
    
    def _suggest_output_path(self, input_path):
        """Suggest output directory based on input file path."""
        output_dir = os.path.dirname(input_path)
        
        self.output_model_path = output_dir
        self.output_path_field.setText(output_dir)
    
    def _validate_output_path(self, path):
        """
        Validate the output file path.
        
        Args:
            path (str): The output file path to validate
            
        Returns:
            True if valid, str error message if invalid
        """
        if not path:
            return "Output directory cannot be empty"
        
        # Convert to absolute path
        path = os.path.abspath(path)
        
        # Check if the path exists and is a directory
        if os.path.exists(path):
            if not os.path.isdir(path):
                return f"Path is not a directory: {path}"
            # Check if directory is writable
            if not os.access(path, os.W_OK):
                return f"Output directory is not writable: {path}"
        else:
            # Check that the parent directory exists so it can be created
            parent = os.path.dirname(path)
            if not os.path.exists(parent):
                return f"Parent directory does not exist: {parent}"
            if not os.access(parent, os.W_OK):
                return f"Parent directory is not writable: {parent}"
        
        return True
    
    # Validation methods
    
    def _validate_input_file(self, path):
        """
        Validate the input ONNX file.
        
        Args:
            path (str): The input file path to validate
            
        Returns:
            True if valid, str error message if invalid
        """
        if not path:
            self._set_validation_error('input_file', "Input ONNX file is required")
            return False
        
        # Check if file exists
        if not os.path.exists(path):
            error_msg = f"Input file does not exist: {path}"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # Check if it's a file (not directory)
        if not os.path.isfile(path):
            error_msg = f"Input path is not a file: {path}"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # Check if file is readable
        if not os.access(path, os.R_OK):
            error_msg = f"Input file is not readable: {path}"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # Check file extension
        if not path.lower().endswith('.onnx'):
            error_msg = "Input file must have .onnx extension"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # Basic ONNX file validation - check file size (should not be empty)
        if os.path.getsize(path) == 0:
            error_msg = "Input ONNX file is empty"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # Try to read first few bytes to ensure it's at least a binary file
        try:
            with open(path, 'rb') as f:
                header = f.read(4)
                # ONNX files are protobuf format, should have some binary content
                if len(header) < 4:
                    error_msg = "Input file is too small to be a valid ONNX model"
                    self._set_validation_error('input_file', error_msg)
                    return False
        except Exception as e:
            error_msg = f"Error reading input file: {str(e)}"
            self._set_validation_error('input_file', error_msg)
            return False
        
        # All checks passed
        self._clear_validation_error('input_file')
        return True
    
    def _validate_config_file(self, path):
        """
        Validate the configuration JSON file.
        
        Args:
            path (str): The config file path to validate
            
        Returns:
            True if valid, str error message if invalid
        """
        # Skip validation if in Python mode with dataloader
        if self.execution_mode == "python" and self.python_data_source == "dataloader":
            self._clear_validation_error('config_file')
            return True
        
        if not path:
            self._set_validation_error('config_file', "Configuration file is required")
            return False
        
        # Check if file exists
        if not os.path.exists(path):
            error_msg = f"Config file does not exist: {path}"
            self._set_validation_error('config_file', error_msg)
            return False
        
        # Check if it's a file (not directory)
        if not os.path.isfile(path):
            error_msg = f"Config path is not a file: {path}"
            self._set_validation_error('config_file', error_msg)
            return False
        
        # Check if file is readable
        if not os.access(path, os.R_OK):
            error_msg = f"Config file is not readable: {path}"
            self._set_validation_error('config_file', error_msg)
            return False
        
        # Check file extension
        if not path.lower().endswith('.json'):
            error_msg = "Config file must have .json extension"
            self._set_validation_error('config_file', error_msg)
            return False
        
        # Validate JSON format
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)
                
            # Basic validation - should be a dict/object
            if not isinstance(config_data, dict):
                error_msg = "Config file must contain a JSON object"
                self._set_validation_error('config_file', error_msg)
                return False
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON format: {str(e)}"
            self._set_validation_error('config_file', error_msg)
            return False
        except Exception as e:
            error_msg = f"Error reading config file: {str(e)}"
            self._set_validation_error('config_file', error_msg)
            return False
        
        # All checks passed
        self._clear_validation_error('config_file')
        return True
    
    def _validate_node_names(self, node_list_str, field_name):
        """
        Validate node names format.
        
        Args:
            node_list_str (str): Comma-separated node names
            field_name (str): Field identifier for error tracking
            
        Returns:
            True if valid, str error message if invalid
        """
        # Empty is valid (optional field)
        if not node_list_str or not node_list_str.strip():
            self._clear_validation_error(field_name)
            return True
        
        # Split by comma and validate each node name
        node_names = [name.strip() for name in node_list_str.split(',')]
        
        # Check for empty names after splitting
        if any(not name for name in node_names):
            error_msg = "Node names cannot be empty (check for consecutive commas)"
            self._set_validation_error(field_name, error_msg)
            return False
        
        # Basic name validation - no special characters that could cause issues
        import re
        invalid_pattern = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
        
        for name in node_names:
            if invalid_pattern.search(name):
                error_msg = f"Invalid characters in node name: {name}"
                self._set_validation_error(field_name, error_msg)
                return False
        
        # All checks passed
        self._clear_validation_error(field_name)
        return True
    
    def _set_validation_error(self, field, error_message):
        """
        Record a validation error for a field.
        
        Args:
            field (str): Field identifier
            error_message (str): Error message
        """
        self.validation_errors[field] = error_message
        self._update_compile_button_state()
    
    def _clear_validation_error(self, field):
        """
        Clear validation error for a field.
        
        Args:
            field (str): Field identifier
        """
        if field in self.validation_errors:
            del self.validation_errors[field]
        self._update_compile_button_state()
    
    def _update_compile_button_state(self):
        """
        Update the compile and generate python script button states based on validation.
        
        The buttons are enabled only when:
        1. DXCom compiler is available
        2. Input ONNX file is valid
        3. Config file is valid
        4. Output path is valid
        5. No validation errors exist
        """
        # Check dxcom availability first
        if not self.dxcom_available:
            self.compile_button.setEnabled(False)
            self.compile_button.setToolTip("dxcom compiler not found - please install dxcom")
            self.gen_python_button.setEnabled(False)
            self.gen_python_button.setToolTip("dxcom compiler not found - please install dxcom")
            return
        
        # Check required fields are filled
        has_input = bool(self.input_model_path)
        has_output = bool(self.output_model_path)
        
        # Config is required UNLESS we're in Python mode with dataloader
        if self.execution_mode == "python" and self.python_data_source == "dataloader":
            has_config = True  # Not required in this mode
        else:
            has_config = bool(self.config_file_path)
        
        # Check no validation errors
        has_errors = len(self.validation_errors) > 0
        
        # Enable button only if all required fields are valid and no errors
        can_compile = has_input and has_config and has_output and not has_errors
        
        self.compile_button.setEnabled(can_compile)
        self.gen_python_button.setEnabled(can_compile)
        
        # Update tooltip
        if can_compile:
            self.compile_button.setToolTip("Click to compile ONNX model to DXNN")
            self.gen_python_button.setToolTip("Generate a Python script using dx_com.compile() API")
        else:
            # Build helpful tooltip message
            missing = []
            if not has_input:
                missing.append("Input ONNX file")
            # Only mention config if it's actually required
            if not has_config and not (self.execution_mode == "python" and self.python_data_source == "dataloader"):
                missing.append("Configuration file")
            if not has_output:
                missing.append("Output path")
            
            if missing:
                tooltip = "Missing: " + ", ".join(missing)
            elif has_errors:
                # Show first error
                first_error = list(self.validation_errors.values())[0]
                tooltip = f"Fix validation errors: {first_error}"
            else:
                tooltip = "Configure required inputs to enable compilation"
            
            self.compile_button.setToolTip(tooltip)
            self.gen_python_button.setToolTip(tooltip)
    
    def _on_input_path_changed(self):
        """Handle changes to input ONNX path (from browse dialog)."""
        path = self.input_path_field.text()
        if path:
            self._validate_input_file(path)
        else:
            self._clear_validation_error('input_file')
            self._update_compile_button_state()
        self._update_command_preview()
    
    def _on_config_path_changed(self):
        """Handle changes to config file path (from browse dialog)."""
        path = self.config_path_field.text()
        if path:
            self._validate_config_file(path)
            # Enable edit button if config file is loaded
            if self.edit_config_button and os.path.exists(path):
                self.edit_config_button.setEnabled(True)
            # Sync calib widgets to values already in the JSON
            if os.path.isfile(path):
                try:
                    import json as _json
                    with open(path, 'r') as _f:
                        _cfg = _json.load(_f)
                    _method = _cfg.get('calibration_method', 'ema')
                    _idx = self.calib_method_combo.findData(_method)
                    if _idx >= 0:
                        self.calib_method_combo.blockSignals(True)
                        self.calib_method_combo.setCurrentIndex(_idx)
                        self.calib_method_combo.blockSignals(False)
                    _num = _cfg.get('calibration_num', 100)
                    self.calib_num_spinbox.blockSignals(True)
                    self.calib_num_spinbox.setValue(int(_num))
                    self.calib_num_spinbox.blockSignals(False)
                except Exception:
                    pass
                self._load_default_loader_from_config()
        else:
            self._clear_validation_error('config_file')
            if self.edit_config_button:
                self.edit_config_button.setEnabled(False)
        self._update_command_preview()
        self._update_compile_button_state()
    
    def _write_calib_to_config(self):
        """Write current Calibration Method and Calibration Samples into the JSON config file."""
        if not self.config_file_path or not os.path.isfile(self.config_file_path):
            return
        try:
            import json as _json
            with open(self.config_file_path, 'r') as _f:
                _cfg = _json.load(_f)
            _cfg['calibration_method'] = self.calib_method_combo.currentData()
            _cfg['calibration_num'] = self.calib_num_spinbox.value()
            with open(self.config_file_path, 'w') as _f:
                _json.dump(_cfg, _f, indent=2)
        except Exception as _e:
            self.set_status_message(f"Warning: could not update config file: {_e}", 3000)

    def _on_calib_setting_changed(self):
        """Write calib changes immediately into the JSON config file when one is loaded."""
        self._write_calib_to_config()
        self._update_command_preview()

    def _on_edit_config_file(self):
        """Open JSON configuration editor dialog."""
        if not self.config_file_path or not os.path.exists(self.config_file_path):
            QMessageBox.warning(
                self,
                "No Config File",
                "Please select a configuration JSON file first."
            )
            return

        # Flush current calib/default_loader settings into the file before opening editor
        self._write_calib_to_config()
        self._write_default_loader_to_config()

        # Import and open dialog
        from .json_config_dialog import JsonConfigDialog

        dialog = JsonConfigDialog(self.config_file_path, self)
        dialog.show()  # Non-modal
    
    def _on_input_nodes_changed(self):
        """Handle changes to input nodes field."""
        text = self.compile_input_nodes_field.text()
        is_valid = self._validate_node_names(text, 'input_nodes')
        
        # Visual feedback
        if text.strip() and not is_valid:
            self.compile_input_nodes_field.setStyleSheet("border: 1px solid #ff6b6b;")
        else:
            self.compile_input_nodes_field.setStyleSheet("")
        self._update_command_preview()
    
    def _on_output_nodes_changed(self):
        """Handle changes to output nodes field."""
        text = self.compile_output_nodes_field.text()
        is_valid = self._validate_node_names(text, 'output_nodes')
        
        # Visual feedback
        if text.strip() and not is_valid:
            self.compile_output_nodes_field.setStyleSheet("border: 1px solid #ff6b6b;")
        else:
            self.compile_output_nodes_field.setStyleSheet("")
        self._update_command_preview()
        if text.strip() and not is_valid:
            self.compile_output_nodes_field.setStyleSheet("border: 1px solid #ff6b6b;")
        else:
            self.compile_output_nodes_field.setStyleSheet("")
    
    def get_validation_errors(self):
        """
        Get current validation errors.
        
        Returns:
            dict: Dictionary of field -> error message
        """
        return self.validation_errors.copy()
    
    def is_ready_to_compile(self):
        """
        Check if all inputs are valid and ready for compilation.
        
        Returns:
            bool: True if ready to compile, False otherwise
        """
        return self.compile_button.isEnabled()
    
    
    def _on_about(self):
        """Show About dialog."""
        about_text = f"""
        <h2>DXCom GUI</h2>
        <p><b>Version:</b> {self.VERSION}</p>
        <p><b>Company:</b> {self.COMPANY}</p>
        <p>ONNX to DXNN Compiler GUI Wrapper</p>
        <p>A graphical interface for the dxcom compiler toolchain.</p>
        <p>© 2026 {self.COMPANY}. All rights reserved.</p>
        """
        QMessageBox.about(self, "About DXCom GUI", about_text)
    
    def _on_check_dxcom_status(self):
        """Show DXCom availability, version, and environment validation information."""
        from .dxcom_detector import refresh_dxcom_detection
        from .environment_validator import clear_validation_cache
        
        # Refresh detection and validation
        refresh_dxcom_detection()
        clear_validation_cache()
        dxcom_info = check_dxcom_available()
        validation = validate_environment()
        
        if dxcom_info.is_valid():
            # Build status text with validation results
            status_text = f"""
            <h3>DXCom Compiler Status</h3>
            <p><b>Status:</b> <span style="color: green;">✓ Available</span></p>
            <p><b>Path:</b> {dxcom_info.path}</p>
            <p><b>Version:</b> {dxcom_info.version or 'Unknown'}</p>
            """
            
            # Add environment validation results
            status_text += "<h4>Environment Validation:</h4>"
            
            if validation.overall_valid:
                status_text += '<p style="color: green;">✓ All checks passed</p>'
            else:
                status_text += '<p style="color: red;">✗ Some checks failed</p>'
            
            # List all checks
            status_text += "<ul>"
            for check in validation.checks:
                if check.passed:
                    icon = "✓"
                    color = "green" if check.severity == "info" else "orange"
                else:
                    icon = "✗"
                    color = "red"
                
                status_text += f'<li><span style="color: {color};">{icon} {check.message}</span></li>'
            status_text += "</ul>"
            
            if validation.errors:
                status_text += "<p><b>Note:</b> Compilation will be disabled until errors are resolved.</p>"
            elif validation.warnings:
                status_text += "<p><b>Note:</b> Warnings present but compilation is allowed.</p>"
            else:
                status_text += "<p>The environment is ready for compilation.</p>"
            
            # Show appropriate dialog based on validation
            if validation.overall_valid:
                QMessageBox.information(self, "DXCom Status", status_text)
            else:
                QMessageBox.warning(self, "DXCom Status", status_text)
            
            # Update internal state
            self.dxcom_available = validation.overall_valid
            self._update_compile_button_state()
            
            if validation.overall_valid:
                self.set_status_message(f"dxcom detected: {dxcom_info.version or 'installed'}")
            else:
                self.set_status_message("Warning: Environment validation failed")
        else:
            # Error - show warning
            status_text = f"""
            <h3>DXCom Compiler Status</h3>
            <p><b>Status:</b> <span style="color: red;">✗ Not Available</span></p>
            <p><b>Error:</b> {dxcom_info.error_message}</p>
            <hr>
            <p>Please install the DEEPX dxcom compiler and ensure it is in your system PATH.</p>
            <p>After installation, use this menu to re-check the status.</p>
            """
            QMessageBox.warning(self, "DXCom Status", status_text)
            
            # Update internal state
            self.dxcom_available = False
            self._update_compile_button_state()
            self.set_status_message("Warning: dxcom compiler not found")
    
    # Phase 6: Advanced Features
    
    def _update_recent_files_menu(self):
        """Update the recent files menu."""
        self.recent_files_menu.clear()
        
        recent_files = self.settings_manager.get_recent_files()
        
        if not recent_files:
            no_recent_action = QAction("No Recent Files", self)
            no_recent_action.setEnabled(False)
            self.recent_files_menu.addAction(no_recent_action)
        else:
            for file_path in recent_files:
                # Show just filename with directory hint and file type indicator
                file_name = os.path.basename(file_path)
                dir_name = os.path.basename(os.path.dirname(file_path))
                
                # Add file type indicator
                if file_path.endswith('.json'):
                    display_name = f"⚙ {file_name} ({dir_name})"
                else:
                    display_name = f"📄 {file_name} ({dir_name})"
                
                action = QAction(display_name, self)
                action.setData(file_path)
                action.triggered.connect(lambda checked, path=file_path: self._on_open_recent_file(path))
                self.recent_files_menu.addAction(action)
            
            self.recent_files_menu.addSeparator()
            clear_action = QAction("Clear Recent Files", self)
            clear_action.triggered.connect(self._on_clear_recent_files)
            self.recent_files_menu.addAction(clear_action)
    
    def _on_open_recent_file(self, file_path):
        """Open a recent file (ONNX or JSON)."""
        if os.path.exists(file_path):
            # Determine file type and handle accordingly
            if file_path.endswith('.json'):
                # Handle JSON config file
                self.config_file_path = file_path
                self.config_path_field.setText(file_path)
                
                # Remember the directory for next time
                self.last_browse_directory = os.path.dirname(file_path)
                
                # Add to recent files (moves it to top)
                self.settings_manager.add_recent_file(file_path)
                self._update_recent_files_menu()
                
                # Validate the config file
                self._validate_config_file(file_path)
                
                # Update status bar
                self.set_status_message(f"Loaded config file: {os.path.basename(file_path)}")
                
            else:
                # Handle ONNX file
                self.batch_mode = False
                self.batch_files = []
                self.input_model_path = file_path
                self.input_path_field.setText(file_path)
                
                # Remember the directory for next time
                self.last_browse_directory = os.path.dirname(file_path)
                
                # Add to recent files (moves it to top)
                self.settings_manager.add_recent_file(file_path)
                self._update_recent_files_menu()
                
                # Auto-suggest output path based on input file
                self._suggest_output_path(file_path)
                
                # Validate the input file
                self._validate_input_file(file_path)
        else:
            QMessageBox.warning(
                self, "File Not Found",
                f"The file no longer exists:\n{file_path}"
            )
            # Remove from recent files
            self.settings_manager.recent_files = [f for f in self.settings_manager.recent_files if f != file_path]
            self.settings_manager._save_recent_files()
            self._update_recent_files_menu()
    
    def _on_clear_recent_files(self):
        """Clear recent files history."""
        reply = QMessageBox.question(
            self, "Clear Recent Files",
            "Are you sure you want to clear recent files history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.settings_manager.clear_recent_files()
            self._update_recent_files_menu()
    
    def _on_open_batch_files(self):
        """Open multiple ONNX files for batch processing."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select ONNX Files for Batch Processing",
            self.last_browse_directory,
            "ONNX Files (*.onnx);;All Files (*)"
        )
        
        if files:
            self.batch_mode = True
            self.batch_files = files
            self.last_browse_directory = os.path.dirname(files[0])
            
            # Show batch info
            batch_info = f"Batch Mode: {len(files)} files selected"
            self.log(batch_info)
            for i, f in enumerate(files, 1):
                self.log(f"  {i}. {os.path.basename(f)}")
            
            # For batch mode, update input field to show first file
            self.input_model_path = files[0]
            self.input_path_field.setText(f"{len(files)} files selected (batch mode)")
            
            # Update compile button text
            if self.compile_button:
                self.compile_button.setText(f"Compile {len(files)} Files")
    
    def _on_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.exec()
    
    def _update_tab_styles(self, theme: str):
        """Update toggle button styles based on current theme."""
        if not hasattr(self, 'mode_btn_container') or self.mode_btn_container is None:
            return

        # Define theme-specific colors
        if theme == 'light':
            active_bg = '#0078d4'
            active_color = '#ffffff'
            inactive_bg = '#e5e5e5'
            inactive_color = '#000000'
            hover_bg = '#d0d0d0'
            border_color = '#cccccc'
        else:  # dark
            active_bg = '#0078d4'
            active_color = '#ffffff'
            inactive_bg = '#2d2d2d'
            inactive_color = '#e0e0e0'
            hover_bg = '#3f3f3f'
            border_color = '#3f3f3f'

        def _make_css(left, right):
            return f"""
            QPushButton[objectName="{left}"],
            QPushButton[objectName="{right}"] {{
                padding: 6px 20px;
                font-weight: bold;
                border: 1px solid {border_color};
                background: {inactive_bg};
                color: {inactive_color};
            }}
            QPushButton[objectName="{left}"] {{
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                border-right: none;
            }}
            QPushButton[objectName="{right}"] {{
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
            QPushButton[objectName="{left}"]:checked,
            QPushButton[objectName="{right}"]:checked {{
                background: {active_bg};
                color: {active_color};
                border-color: {active_bg};
            }}
            QPushButton[objectName="{left}"]:hover:!checked,
            QPushButton[objectName="{right}"]:hover:!checked {{
                background: {hover_bg};
            }}
        """

        self.mode_btn_container.setStyleSheet(
            _make_css("modeToggleLeft", "modeToggleRight")
        )
        if hasattr(self, 'data_src_btn_container') and self.data_src_btn_container:
            self.data_src_btn_container.setStyleSheet(
                _make_css("dataToggleLeft", "dataToggleRight")
            )

    def _on_toggle_theme(self):
        """Toggle between light and dark theme."""
        current_theme = self.settings_manager.get('theme', 'light')
        new_theme = 'dark' if current_theme == 'light' else 'light'
        self.settings_manager.set('theme', new_theme)
        self.apply_theme(new_theme)
    
    def apply_theme(self, theme: str):
        """Apply the specified theme."""
        stylesheet = get_theme_stylesheet(theme)
        self.setStyleSheet(stylesheet)
        
        # Update tab widget styles
        self._update_tab_styles(theme)
        
        # Update header separator color
        if hasattr(self, 'header_separator') and self.header_separator is not None:
            if theme == 'light':
                self.header_separator.setFixedHeight(2)
                self.header_separator.setStyleSheet("background-color: #cccccc;")
                self.header_separator.setVisible(True)
            else:  # dark - show separator with dark color
                self.header_separator.setFixedHeight(2)
                self.header_separator.setStyleSheet("background-color: #3f3f3f;")
                self.header_separator.setVisible(True)
        
        # Update theme toggle action text
        if hasattr(self, 'theme_action'):
            if theme == 'light':
                self.theme_action.setText("Switch to &Dark Theme")
            else:
                self.theme_action.setText("Switch to &Light Theme")

    def set_dxcom_path(self, path: str):
        """Override the dxcom executable path (from --dxcom-path CLI arg)."""
        from .dxcom_detector import set_custom_dxcom_path, refresh_dxcom_detection
        set_custom_dxcom_path(path)
        refresh_dxcom_detection()

    def _on_show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
        <h3>Keyboard Shortcuts</h3>
        <table cellpadding="5">
        <tr><td><b>Ctrl+O</b></td><td>Open ONNX File</td></tr>
        <tr><td><b>Ctrl+J</b></td><td>Open JSON Config</td></tr>
        <tr><td><b>Ctrl+R</b></td><td>Run Compilation</td></tr>
        <tr><td><b>Ctrl+T</b></td><td>Toggle Theme</td></tr>
        <tr><td><b>Ctrl+,</b></td><td>Open Settings</td></tr>
        <tr><td><b>Ctrl+Q</b></td><td>Quit Application</td></tr>
        <tr><td><b>F1</b></td><td>Show Keyboard Shortcuts</td></tr>
        </table>
        """
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def _update_command_preview(self):
        """Update the command preview display."""
        if not self.input_model_path or not self.output_model_path:
            self.command_preview_field.setText("")
            self.command_preview_field.setPlaceholderText("Configure inputs to see the command...")
            return
        
        try:
            # Check execution mode
            if self.execution_mode == "python":
                # Python mode: show Python script execution command
                import os
                import sys
                python_executable = sys.executable
                if self.saved_python_script_path and os.path.exists(self.saved_python_script_path):
                    command_str = f"{python_executable} {self.saved_python_script_path}"
                else:
                    command_str = f"{python_executable} /tmp/tmp_dx_com.py  # Will be generated"
                self.command_preview_field.setText(command_str)
            else:
                # CLI mode: Build command using the same logic as dxcom_wrapper
                cmd = ['dxcom']
                
                # Required: Model path (-m)
                cmd.extend(['-m', self.input_model_path])
                
                # Required: Output directory (-o)
                output_dir = self.output_model_path
                if not output_dir:
                    output_dir = '.'
                cmd.extend(['-o', output_dir])
                
                # Configuration file
                if self.config_file_path:
                    cmd.extend(['-c', self.config_file_path])
                
                # Optimization level
                opt_level = self.opt_level_combo.currentData() if self.opt_level_combo else 0
                cmd.extend(['--opt_level', str(opt_level)])
                
                # Boolean flags
                if self.gen_log_checkbox and self.gen_log_checkbox.isChecked():
                    cmd.append('--gen_log')
                
                if self.aggressive_partitioning_checkbox and self.aggressive_partitioning_checkbox.isChecked():
                    cmd.append('--aggressive_partitioning')
                
                # Optional node specifications
                if self.compile_input_nodes_field and self.compile_input_nodes_field.text().strip():
                    cmd.extend(['--compile_input_nodes', self.compile_input_nodes_field.text().strip()])
                
                if self.compile_output_nodes_field and self.compile_output_nodes_field.text().strip():
                    cmd.extend(['--compile_output_nodes', self.compile_output_nodes_field.text().strip()])
                
                # Convert to string for display
                command_str = ' '.join(cmd)
                self.command_preview_field.setText(command_str)
        except Exception as e:
            self.command_preview_field.setText(f"Error generating command: {e}")
    
    def _on_copy_command(self):
        """Copy the command preview to clipboard."""
        from PySide6.QtWidgets import QApplication
        command = self.command_preview_field.text()
        if command and not command.startswith("Error"):
            QApplication.clipboard().setText(command)
            self.set_status_message("Command copied to clipboard!", 2000)
        else:
            self.set_status_message("No valid command to copy", 2000)
    
    def _on_generate_python_script(self):
        """Generate and show a Python script using dx_com.compile() API."""
        import os
        
        # Get current options
        options = self.get_compiler_options()
        
        # Determine default filename
        default_name = "compile_model.py"
        if self.input_model_path:
            base_name = os.path.splitext(os.path.basename(self.input_model_path))[0]
            default_name = f"compile_{base_name}.py"
        
        # Use the shared script generation method
        script_content = self._generate_python_script_content(options)
        
        # Show the script in an editable dialog
        dialog = PythonScriptDialog(script_content, default_name, self)
        dialog.exec()
        
        # If user saved the script, store the path for compilation
        if dialog.saved_file_path:
            self.saved_python_script_path = dialog.saved_file_path
            self.set_status_message(f"Python script saved: {os.path.basename(dialog.saved_file_path)}", 3000)
            # Update command preview to show the saved script path
            self._update_command_preview()

