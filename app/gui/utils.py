import os
import shutil
import gzip

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QProcess
from PyQt5.QtCore import QAbstractTableModel

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QToolButton
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QScrollArea

from app.tools.config import config, preference
from app.tools.utils import write_config, project_folder_path, open_default_application, \
                                    project_folder_path, get_ext, is_fasta_file, get_fasta_info, \
                                    open_default_texteditor
from app.tools.biofiles import open_blast_result_as_table, open_psl_as_table


def is_valid(widget, infilepath, msg=None):
    if not infilepath or not os.path.exists(infilepath):
        _msg = msg + ' The selected file or folder might not be found.' if msg else 'Please check that you supplied the correct filename or folder. The selected file or folder could not be found.'
        QMessageBox.about(widget, 'Information', _msg)
        return False
    return True


class IconLabel(QWidget):

    IconSize = QSize(16, 16)
    HorizontalSpacing = 2

    def __init__(self, text, final_stretch=True, img='bulb.png'):
        super(QWidget, self).__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        icon = QLabel()
        pixmap = QPixmap(os.path.join(config['img'], img))
        icon.setPixmap(pixmap)

        layout.addWidget(icon)
        layout.addSpacing(self.HorizontalSpacing)
        layout.addWidget(QLabel(text))

        if final_stretch:
            layout.addStretch()


