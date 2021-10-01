import os

from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import (
    Qt,
    QSize,
)
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QPushButton,
    QSystemTrayIcon,
    QAction,
    QWidget,
    QTabWidget,
    QDockWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
    QTextEdit,
    QListWidget,
    QMessageBox,
    QDesktopWidget,
)

from app.gui.utils import (
    HCollapsibleBox,
    FileBrowserWidget,
    TableWidget,
    IconLabel,
)
from app.gui.blast_widget import BlastWidget
from app.gui.blat_widget import BlatWidget
from app.gui.orf_widget import ORFWidget
from app.gui.fasta_widget import FastaWidget
from app.gui.help_widget import HelpWidget
from app.tools.config import APP_NAME, config
from app.tools.utils import (
    init_tool,
    is_fastx_file,
    is_table_file,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.geometry = None
        # self.sequence_window = None
        # self.process_dialog = None

        # first check
        init_tool()

        self.setWindowTitle(APP_NAME)
        self.set_menubar()
        # set_toolbar()
        # self.set_statusbar()

        self.set_window()

        self.init_ui()

    def set_window(self):
        app = QApplication.instance()
        screen = app.primaryScreen()

        app_icon = QIcon()
        app_icon.addFile(os.path.join(config['img'], 'helix512.png'), QSize(512, 512))
        app_icon.addFile(os.path.join(config['img'], 'helix256.png'), QSize(256, 256))
        app_icon.addFile(os.path.join(config['img'], 'helix128.png'), QSize(128, 128))
        app_icon.addFile(os.path.join(config['img'], 'helix64.png'), QSize(64, 64))
        app_icon.addFile(os.path.join(config['img'], 'helix32.png'), QSize(32, 32))
        app_icon.addFile(os.path.join(config['img'], 'helix24.png'), QSize(24, 24))
        app_icon.addFile(os.path.join(config['img'], 'helix16.png'), QSize(16, 16))
        self.setWindowIcon(app_icon)

        self.geometry = screen.availableGeometry()
        self.setMinimumSize(self.geometry.width() * 0.8, self.geometry.height() * 0.7)
        # self.resize(self.geometry.width() * 0.8, self.geometry.height() * 0.6)
        # self.resize(self.geometry.width() * 0.5, self.geometry.height() * 0.6)

        # Create the tray
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon(os.path.join(config['img'], 'helix512.png')))
        tray.setVisible(True)

        self.setStyleSheet('''
                            QToolTip { 
                                background-color: white; 
                                color: black; 
                                border: 2px solid darkkhaki;
                                padding: 5px;
                                border-radius: 50%;
                                
                            }
                            QWidget {
                                /*font: 11pt Comic Sans MS*/;
                                /*font: 11pt;*/
                                }
                           ''')

        win = self.frameGeometry()
        pos = self.geometry.center()
        win.moveCenter(pos)
        self.move(win.topLeft())
        self.show()


    def set_toolbar(self):
        toolbar = QToolBar("Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

    def set_menubar(self):
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        file_menu = menu_bar.addMenu('&File')

        self.exit_action = QAction('Exit')
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.setStatusTip('Exit application')
        self.exit_action.triggered.connect(QApplication.instance().quit)
        file_menu.addAction(self.exit_action)

        tools_menu = menu_bar.addMenu('&Tools')
        self.blast_action = QAction('&Blast')
        self.blast_action.setShortcut('Ctrl+b')
        self.blast_action.triggered.connect(self.blast_widget)
        tools_menu.addAction(self.blast_action)
        self.blat_action = QAction('Bl&at')
        self.blat_action.setShortcut('Ctrl+a')
        self.blat_action.triggered.connect(self.blat_widget)
        tools_menu.addAction(self.blat_action)
        self.orf_action = QAction('O&RF')
        self.orf_action.setShortcut('Ctrl+r')
        self.orf_action.triggered.connect(self.orf_widget)
        tools_menu.addAction(self.orf_action)
        self.fasta_action = QAction('&File Manipulation')
        self.fasta_action.setShortcut('Ctrl+f')
        self.fasta_action.triggered.connect(self.fasta_widget)
        tools_menu.addAction(self.fasta_action)

        view_menu = menu_bar.addMenu('&View')
        self.right_position_log_view_action = QAction('Right', checkable=True)
        # self.right_position_log_view_action.setStatusTip('Position righShow log')
        self.right_position_log_view_action.setChecked(True)
        self.right_position_log_view_action.triggered.connect(self.right_position_toggle_log_view)
        view_menu.addAction(self.right_position_log_view_action)

        self.bottom_position_log_view_action = QAction('Bottom', checkable=True)
        # self.bottom_position_log_view_action.setStatusTip('Show log')
        self.bottom_position_log_view_action.setChecked(False)
        self.bottom_position_log_view_action.triggered.connect(self.bottom_position_toggle_log_view)
        view_menu.addAction(self.bottom_position_log_view_action)

        help_menu = menu_bar.addMenu('&Help')
        self.about_action = QAction('About')
        self.about_action.triggered.connect(self.show_about_action)
        help_menu.addAction(self.about_action)
        # self.help_show_action = QAction('Show', checkable=True)
        # # self.help_show_action.triggered.connect(self.help_show_toggle)
        # help_menu.addAction(self.help_show_action)

    def show_about_action(self):
        msg = '{}\n version 1.0.4\n'.format(APP_NAME)
        QMessageBox.about(self, 'About', msg)

    def right_position_toggle_log_view(self):
        if self.right_position_log_view_action.isChecked():
            self.bottom_position_log_view_action.setChecked(False)
            self.dock_widget.show()
            self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
        else:
            self.dock_widget.hide()

    def bottom_position_toggle_log_view(self):
        if self.bottom_position_log_view_action.isChecked():
            self.right_position_log_view_action.setChecked(False)
            self.dock_widget.show()
            self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget)
        else:
            self.dock_widget.hide()

    def set_statusbar(self):
        self.setStatusBar(QStatusBar(self))

    def init_ui(self):
        self.btn_blast = QPushButton('&Blast', self)
        # self.btn_blast.resize(100,32)
        # self.btn_blast.setFont(QFont('Times', 15))
        self.btn_blast.clicked.connect(self.blast_widget)

        self.btn_blat = QPushButton('Bl&at', self)
        self.btn_blat.clicked.connect(self.blat_widget)

        self.btn_orf = QPushButton('O&RF', self)
        self.btn_orf.clicked.connect(self.orf_widget)

        self.btn_fasta = QPushButton('&File Manipulation', self)
        self.btn_fasta.clicked.connect(self.fasta_widget)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        left_layout.addWidget(self.btn_blast)
        left_layout.addWidget(self.btn_blat)
        left_layout.addWidget(self.btn_orf)
        left_layout.addWidget(self.btn_fasta)

        main_layout = QHBoxLayout()

        more_options_box = HCollapsibleBox('main')
        more_options_box.setContentLayout(left_layout)
        main_layout.addWidget(more_options_box)


        # right widget
        submain_layout = QVBoxLayout()
        submain_layout.addWidget(IconLabel('It would take several seconds to read and write data. Please be patient until you see “OK” dialogue box for each step.', img='chronometer.png'))

        self.blastStack = BlastWidget(window=self)
        self.blatStack = BlatWidget(window=self)
        self.orfStack = ORFWidget(window=self)
        self.fastaStack = FastaWidget(window=self)

        self.right_menu_stack = QStackedWidget()
        self.right_menu_stack.addWidget(self.blastStack)
        self.right_menu_stack.addWidget(self.blatStack)
        self.right_menu_stack.addWidget(self.orfStack)
        self.right_menu_stack.addWidget(self.fastaStack)

        self.right_menu_stack.setCurrentIndex(0)

        submain_layout.addWidget(self.right_menu_stack)

        right_layout = QWidget()
        right_layout.setLayout(submain_layout)
        
        main_layout.addWidget(right_layout)
        main_layout.setStretch(1, 1)
        # main_layout.setStretch(1, 200)
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        self.init_system_log_widget()

    def init_system_log_widget(self):
        self.dock_widget = QDockWidget('')
        self.dock_widget.setMinimumWidth(self.geometry.width() * 0.25)

        self.system_log_tab_widget = QTabWidget()
        self.system_log_tab_widget.tabBar().setObjectName("system_log_tab_widget_tab")

        self.project_folder_widget = FileBrowserWidget(window=self)
        self.system_help_widget = HelpWidget()
        # self.system_help_widget =  QWebEngineView()
        self.system_log_log_widget = QTextEdit()

        self.system_log_tab_widget.addTab(self.project_folder_widget, 'Project Folder')
        self.system_log_tab_widget.addTab(self.system_help_widget, 'Help')
        self.system_log_tab_widget.addTab(self.system_log_log_widget, 'Log')

        self.system_log_tab_widget.setCurrentIndex(0)

        self.dock_widget.setWidget(self.system_log_tab_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)

    def blast_widget(self):
        self.right_menu_stack.setCurrentIndex(0)

    def blat_widget(self):
        self.right_menu_stack.setCurrentIndex(1)

    def orf_widget(self):
        self.right_menu_stack.setCurrentIndex(2)

    def fasta_widget(self):
        self.right_menu_stack.setCurrentIndex(3)

    def update_log(self, msg):
        # self.system_log_tab_widget.setCurrentIndex(1)
        self.system_log_log_widget.insertPlainText(msg + '\n')
        self.system_log_log_widget.ensureCursorVisible()