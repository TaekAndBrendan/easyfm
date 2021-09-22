import os

from PyQt5.QtCore import (
    Qt,
    QMutex,
    QThread,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QTabWidget,
    QFileDialog,
    QLabel,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QTableView,
    QCompleter,
    QMessageBox,
)
import gffutils
import pyfastx

from Bio import SeqIO

from app.tools.biofiles import (
    covnert_fastq_into_fasta,
    reverse_complement,
    reverse_complements,
    reverse,
    reverses,
)
from app.gui.utils import (
    BaseWidgetUtil,
    TableView,
    TableModel,
    CollapsibleBox,
    IconLabel,
    is_valid,
)
from app.tools.utils import (
    project_folder_path,
    replace_ext,
    get_filepath_project,
    is_fasta_file,
    is_fastq_file,
    is_fastx_file,
    get_gff_features,
    get_valid_filename,
    filter_gff_features,
    get_compressed_file_type,    
)


class FastaWidget(QWidget):
    def __init__(self, window=None, parent=None):
        super(FastaWidget, self).__init__(parent)
        self.window = window

        self.fasta_tab = QTabWidget()
        self.fasta_tab.tabBar().setObjectName("fasta_tab_tab")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self.fasta_tab)

        fa_widget = FAFQWidget(window=window)
        self.fasta_tab.addTab(fa_widget, 'Index/Extract')
        self.fasta_tab.setCurrentIndex(0)

        fa_converter_widget = SequenceConvertWidget(window=window)
        self.fasta_tab.addTab(fa_converter_widget, 'Sequence Reverse')
        
        fq2fa_widget = FQ2FAWidget(window=window)
        self.fasta_tab.addTab(fq2fa_widget, 'Convert FastQ to FastA')

        # Gff Widget
        gff_widget = GffWidget(window=window)
        self.fasta_tab.addTab(gff_widget, 'Extract GFF/GTF')