class QProcessWidgetUtil:
    """Run qprocess with command
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qprocess = None
        self.error_msg = None
        self.final_msg = ''
        self.qprocess_button_label = ''

    def qprocess_start(self, cmd, options, final_msg=''):
        if self.qprocess:
            self.process_log('Another qprocess is executing...')
            return
        
        self.qprocess = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
        self.qprocess.readyReadStandardOutput.connect(self.handle_stdout)
        self.qprocess.readyReadStandardError.connect(self.handle_stderr)
        self.qprocess.stateChanged.connect(self.handle_state)
        self.qprocess.finished.connect(self.qprocess_finished)  # Clean up once complete.

        self.qprocess_button_label = self.qprocess_button.text()

        self.qprocess_button.setText('Processing...')
        self.qprocess_button.setEnabled(False)
        query = cmd + ' ' + ' '.join(options)
        self.process_log('Command ========================\n {}'.format(query))
        self.final_msg = final_msg
        self.qprocess.start(query)

    def handle_stderr(self):
        data = self.qprocess.readAllStandardError()
        self.error_msg = bytes(data).decode('utf8')
        self.process_log('Error:' + self.error_msg)

    def handle_stdout(self):
        data = self.qprocess.readAllStandardOutput()
        stdout = bytes(data).decode('utf8')
        if stdout:
            self.process_log(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]

    def qprocess_finished(self):
        if self.error_msg:
            msg = self.error_msg
        else:
            msg = self.final_msg if self.final_msg else 'Finished.'

        QMessageBox.about(self, 'Information', msg)

        self.qprocess_button.setText(self.qprocess_button_label)
        self.qprocess_button.setEnabled(True)
        self.qprocess = None
        self.error_msg = None
        # self.reset()


class BaseWidgetUtil:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_log(self, msg):
        self.window.update_log(msg)

    def resetWidget(self):
        w_list = self.findChildren(QWidget)
        for w in w_list:
            if w.__class__.__name__ == 'QTextEdit':
                w.setText('')
            if w.__class__.__name__ == 'QLineEdit':
                w.setText('')
            if w.__class__.__name__ == 'QComboBox':
                w.setCurrentIndex(0)

    def extract(self, infilepath, msg=None, btn=None):
        filepath, ext = os.path.splitext(infilepath)

        if ext != '.gz' and ext != '.zip':
            return infilepath
        
        _msg = 'Do you want to extract this file and proceed with your work?' if not msg else msg
            
        reply = QMessageBox.question(self, 'Extract a file',
                                    _msg,
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        if reply == QMessageBox.Yes:

            button_label = None
            if btn:
                button_label = btn.text()
                btn.setText('Processing...')
                btn.setEnabled(False)

            with gzip.open(infilepath, 'rb') as f_in:
                with open(filepath, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            if btn:
                btn.setText(button_label)
                btn.setEnabled(True)            

            return filepath

        return False


class TableView(QTableView):
    def __init__(self, data=None, header=None):
        super(TableView, self).__init__()
        if data == None:
            return
        self.fileModel = TableModel(data, header)
        self.setModel(self.fileModel)
        self.setAlternatingRowColors(True)
        self.resizeColumnsToContents()

    def scretch_header(self):
        for i in range(self.horizontalHeader().count()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            # self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)


class TableModel(QAbstractTableModel):
    def __init__(self, data=None, header=None):
        super().__init__()
        self._data = data
        self._header = header

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data[index.row()][index.column()]
            return str(value)

    def rowCount(self, index):
        # return self._data.shape[0]
        if len(self._data) == 0:
            return 0
        return len(self._data)


    def columnCount(self, index):
        # return self._data.shape[1]
        if len(self._data) == 0:
            return 0
        return len(self._data[0])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if self._header and role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._header[section])

            if orientation == Qt.Vertical:
                return str(section)

    def get_row(self, index):
        return self._data[index]


class PDTableView(QTableView):
    def __init__(self, pd_data=None):
        super(PDTableView, self).__init__()
        if pd_data == None:
            return
        self.fileModel = TableModel(pd_data)
        self.setModel(self.fileModel)
        self.setAlternatingRowColors(True)
        
        # self.resizeColumnsToContents()

    def scretch_header(self):
        for i in range(self.horizontalHeader().count()):
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
            # self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)


class PDTableModel(QAbstractTableModel):
    def __init__(self, data=None, header=None):
        super(PDTableModel, self).__init__()
        self._data = data
        self._header = header

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._header[section])

            # if orientation == Qt.Vertical:
            #     return str(self._data.index[section])

    def get_row(self, index):
        return self._data.iloc[index].tolist()


class CollapsibleBox(QWidget):
    def __init__(self, title='', parent=None):
        super(CollapsibleBox, self).__init__(parent)

        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet('QToolButton { border: none; }')
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(maximumHeight=0, minimumHeight=0)
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self, b'minimumHeight'))
        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self, b'maximumHeight'))
        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self.content_area, b'maximumHeight'))

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        
        arrow = QtCore.Qt.DownArrow if not checked else QtCore.Qt.RightArrow
        self.toggle_button.setArrowType(arrow)

        direction = QtCore.QAbstractAnimation.Forward if not checked else QtCore.QAbstractAnimation.Backward
        self.toggle_animation.setDirection(direction)
        
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        
        content_height = layout.sizeHint().height()
        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class HCollapsibleBox(QWidget):
    def __init__(self, title='title', parent=None):
        super(HCollapsibleBox, self).__init__(parent)

        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet('QToolButton { border: none; }')
        self.toggle_button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)
        self.toggle_button.setAutoRaise(True)
        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        # self.content_area = QtWidgets.QScrollArea(maximumWidth=100, minimumWidth=100)
        self.content_area = QtWidgets.QScrollArea(maximumWidth=0)
        self.content_area.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout2 = QVBoxLayout(self)
        layout2.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout2.addWidget(self.toggle_button)
        layout.addLayout(layout2)
        layout.addWidget(self.content_area)

        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self, b'minimumWidth'))
        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self, b'maximumWidth'))
        self.toggle_animation.addAnimation(QtCore.QPropertyAnimation(self.content_area, b'maximumWidth'))

    @QtCore.pyqtSlot()
    def on_pressed(self):
        checked = self.toggle_button.isChecked()
        
        arrow = QtCore.Qt.LeftArrow if not checked else QtCore.Qt.RightArrow
        self.toggle_button.setArrowType(arrow)

        direction = QtCore.QAbstractAnimation.Forward if not checked else QtCore.QAbstractAnimation.Backward
        self.toggle_animation.setDirection(direction)
        
        self.toggle_animation.start()

    def setContentLayout(self, layout):
        lay = self.content_area.layout()
        del lay
        self.content_area.setLayout(layout)
        # collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        collapsed_height = self.sizeHint().width() - self.content_area.maximumWidth()
        
        content_height = layout.sizeHint().width()

        for i in range(self.toggle_animation.animationCount()):
            animation = self.toggle_animation.animationAt(i)
            animation.setDuration(500)
            animation.setStartValue(collapsed_height)
            animation.setEndValue(collapsed_height + content_height)

        content_animation = self.toggle_animation.animationAt(self.toggle_animation.animationCount() - 1)
        content_animation.setDuration(500)
        content_animation.setStartValue(0)
        content_animation.setEndValue(content_height)


class FileBrowserWidget(QWidget, BaseWidgetUtil):
    def __init__(self, data=None, window=None, parent=None):
        super(FileBrowserWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        blastresult_first_layout = QHBoxLayout()

        browser_file_label = QLabel('Project Folder')
        blastresult_first_layout.addWidget(browser_file_label)

        self.project_folder_editor = QLineEdit()
        self.project_folder_editor.setMinimumWidth(100)
        blastresult_first_layout.addWidget(self.project_folder_editor)

        browser_project_button = QPushButton('Browse')
        blastresult_first_layout.addWidget(browser_project_button)

        browser_project_button.clicked.connect(self.browse_project)

        set_project_button = QPushButton('Set Project')
        blastresult_first_layout.addWidget(set_project_button)

        set_project_button.clicked.connect(self.set_project)

        main_layout.addLayout(blastresult_first_layout)

        self.fileModel = QFileSystemModel()
        self.fileModel.setRootPath('')
        self.treeView = QTreeView()
        self.treeView.setAlternatingRowColors(True)
        self.treeView.setModel(self.fileModel)
        self.treeView.doubleClicked.connect(self.tree_cilcked)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        
        self.treeView.header().resizeSection(0, 250)
        self.treeView.header().setStretchLastSection(True)
        self.treeView.setSortingEnabled(True)
        
        layout = QHBoxLayout()

        layout.addWidget(self.treeView)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)

        self.init_project()

    def open_menu(self, position):
        file_index = self.treeView.indexAt(position)
        path = self.fileModel.fileInfo(file_index).absoluteFilePath() if file_index.isValid() else project_folder_path()

        menu = QtWidgets.QMenu(self)
        
        if file_index.isValid():
            get_fasta_information_action = menu.addAction('Get Fasta Information')
            open_texteditor_action = menu.addAction('Open With Text Editor')
            delete_action = menu.addAction('Delete')
        
        create_folder_action = menu.addAction('Create Folder')

        action = menu.exec_(self.treeView.viewport().mapToGlobal(position))

        if file_index.isValid():
            if action == get_fasta_information_action:
                self.get_fasta_information(path)
            if action == open_texteditor_action:
                self.open_texteditor(path)
            if action == delete_action:
                self.delete_this(path)

        if action == create_folder_action:
            self.create_folder(path)

    def get_fasta_information(self, path):
        if is_fasta_file(path):
            try:
                fasta_info = get_fasta_info(path)
                res = '\n'.join('{} : {}'.format(key, val) for key, val in fasta_info.items())

                dlg = QMessageBox(self)
                dlg.setWindowTitle('Fasta Information')
                dlg.setText(res)
                button = dlg.exec()
            except Exception as e:
                QMessageBox.about(self, 'Fasta Information', str(e))
        else:
            QMessageBox.about(self, 'Fasta Information', 'Sorry, Only Fasta file can view.')

    def open_texteditor(self, path):
        open_default_texteditor(path)
        
    def delete_this(self, path):
        reply = QMessageBox.question(self, 'Delete file or folder',
                            'Do you want to delete this?',
                             QMessageBox.Yes | QMessageBox.No,
                             QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)

    def create_folder(self, path):
        if os.path.isfile(path):
            path = os.path.dirname(path)

        folder_name, ok = QInputDialog.getText(self, 'Create folder', 'Please input folder name.')
        if ok:
            folder_path = os.path.join(path, folder_name)
            if os.path.exists(folder_path) :
                QMessageBox.about(self, 'Information', 'This folder already exists')
            else:
                os.mkdir(folder_path)

    def view_file(self, path):
        self.window.view_file(path)

    def init_project(self):
        project_path = project_folder_path()
        self.treeView.setRootIndex(self.fileModel.index(project_path))
        self.project_folder_editor.setText(project_path)

    def browse_project(self):
        open_path = self.project_folder_editor.text()
        if not open_path:
            open_path = project_folder_path()

        path = QFileDialog.getExistingDirectory(self, 
                                'Set Project Folder',
                                open_path,
                                QFileDialog.ShowDirsOnly)

        if self.window and path:
            self.project_folder_editor.setText(path)
            self.treeView.setRootIndex(self.fileModel.index(path))

    def set_project(self):
        path = self.project_folder_editor.text()
        if self.window and path:
            preference['project_folder'] = path
            write_config()
            QMessageBox.about(self, 'Information', 'Project folder is ' + path)

    def tree_cilcked(self, Qmodelidx):
        path = self.fileModel.filePath(Qmodelidx)
        if os.path.isfile(path):
            open_default_application(path)


class TableWidget(QWidget):
    def __init__(self, filepath, parent=None):
        super().__init__()
        self.filepath = filepath
        self.parent = parent

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        blastresult_first_layout = QHBoxLayout()

        browser_file_label = QLabel('File')
        blastresult_first_layout.addWidget(browser_file_label)

        self.file_editor = QLineEdit()
        blastresult_first_layout.addWidget(self.file_editor)

        browser_file_button = QPushButton('Browse')
        blastresult_first_layout.addWidget(browser_file_button)

        # browser_file_button.clicked.connect(self.browse_file)

        main_layout.addLayout(blastresult_first_layout)

        layout = QHBoxLayout()
        self.table = TableView()

        layout.addWidget(self.table)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)

        # self.setMinimumSize(1800, 800)
        self.resize(self.parent.geometry.width() * 0.7, self.parent.geometry.height() * 0.6)

        self.setWindowTitle('Sequence window')

        self.init()

    def closeEvent(self, event):
        self.parent.sequence_window = None
    
    def init(self):
        self.file_editor.setText(self.filepath)

        if get_ext(self.filepath) == '.psl':
            data = open_psl_as_table(self.filepath)
        else:
            data = open_blast_result_as_table(self.filepath)
       
        model = TableModel(data)
        self.table.setModel(model)
        self.table.update()


class ScrollLabel(QScrollArea):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
 
        # making widget resizable
        self.setWidgetResizable(True)
 
        # making qwidget object
        content = QWidget(self)
        self.setWidget(content)
 
        # vertical box layout
        lay = QVBoxLayout(content)
 
        # creating label
        self.label = QLabel(content)
        self.label.setOpenExternalLinks(True)
 
        # setting alignment to the text
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
 
        # making label multi-line
        self.label.setWordWrap(True)
 
        # adding label to the layout
        lay.addWidget(self.label)
 
    # the setText method
    def setText(self, text):
        # setting text to the label
        self.label.setText(text)