class FAFQWidget(QWidget, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(FAFQWidget, self).__init__(parent)
        self.window = window
        self.fastaq = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        main_layout.addWidget(IconLabel('Light weight only (Recommended to use a small set data).'))

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('FastA/FastQ File'))

        self.browser_fastaq_file_editor = QLineEdit()
        layout.addWidget(self.browser_fastaq_file_editor)

        self.browser_fastaq_file_button = QPushButton('Browse')
        layout.addWidget(self.browser_fastaq_file_button)

        self.browser_fastaq_file_button.clicked.connect(self.browse_fastaq_file)

        main_layout.addLayout(layout)

        layout = QHBoxLayout()        
        layout.addWidget(QLabel('Index Output File'))
        self.index_output_file_editor = QLineEdit()
        layout.addWidget(self.index_output_file_editor)
        
        self.index_output_file_path_button = QPushButton('Change Folder')
        layout.addWidget(self.index_output_file_path_button)
        self.index_output_file_path_button.clicked.connect(self.index_output_file_path)
        main_layout.addLayout(layout)

        more_options = QVBoxLayout()

        more_options.addWidget(IconLabel('Please insert your prefix ID list as a single .txt file without ‘>’ sign that you want to extract and save.'))
        
        layout = QHBoxLayout()        
        layout.addWidget(QLabel("Input User's Index File"))
        self.input_index_file_editor = QLineEdit()
        layout.addWidget(self.input_index_file_editor)
        
        self.input_index_file_open_button = QPushButton('Browse')
        layout.addWidget(self.input_index_file_open_button)
        self.input_index_file_open_button.clicked.connect(self.input_indxes_file_open)


        more_options.addLayout(layout)

        more_options_box = CollapsibleBox("Save Indexes with User's File")
        more_options_box.setContentLayout(more_options)
        main_layout.addWidget(more_options_box)

        more_options = QVBoxLayout()

        more_options.addWidget(IconLabel('Please make sure your original prefix ID is concise without any spaces or special characters. And then, type the unique ID(s) that you want to extract and save.'))

        layout = QHBoxLayout()
        
        layout.addWidget(QLabel('Prefix ID'))
        self.save_prefix_index_editor = QLineEdit()
        # self.save_prefix_index_editor.setPlaceholderText("e.g. Insert your prefix, 'abc.1' when you want to save 'abc.1.1', 'abc.1.2'.")

        layout.addWidget(self.save_prefix_index_editor)
        
        # self.save_prefix_index_button = QPushButton('Save indexes')
        # layout.addWidget(self.save_prefix_index_button)
        # self.save_prefix_index_button.clicked.connect(self.save_prefix_index)

        more_options.addLayout(layout)

        more_options_box = CollapsibleBox("Save Indexes with Prefix")
        more_options_box.setContentLayout(more_options)
        main_layout.addWidget(more_options_box)

        layout = QHBoxLayout()
        layout.addStretch()

        self.save_filtered_indexes_button = QPushButton('Save Indexes')
        layout.addWidget(self.save_filtered_indexes_button)
        self.save_filtered_indexes_button.clicked.connect(self.save_filtered_indexes)
        main_layout.addLayout(layout)

        main_layout.addWidget(IconLabel('Please double click an item to extract and save.'))

        # tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.tabBar().setObjectName('fasta_tab')

        self.index_list = QListWidget()
        # self.index_list.itemClicked.connect(self.click_index)
        self.index_list.itemDoubleClicked.connect(self.save_item_index)
        self.tab_widget.addTab(self.index_list, 'Index')
        

        main_layout.addWidget(self.tab_widget)

    def browse_fastaq_file(self):
        infilepath, _ = QFileDialog.getOpenFileName(
                            self,
                            'Open Fasta or FastQ File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='Fasta Files(*.fa *.fas *.fna *.fasta *.fastq *.fq *.gz);;All Files(*.*)')

        if self.window and infilepath:
            
            self.browser_fastaq_file_editor.setText(infilepath)
            outfile_path = replace_ext(infilepath, 'fa', 'sub')
            self.index_output_file_editor.setText(outfile_path)

            try:
                self.load_fastaq()
                self.run_index()
            except Exception as e:
                QMessageBox.about(self, 'Information', str(e))


    def load_fastaq(self):
        infilepath = self.browser_fastaq_file_editor.text()
        print(infilepath)
        if is_fasta_file(infilepath) or get_compressed_file_type(infilepath) == 'fa':
            self.fastaq = pyfastx.Fasta(infilepath)
        elif is_fastq_file(infilepath) or get_compressed_file_type(infilepath) == 'fq':
            self.fastaq = pyfastx.Fastq(infilepath)

    def is_valid_inputs(self):
        infilepath = self.browser_fastaq_file_editor.text()

        if not is_valid(self, infilepath, 'Please check a fasta or fastq file.'):
            return False

        if is_fasta_file(infilepath):
            return True 
        if get_compressed_file_type(infilepath) == 'fa':
            return True 
        if is_fastq_file(infilepath):
            return True 
        if get_compressed_file_type(infilepath) == 'fq':
            return True 

        QMessageBox.about(self, 'Information', 'Please check a fasta or fastq file.')
        return False

    def input_indxes_file_open(self):
        infilepath, _ = QFileDialog.getOpenFileName(
                            self,
                            "Open User's Index File",
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            # filter='Fasta Files(*.fa *.fas *.fna *.fasta *.fastq *.fq *.txt);;All Files(*.*)')
                            filter='All Files(*.*)')

        if self.window and is_valid(self, infilepath, "Please check user's index file"):
            self.input_index_file_editor.setText(infilepath)


    def index_output_file_path(self):
        infilepath = self.browser_fastaq_file_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select a Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfile_path:
            self.index_output_file_editor.setText(outfile_path)
     
    def run_index(self):
        if not self.is_valid_inputs():
            return

        if not self.fastaq:
            raise Exception("Sorry, Please check a fasta or fastq file.") 

        self.fa_load_worker = FALoadWorker(self.fastaq, self.index_list)
        self.fa_load_worker.started.connect(self.fa_load_worker_started_callback)
        self.fa_load_worker.finished.connect(self.fa_load_worker_finished_callback)
        self.fa_load_worker.start()

    def fa_load_worker_started_callback(self):
        self.browser_fastaq_file_button.setText('Loading...')
        self.browser_fastaq_file_button.setEnabled(False)

    def fa_load_worker_finished_callback(self):
        self.browser_fastaq_file_button.setText('Browse')
        self.browser_fastaq_file_button.setEnabled(True)

    def save_item_index(self, item):
        reply = QMessageBox.question(self, 'Saved Fasta',
                                    'Do you want to save fasta?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        item_data = item.text()

        filename = get_valid_filename('{}.fa'. format(item_data))

        new_filename, _ = QFileDialog.getSaveFileName(self, 
                                'Do you want to save sequence?',
                                os.path.join(project_folder_path(), filename),
                                '.fa;;All files (*.*)')

        if self.window and new_filename:
            with open(new_filename, 'w') as f:
                f.write('>{}\n'.format(item_data))
                f.write(self.fastaq[item_data].seq)

    def save_filtered_indexes(self):
        if not self.is_valid_inputs():
            return
        
        outfile_path = self.index_output_file_editor.text()

        prefix_index = self.save_prefix_index_editor.text()

        infilepath = self.input_index_file_editor.text()

        if not prefix_index and not infilepath:
            QMessageBox.about(self, 'Information', "Please choose one of the options, User's index file or Prefix")
            return

        if prefix_index and infilepath:
            QMessageBox.about(self, 'Information', "Please choose one of the options, User's index file or Prefix")
            return

        _prefix_indexes = None
        if prefix_index:
            _prefix_indexes = list(map(lambda x: x.strip(), prefix_index.split(',')))

        if infilepath and not is_valid(self, infilepath, "Please check user's index file"):
            return False

        user_indexes = None

        if not _prefix_indexes:
            with open(infilepath, 'r') as f:
                user_indexes = [line.replace('>', '').strip() for line in f]

        # self._save_indexes(outfile_path, user_indexes, _prefix_indexes)
        try:
            self._save_indexes(outfile_path, user_indexes, _prefix_indexes)
        except Exception as e:
            QMessageBox.about(self, 'Information', str(e))


    def _save_indexes(self, outfile_path, user_indexes, prefix_indexes):
        self.fasta_save_worker = FASaveWorker(self.fastaq, outfile_path, user_indexes, prefix_indexes)
        self.fasta_save_worker.started.connect(self.fasta_save_worker_started_callback)
        self.fasta_save_worker.finished.connect(self.fasta_save_worker_finished_callback)
        self.fasta_save_worker.start()

    def fasta_save_worker_started_callback(self):
        self.save_filtered_indexes_button.setText('Processing...')
        self.save_filtered_indexes_button.setEnabled(False)

    def fasta_save_worker_finished_callback(self):
        QMessageBox.about(self, 'Saved Fasta', 'Saved {} Sequences in {}'.format(self.fasta_save_worker.saved_count, self.fasta_save_worker.outfile_path))
        self.save_filtered_indexes_button.setText('Save Indexes')
        self.save_filtered_indexes_button.setEnabled(True)

class FALoadWorker(QThread):
    def __init__(self, fastaq, index_list, parent=None):
        super(FALoadWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()

        self.fastaq = fastaq
        self.index_list = index_list

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        self.index_list.clear()

        for rec in self.fastaq:
            item_to_add = QListWidgetItem()
            item_to_add.setText(rec.name)
            item_to_add.setData(Qt.UserRole, (rec.name,))
            self.index_list.addItem(item_to_add)

        self.index_list.setAlternatingRowColors(True)

class FASaveWorker(QThread):
    # data = pyqtSignal(dict)
    def __init__(self, fastaq, outfile_path, user_indexes=None, prefix_indexes=None, parent=None):
        super(FASaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.fastaq = fastaq
        self.outfile_path = outfile_path
        self.user_indexes = user_indexes
        self.prefix_indexes = prefix_indexes
        self.saved_count = 0

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        if self.user_indexes:
            fastq_indexes = [rec.name for rec in self.fastaq]

            with open(self.outfile_path, 'w') as f:
                for index in self.user_indexes:
                    if index in fastq_indexes:
                        f.write('>{}\n{}\n'.format(index, self.fastaq[index].seq))
                        self.saved_count = self.saved_count + 1

            return
        # print(list(self.prefix_indexes))
        if self.prefix_indexes:
            with open(self.outfile_path, 'w') as f:
                for rec in self.fastaq:
                    for prefix_index in self.prefix_indexes:
                        # if rec.name.startswith(self.prefix_indexes):
                        print('-{}-'.format(prefix_index.strip()))
                        print('={}='.format(rec.name.strip()))
                        if rec.name.strip() == prefix_index.strip():
                            f.write('>{}\n{}\n'.format(rec.name, self.fastaq[rec.name].seq))
                            self.saved_count = self.saved_count + 1
                            break
            return

class SequenceConvertWidget(QWidget, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(SequenceConvertWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        layout = QHBoxLayout()        
        layout.addWidget(QLabel('Fasta File'))
        
        self.file_editor = QLineEdit()
        layout.addWidget(self.file_editor)

        browser_file_button = QPushButton('Browse')
        browser_file_button.clicked.connect(self.browse_infile)
        layout.addWidget(browser_file_button)
        main_layout.addLayout(layout)
    
        layout = QHBoxLayout()        
        layout.addWidget(QLabel('Output File'))
        self.outfile_editor = QLineEdit()
        layout.addWidget(self.outfile_editor)
        
        self.out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.out_path_button)
        self.out_path_button.clicked.connect(self.out_path)

        main_layout.addLayout(layout)
        
        more_options = QVBoxLayout()
        
        layout = QHBoxLayout()        
        layout.addWidget(QLabel('Input Folder'))
        self.input_folder_editor = QLineEdit()
        layout.addWidget(self.input_folder_editor)
        
        self.input_folder_open_button = QPushButton('Set Folder')
        layout.addWidget(self.input_folder_open_button)
        self.input_folder_open_button.clicked.connect(self.input_folder_open)

        more_options.addLayout(layout)

        layout = QHBoxLayout()        
        layout.addWidget(QLabel('Output Folder'))
        self.out_folder_editor = QLineEdit()
        layout.addWidget(self.out_folder_editor)
        
        self.out_folder_open_button = QPushButton('Set Folder')
        layout.addWidget(self.out_folder_open_button)
        self.out_folder_open_button.clicked.connect(self.out_folder_open)

        more_options.addLayout(layout)

        more_options_box = CollapsibleBox('Select a Folder to reverse')
        more_options_box.setContentLayout(more_options)
        main_layout.addWidget(more_options_box)

        layout = QHBoxLayout()
        layout.addStretch()
        self.reverse_complement_button = QPushButton('Reverse Complement')
        self.reverse_complement_button.clicked.connect(self.run_reverse_complement)
        layout.addWidget(self.reverse_complement_button)

        self.Reverse_button = QPushButton('Reverse')
        layout.addWidget(self.Reverse_button)
        self.Reverse_button.clicked.connect(self.run_reverse)
        main_layout.addLayout(layout)


    def browse_infile(self):
        infilename, _ = QFileDialog.getOpenFileName(
                                    self,
                                    'Open File',
                                    project_folder_path(),
                                    options=QFileDialog.DontUseNativeDialog,
                                    filter='Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)')

        if self.window and infilename:
            self.file_editor.setText(infilename)

            outfilename_path = replace_ext(infilename, 'fa', 'out')
            self.outfile_editor.setText(outfilename_path)

    def out_path(self):
        infilepath = self.outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select a Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfile_path:
            self.outfile_editor.setText(outfile_path)

    def is_valid_inputs(self):
        infilepath = self.file_editor.text()
        outfilepath = self.outfile_editor.text()
        if is_valid(self, infilepath, 'Please check a fasta file') and is_valid(self, outfilepath, 'Please check a out file'):
            return True

        input_folder_path = self.input_folder_editor.text()
        out_folder_path = self.out_folder_editor.text()
        if is_valid(self, input_folder_path, 'Please check a input folder') and is_valid(self, out_folder_path, 'Please check a out folder'):
            return True

        return False

    def input_folder_open(self):
        input_folder = QFileDialog.getExistingDirectory(self,
                                    'Select a Folder to save',
                                    project_folder_path(),
                                    QFileDialog.ShowDirsOnly)

        if self.window and input_folder:
            self.input_folder_editor.setText(input_folder)
            

    def out_folder_open(self):
        out_folder = QFileDialog.getExistingDirectory(self,
                                    'Select a Folder to save',
                                    project_folder_path(),
                                    QFileDialog.ShowDirsOnly)

        if self.window and out_folder:
            self.out_folder_editor.setText(out_folder)

    def run_reverse_complement(self):
        if not self.is_valid_inputs():
           return

        try:
            self._run_reverse_complement()
        except Exception as e:
            QMessageBox.about(self, 'Information', str(e))

    def _run_reverse_complement(self):
        infilepath = self.file_editor.text()
        outfilepath = self.outfile_editor.text()

        input_folder_path = self.input_folder_editor.text()
        out_folder_path = self.out_folder_editor.text()

        self.reverse_complement_save_worker = ReverseComplementSaveWorker(infilepath, outfilepath, input_folder_path, out_folder_path)
        self.reverse_complement_save_worker.started.connect(self.reverse_complement_save_worker_started_callback)
        self.reverse_complement_save_worker.finished.connect(self.reverse_complement_save_worker_finished_callback)
        self.reverse_complement_save_worker.start()

    def reverse_complement_save_worker_started_callback(self):
        self.reverse_complement_button.setText('Processing')
        self.reverse_complement_button.setEnabled(False)
        self.Reverse_button.setText('Processing')
        self.Reverse_button.setEnabled(False)


    def reverse_complement_save_worker_finished_callback(self):
        infilepath = self.file_editor.text()
        outfilepath = self.outfile_editor.text()

        input_folder_path = self.input_folder_editor.text()
        out_folder_path = self.out_folder_editor.text()

        # folder
        if input_folder_path and out_folder_path: 
            QMessageBox.about(self, 'Saved Files', 'Reverse complement fasta are saved in {}'.format(out_folder_path))
        else:
            QMessageBox.about(self, 'Saved Files', 'Reverse complement fasta are saved in {}'.format(outfilepath))

        self.reverse_complement_button.setText('Reverse Complement')
        self.reverse_complement_button.setEnabled(True)
        self.Reverse_button.setText('Reverse')
        self.Reverse_button.setEnabled(True)


    def run_reverse(self):
        if not self.is_valid_inputs():
            return

        # self._run_reverse()
        try:
            self._run_reverse()
        except Exception as e:
            QMessageBox.about(self, 'Information', str(e))

    def _run_reverse(self):
        infilepath = self.file_editor.text()
        outfilepath = self.outfile_editor.text()

        input_folder_path = self.input_folder_editor.text()
        out_folder_path = self.out_folder_editor.text()

        self.reverse_save_worker = ReverseSaveWorker(infilepath, outfilepath, input_folder_path, out_folder_path)
        self.reverse_save_worker.started.connect(self.reverse_save_worker_started_callback)
        self.reverse_save_worker.finished.connect(self.reverse_save_worker_finished_callback)
        self.reverse_save_worker.start()

    def reverse_save_worker_started_callback(self):
        self.reverse_complement_button.setText('Processing')
        self.reverse_complement_button.setEnabled(False)
        self.Reverse_button.setText('Processing')
        self.Reverse_button.setEnabled(False)


    def reverse_save_worker_finished_callback(self):
        infilepath = self.file_editor.text()
        outfilepath = self.outfile_editor.text()

        input_folder_path = self.input_folder_editor.text()
        out_folder_path = self.out_folder_editor.text()

        # folder
        if input_folder_path and out_folder_path: 
            QMessageBox.about(self, 'Saved Files', 'Reverse fasta are saved in {}'.format(out_folder_path))
        else:
            QMessageBox.about(self, 'Saved File', 'Reverse fasta are saved in {}'.format(outfilepath))

        self.reverse_complement_button.setText('Reverse Complement')
        self.reverse_complement_button.setEnabled(True)
        self.Reverse_button.setText('Reverse')
        self.Reverse_button.setEnabled(True)


class ReverseSaveWorker(QThread):
    # data = pyqtSignal(dict)
    def __init__(self, infilepath, outfilepath, input_folder_path, out_folder_path, parent=None):
        super(ReverseSaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.infilepath = infilepath
        self.outfilepath = outfilepath
        self.input_folder_path = input_folder_path
        self.out_folder_path = out_folder_path

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        # folder
        if self.input_folder_path and self.out_folder_path: 
            reverses(self.input_folder_path, self.out_folder_path)
        else:
            reverse(self.infilepath, self.outfilepath)

class ReverseComplementSaveWorker(QThread):
    # data = pyqtSignal(dict)
    def __init__(self, infilepath, outfilepath, input_folder_path, out_folder_path, parent=None):
        super(ReverseComplementSaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.infilepath = infilepath
        self.outfilepath = outfilepath
        self.input_folder_path = input_folder_path
        self.out_folder_path = out_folder_path

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        # folder
        if self.input_folder_path and self.out_folder_path: 
            reverse_complements(self.input_folder_path, self.out_folder_path)
        else:
            reverse_complement(self.infilepath, self.outfilepath)

class FQ2FAWidget(QWidget, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(FQ2FAWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        main_layout.addWidget(IconLabel('Light weight only (Recommended to use a small set data).'))

        layout = QHBoxLayout()

        layout.addWidget(QLabel('Query FastQ File'))

        self.browser_fastq_file_editor = QLineEdit()
        layout.addWidget(self.browser_fastq_file_editor)

        browser_fastq_file_button = QPushButton('Browse')
        browser_fastq_file_button.clicked.connect(self.browse_fastq_file)
        layout.addWidget(browser_fastq_file_button)

        main_layout.addLayout(layout)

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out FastA File'))

        self.outfile_editor = QLineEdit()
        layout.addWidget(self.outfile_editor)

        self.outfile_path_button = QPushButton('Change Folder')
        layout.addWidget(self.outfile_path_button)

        self.outfile_path_button.clicked.connect(self.fasta_outfile_path)

        main_layout.addLayout(layout)

        # buttons
        layout = QHBoxLayout()
        layout.addStretch()

        self.extrace_button = QPushButton('Extract')
        layout.addWidget(self.extrace_button)
        self.extrace_button.clicked.connect(self.run_extract)

        main_layout.addLayout(layout)

    def browse_fastq_file(self):
        filename, _ = QFileDialog.getOpenFileName(
                            self,
                            'Open FastQ File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='fastq Files(*.fastq *.fq *.gz);;All Files(*.*)')

        if self.window and filename:
            self.browser_fastq_file_editor.setText(filename)

            outfilename = replace_ext(filename, 'fa')
            self.outfile_editor.setText(outfilename)

    def fasta_outfile_path(self):
        infilepath = self.outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select a Folder',
                                            filepath_project,
                                            '.fa;;.*')

        if self.window and outfile_path:
            self.outfile_editor.setText(outfile_path)

    def is_valid_inputs(self):
        infilepath = self.browser_fastq_file_editor.text()

        if not is_valid(self, infilepath, 'Please check a input file.'):
            return False

        if not is_fastq_file(infilepath) and not get_compressed_file_type(infilepath) == 'fq':
            QMessageBox.about(self, 'Information', 'Please check a input file. Only FastaQ file is accepted.')
            return False

        outfilepath = self.outfile_editor.text()
        if not is_valid(self, outfilepath, 'Please check a out file.'):
            return False

        return True

    def run_extract(self):
        if not self.is_valid_inputs():
            return

        # TODO : check QMessageBox to change
        reply = QMessageBox.question(self, 'FastQ',
                                    'Do you want to extract fasta?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            self._run_extract()
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))   

    def _run_extract(self):
        infilepath = self.browser_fastq_file_editor.text()
        outfilename = self.outfile_editor.text()
        
        self.fa2fq_save_worker = FA2FQSaveWorker(infilepath, outfilename)
        self.fa2fq_save_worker.started.connect(self.fa2fq_save_worker_started_callback)
        self.fa2fq_save_worker.finished.connect(self.fa2fq_save_worker_finished_callback)
        self.fa2fq_save_worker.start()

    def fa2fq_save_worker_started_callback(self):
        self.extrace_button.setText('Processing...')
        self.extrace_button.setEnabled(False)

    def fa2fq_save_worker_finished_callback(self):
        outfilename = self.outfile_editor.text()
        QMessageBox.about(self, 'Saved Fasta', 'Converted records in {}'.format(outfilename))
        self.extrace_button.setText('Convert')
        self.extrace_button.setEnabled(True)


class FA2FQSaveWorker(QThread):
    # data = pyqtSignal(dict)
    def __init__(self, infilepath, outfilepath, parent=None):
        super(FA2FQSaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.infilepath = infilepath
        self.outfilepath = outfilepath

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        covnert_fastq_into_fasta(self.infilepath, self.outfilepath)

# load gff featues with thread
gff_features = None
seqs = None
ftypes = None

class GffWidget(QWidget, BaseWidgetUtil):
    def __init__(self, data=None, window=None, parent=None):
        super(GffWidget, self).__init__(parent)
        self.window = window
        # self.gff_features = None
        self.filtered_gff_features = None
        self.columns = ['Sequence Name', 'Source', 'Feature', 'Start', 'End', 'Score', 'Strand', 'Frame', 'Attribute']

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        layout = QHBoxLayout()

        gff_file_label = QLabel('GFF/GTF File')
        layout.addWidget(gff_file_label)

        self.gff_file_editor = QLineEdit()
        layout.addWidget(self.gff_file_editor)

        self.gff_file_button = QPushButton('Browse')
        self.gff_file_button.clicked.connect(self.browse_gff_file)
        layout.addWidget(self.gff_file_button)

        main_layout.addLayout(layout)

        layout = QHBoxLayout()

        fasta_file_label = QLabel('Reference Fasta File')
        layout.addWidget(fasta_file_label)

        self.fasta_file_editor = QLineEdit()
        layout.addWidget(self.fasta_file_editor)

        self.fasta_file_button = QPushButton('Browse')
        self.fasta_file_button.clicked.connect(self.browse_fasta_file)
        layout.addWidget(self.fasta_file_button)

        main_layout.addLayout(layout)

         # option
        groupBox = QGroupBox('Filtering Options')
        layout = QHBoxLayout()
        # layout.addStretch(1)
        
        self.gff_count = QLabel('')
        layout.addWidget(self.gff_count)

        # self.seq_cb = QComboBox()
        # self.seq_cb.addItem('Sequence Name')
        # self.seq_cb.setMinimumWidth(200)
        # layout.addWidget(self.seq_cb)

        self.seq_editor = QLineEdit()
        self.seq_editor.setPlaceholderText('Sequence Name')
        self.seq_editor.setMinimumWidth(150)
        
        layout.addWidget(self.seq_editor)

        self.feature_type_cb = QComboBox()
        self.feature_type_cb.addItem('Feature Type')
        self.feature_type_cb.setMinimumWidth(150)
        layout.addWidget(self.feature_type_cb)

        self.strand_cb = QComboBox()
        self.strand_cb.addItem('Strand')
        self.strand_cb.addItem('+')
        self.strand_cb.addItem('-')
        layout.addWidget(self.strand_cb)

        self.filter_button = QPushButton('Filter')
        self.filter_button.clicked.connect(self.filter_types)
        layout.addWidget(self.filter_button)

        layout.addStretch()

        self.forward_flanking_regions_editor = QLineEdit()
        self.forward_flanking_regions_editor.setPlaceholderText('Forward Flanking Regions')
        layout.addWidget(self.forward_flanking_regions_editor)

        self.reverse_flanking_regions_editor = QLineEdit()
        self.reverse_flanking_regions_editor.setPlaceholderText('Reverse Flanking Regions') 
        layout.addWidget(self.reverse_flanking_regions_editor)

        self.save_filtered_features_button = QPushButton('Save all filtered features')
        layout.addWidget(self.save_filtered_features_button)
        self.save_filtered_features_button.clicked.connect(self.save_filtered_features)

        groupBox.setLayout(layout)
        main_layout.addWidget(groupBox)

        main_layout.addWidget(IconLabel('Please double click an item to save.'))

        layout = QHBoxLayout()

        self.table_view = TableView()
        self.table_view.setSelectionBehavior(QTableView.SelectRows);
        self.table_view.doubleClicked.connect(self.save_feature)
        layout.addWidget(self.table_view)
        main_layout.addLayout(layout)
       
        self.setLayout(main_layout)

    def browse_gff_file(self):
        filename, _ = QFileDialog.getOpenFileName(self,
                            'Open File',
                            # config['data'],
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='gff Files(*.gff3 *.gff *.gtf *.gz);;All Files(*.*)')
                            # filter="All Files(*.*)")

        if self.window and filename:
            self.gff_file_editor.setText(filename)

            filename = self.gff_file_editor.text()

            _infilename = self.extract(filename, btn=self.gff_file_button)
            if not _infilename:
                return

            self.gff_load_worker = GFFLoadWorker(_infilename)
            self.gff_load_worker.started.connect(self.gff_load_worker_started_callback)
            self.gff_load_worker.finished.connect(self.gff_load_worker_finished_callback)
            self.gff_load_worker.start()


    def gff_load_worker_started_callback(self):
        self.gff_file_button.setText('Loading...')
        self.gff_file_button.setEnabled(False)
        self.save_filtered_features_button.setEnabled(False)
        self.filter_button.setEnabled(False)

    def gff_load_worker_finished_callback(self):
        self.gff_file_button.setText('Browse')
        self.gff_file_button.setEnabled(True)
        self.save_filtered_features_button.setEnabled(True)
        self.filter_button.setEnabled(True)

        # self.gff_count.setText('Count:{} '.format(len(self.gff_features)))
        # model = TableModel(self.gff_features, ['Sequence Name', 'Source', 'Feature', 'Start', 'End', 'Score', 'Strand', 'Frame', 'Attribute'])

        self.gff_count.setText('Count:{} '.format(len(gff_features)))
        model = TableModel(gff_features, ['Sequence Name', 'Source', 'Feature', 'Start', 'End', 'Score', 'Strand', 'Frame', 'Attribute'])


        self.table_view.setModel(model)
        self.table_view.resizeColumnsToContents()
        self.table_view.setAlternatingRowColors(True)
        self.table_view.update()

        # self.seq_cb.clear()
        # self.seq_cb.addItem('Sequence Name')
        # for seq in seqs:
        #     self.seq_cb.addItem(seq)

        seq_completer = QCompleter(seqs)
        seq_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.seq_editor.setCompleter(seq_completer)


        self.feature_type_cb.clear()
        self.feature_type_cb.addItem('Feature Type')
        for ftype in ftypes:
            self.feature_type_cb.addItem(ftype)



    def browse_fasta_file(self):
        filename, _ = QFileDialog.getOpenFileName(self,
                            'Open File',
                            # config['data'],
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)')

        if self.window and filename:


            _infilename = self.extract(filename, btn=self.fasta_file_button)
            if not _infilename:
                return

            self.fasta_file_editor.setText(_infilename)

            
    def is_valid_inputs(self):
        if not self.gff_file_editor.text():
            QMessageBox.about(self, 'Information', 'Please choose a gff file.')
            return False

        fasta_file = self.fasta_file_editor.text()
        if not is_valid(self, fasta_file, 'Please choose a reference fasta file.'):
            return False
        
        if not self.forward_flanking_regions_editor.text() == '' and not self.forward_flanking_regions_editor.text().isdigit():
            QMessageBox.about(self, 'Information', 'Please check forward flanking regions.')
            return False
        
        if not self.reverse_flanking_regions_editor.text() == '' and not self.reverse_flanking_regions_editor.text().isdigit():
            QMessageBox.about(self, 'Information', 'Please check reverse flanking regions.')
            return False
        
        return True

    def filter_types(self):
        if not self.gff_file_editor.text():
            QMessageBox.about(self, 'Information', 'Please choose a gff file.')
            return False
        
        # selected_seq = None if self.seq_cb.currentIndex() == 0 else self.seq_cb.currentText()
        selected_seq = None if self.seq_editor.text()=='' else self.seq_editor.text()
        selected_ftype = None if self.feature_type_cb.currentIndex() == 0 else self.feature_type_cb.currentText()
        selected_strand = None if self.strand_cb.currentIndex() == 0 else self.strand_cb.currentText()

        self.filtered_gff_features = filter_gff_features(gff_features, selected_seq, selected_ftype, selected_strand)

        self.gff_count.setText('Count: {} '.format(len(self.filtered_gff_features)))

        model = TableModel(self.filtered_gff_features, self.columns)
        self.table_view.setModel(model)
        self.table_view.scretch_header()
        self.table_view.update()
      
    def save_filtered_features(self):
        if not self.is_valid_inputs():
            return 

        reply = QMessageBox.question(self, 'Saved Features',
                                    'Do you want to save features?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        ftype = self.feature_type_cb.currentText()

        save_folder = QFileDialog.getExistingDirectory(self,
                                    'Select a Folder to save',
                                    project_folder_path(),
                                    QFileDialog.ShowDirsOnly)

        if not save_folder:
            return

        # self._save_filtered_features(save_folder)
        try:
            self._save_filtered_features(save_folder)
        except Exception as e:
            self.save_filtered_features_button.setText('Save all filtered features')
            QMessageBox.about(self, 'Error', str(e))


    def save_feature(self, Qmodelidx):
        if not self.fasta_file_editor.text():
            QMessageBox.about(self, 'Information', 'Please choose a fasta file.')
            return False
        
        forward_flanking_regions = 0 if self.forward_flanking_regions_editor.text() == '' else int(self.forward_flanking_regions_editor.text())
        
        reverse_flanking_regions = 0 if self.reverse_flanking_regions_editor.text() == '' else int(self.reverse_flanking_regions_editor.text())

        reply = QMessageBox.question(self, 'Saved Feature',
                                    'Do you want to save this feature?\n(forward flanking regions: {},reverse flanking regions: {})'.format(forward_flanking_regions, reverse_flanking_regions),
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        # self._save_feature(Qmodelidx, forward_flanking_regions, reverse_flanking_regions)
        try:
            self._save_feature(Qmodelidx, forward_flanking_regions, reverse_flanking_regions)
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))

    def _save_feature(self, Qmodelidx, forward_flanking_regions, reverse_flanking_regions):
        row = Qmodelidx.model().get_row(Qmodelidx.row())
        r = '\t'.join(list(map(lambda x: str(x), row)))

        feature = gffutils.feature.feature_from_line(r)
        filename = '{}_{}_{}_{}_{}.fa'. format(feature.seqid, feature.source, feature.featuretype, feature.start, feature.end)
        filename = get_valid_filename(filename)

        # feature.start = 0 if feature.start == 0 else feature.start - forward_flanking_regions
        if feature.start < forward_flanking_regions:
            feature.start = 0
        else:
            feature.start = feature.start - forward_flanking_regions        

        
        # feature.end = 0 if feature.end == 0 else feature.end + reverse_flanking_regions
        feature.end = feature.end + reverse_flanking_regions
        
        new_filename, _ = QFileDialog.getSaveFileName(self, 
                                'Do you want to save sequence?',
                                os.path.join(project_folder_path(), filename),
                                '.fa;;All files (*.*)')

        fastafile = self.fasta_file_editor.text()
        if new_filename:
            ids = '>{} {} {} {} {}\n'. format(feature.seqid, feature.source, feature.featuretype, feature.start, feature.end)
            with open(new_filename, 'w') as f:
                f.write(ids)
                f.write(feature.sequence(fastafile))

            QMessageBox.about(self, 'Saved Features', 'Feature are saved in ' + new_filename)

    def _save_filtered_features(self, save_folder):

        forward_flanking_regions = 0 if self.forward_flanking_regions_editor.text() == '' else int(self.forward_flanking_regions_editor.text())
        
        reverse_flanking_regions = 0 if self.reverse_flanking_regions_editor.text() == '' else int(self.reverse_flanking_regions_editor.text())

        fastafile = self.fasta_file_editor.text()

        data = self.filtered_gff_features if self.filtered_gff_features else gff_features

        self.gff_save_worker = GFFSaveWorker(forward_flanking_regions, reverse_flanking_regions, data, fastafile, save_folder)
        self.gff_save_worker.started.connect(self.worker_started_callback)
        self.gff_save_worker.finished.connect(self.worker_finished_callback)
        self.gff_save_worker.start()

    def worker_started_callback(self):
        self.save_filtered_features_button.setText('Processing...')
        self.save_filtered_features_button.setEnabled(False)

    def worker_finished_callback(self):
        QMessageBox.about(self, 'Saved Features', 'All features are saved')
        self.save_filtered_features_button.setText('Save all filtered features')
        self.save_filtered_features_button.setEnabled(True)


class GFFLoadWorker(QThread):
    def __init__(self, filename, parent=None):
        super(GFFLoadWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()

        self.filename = filename

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        global gff_features
        global seqs
        global ftypes
        gff_features, seqs, ftypes = get_gff_features(self.filename)


class GFFSaveWorker(QThread):
    def __init__(self, forward_flanking_regions, reverse_flanking_regions, data, fastafile, save_folder, parent=None):
        super(GFFSaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.forward_flanking_regions = forward_flanking_regions
        self.reverse_flanking_regions = reverse_flanking_regions
        self.data = data
        self.fastafile = fastafile
        self.save_folder = save_folder

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        for item in self.data:
            r = '\t'.join(list(map(lambda x: str(x), item)))

            feature = gffutils.feature.feature_from_line(r)
            filename = '{}_{}_{}_{}_{}.fa'. format(feature.seqid, feature.source, feature.featuretype, feature.start, feature.end)
            filename = get_valid_filename(filename)
            ids = '>{} {} {} {} {}\n'. format(feature.seqid, feature.source, feature.featuretype, feature.start, feature.end)

            if feature.start < self.forward_flanking_regions:
                feature.start = 0
            else:
                feature.start = feature.start - self.forward_flanking_regions        

            # feature.end = 0 if feature.end == 0 else feature.end + self.reverse_flanking_regions
            feature.end = feature.end + self.reverse_flanking_regions

            path = os.path.join(self.save_folder, filename)

            with open(path, 'w') as f:
                f.write(ids)
                f.write(feature.sequence(self.fastafile))

