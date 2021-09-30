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
    QPushButton,
    QTabWidget,
    QFileDialog,
    QLabel,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QGroupBox,
    QCheckBox,
)

from app.tools.biofiles import parse_xml
from app.gui.utils import (
    QProcessWidgetUtil,
    BaseWidgetUtil,
    CollapsibleBox,
    IconLabel,
    is_valid,
)
from app.tools.utils import (
    project_folder_path,
    replace_ext,
    cpu_count,
    get_cmd,
    get_filepath_project,
    comamnds_to_list,
)


# Stand-alone BLAST formatter client, version 2.11.0+
class BlastWidget(QWidget):
    def __init__(self, window=None, parent=None):
        super(BlastWidget, self).__init__(parent)
        self.window = window

        blast_tab = QTabWidget()
        blast_tab.tabBar().setObjectName('blast_tab_tab')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(blast_tab)

        # make db widget
        blastdb_widget = BlastDBWidget(window=window)
        blast_tab.addTab(blastdb_widget, 'Database')
        blast_tab.setCurrentIndex(0)

        # run widget
        blastrun_widget = BlastRunWidget(window=window)
        blast_tab.addTab(blastrun_widget, 'Blast Run')

        # convert widget
        blast_convert_widget = BlastConvertWidget(window=window)
        blast_tab.addTab(blast_convert_widget, 'Result Convert')
        
        # pasrse widget
        blast_paser_widget = BlastPaserWidget(window=window)
        blast_tab.addTab(blast_paser_widget, 'XML Parsing')


class BlastDBWidget(QWidget, QProcessWidgetUtil, BaseWidgetUtil):
    """makedb widget"""
    def __init__(self, window=None, parent=None):
        super(BlastDBWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        # main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        # input file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Input File'))

        self.blastdb_infile_editor = QLineEdit()
        self.blastdb_infile_editor.setToolTip('<a href="http://google.com">Help<a/>')
        layout.addWidget(self.blastdb_infile_editor)

        self.blastdb_type_cb = QComboBox()
        self.blastdb_type_cb.addItem('Database Type')
        self.blastdb_type_cb.addItem('Nucleotide')
        self.blastdb_type_cb.addItem('Protein')
        self.blastdb_type_cb.setCurrentIndex(0)
        layout.addWidget(self.blastdb_type_cb)

        browser_file_button = QPushButton('Browse')
        browser_file_button.setToolTip('Help')
        layout.addWidget(browser_file_button)
        browser_file_button.clicked.connect(self.browse_infile)

        main_layout.addLayout(layout)

        option_layout = QVBoxLayout()
        # Out path
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out Folder'))

        self.blastdb_out_folder_editor = QLineEdit()
        layout.addWidget(self.blastdb_out_folder_editor)

        browser_outpath_button = QPushButton('Browse')
        layout.addWidget(browser_outpath_button)
        browser_outpath_button.clicked.connect(self.browse_outpath)

        option_layout.addLayout(layout)

        # Database name
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Database Name'))

        self.blastdb_name_editor = QLineEdit()
        layout.addWidget(self.blastdb_name_editor)
        
        option_layout.addLayout(layout)

        more_options_box = CollapsibleBox('More Options Manually')
        more_options_box.setContentLayout(option_layout)
        main_layout.addWidget(more_options_box)

        # Create DB, qprocess
        layout = QHBoxLayout()
        layout.addStretch(1)
        self.qprocess_button = QPushButton('Create')
        layout.addWidget(self.qprocess_button)
        self.qprocess_button.clicked.connect(self.create_blastdb)

        main_layout.addLayout(layout)

    def browse_infile(self):
        """pick up a db file"""
        infilename, _ = QFileDialog.getOpenFileName(
                                    self,
                                    'Open File',
                                    project_folder_path(),
                                    options=QFileDialog.DontUseNativeDialog,
                                    filter='Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)')

        if self.window and infilename:
            self.blastdb_infile_editor.setText(infilename)

    def browse_outpath(self):
        blastdb_out_folder = QFileDialog.getExistingDirectory(self, 
                                                    'Select Folder',
                                                    project_folder_path(),
                                                    QFileDialog.ShowDirsOnly)
        if self.window and blastdb_out_folder:
            self.blastdb_out_folder_editor.setText(blastdb_out_folder)

    def create_blastdb(self):
        if not self.is_valid_inputs():
            return

        reply = QMessageBox.question(self, 'Building a database',
                                    'Do you want to create a database?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            self._create_blastdb()
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))

    def is_valid_inputs(self):
        blastdb_infile = self.blastdb_infile_editor.text()

        if not is_valid(self, blastdb_infile, 'Please check a database file.'):
            return False

        if self.blastdb_type_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a database type.')
            return False

        return True

    def _create_blastdb(self):
        cmd = get_cmd('makeblastdb')

        options = []
        options.append('-in')
        infilename = self.blastdb_infile_editor.text()

        _infilename = self.extract(infilename, btn=self.qprocess_button)
        if not _infilename:
            return

        options.append(_infilename)

        options.append('-dbtype')
        dbtype = 'nucl' if self.blastdb_type_cb.currentIndex() == 1 else 'prot'
        options.append(dbtype)

        db_filename = self.blastdb_name_editor.text()

        if db_filename:
            db_outpath = self.blastdb_out_folder_editor.text()
            db_outfile = os.path.join(db_outpath, db_filename) if db_outpath else db_filename
            options.append('-out')
            options.append(db_outfile)

        try:
            self.qprocess_start(cmd, options, 'Database is created.')
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))
            
    def reset(self):
        pass


class BlastRunWidget(QWidget, QProcessWidgetUtil, BaseWidgetUtil):
    def __init__(self, window=None, parent=None, **kwargs):
        super(BlastRunWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        # main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.setLayout(main_layout)

        # Database name
        blast_db_widget = QWidget()

        layout = QHBoxLayout()

        layout.addWidget(QLabel('Database Name'))

        self.blastrun_db_editor = QLineEdit()
        self.blastrun_db_editor.setPlaceholderText('Please select a fasta file with which you have created database.')        
        
        layout.addWidget(self.blastrun_db_editor)

        blastrun_db_button = QPushButton('Browse')
        layout.addWidget(blastrun_db_button)

        blastrun_db_button.clicked.connect(self.get_dbfile)

        main_layout.addLayout(layout)

        # Input file
        layout = QHBoxLayout()

        layout.addWidget(QLabel('Input Query File'))

        self.blastrun_infile_editor = QLineEdit()
        layout.addWidget(self.blastrun_infile_editor)

        blastrun_file_button = QPushButton('Browse')
        layout.addWidget(blastrun_file_button)

        blastrun_file_button.clicked.connect(self.get_infile)

        main_layout.addLayout(layout)

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out File'))

        self.blastrun_outfile_editor = QLineEdit()
        layout.addWidget(self.blastrun_outfile_editor)

        self.blastrun_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.blastrun_out_path_button)

        self.blastrun_out_path_button.clicked.connect(self.blastrun_out_path)

        main_layout.addLayout(layout)

        # Tools
        layout = QHBoxLayout()

        self.blastrun_tool_cb = QComboBox()
        self.blastrun_tool_cb.addItem('Tools')
        self.blastrun_tool_cb.addItem('blastn')
        self.blastrun_tool_cb.addItem('blastp')
        self.blastrun_tool_cb.addItem('blastx')
        self.blastrun_tool_cb.addItem('tblastx')
        self.blastrun_tool_cb.addItem('tblastn')
        layout.addWidget(self.blastrun_tool_cb)

        self.blastrun_evalue_cb = QComboBox()
        self.blastrun_evalue_cb.addItem('E-value')
        self.blastrun_evalue_cb.addItem('1e-1')
        self.blastrun_evalue_cb.addItem('1e-2')
        self.blastrun_evalue_cb.addItem('1e-3')
        self.blastrun_evalue_cb.addItem('1e-4')
        self.blastrun_evalue_cb.addItem('1e-5')
        self.blastrun_evalue_cb.addItem('1e-6')
        self.blastrun_evalue_cb.addItem('1e-7')
        self.blastrun_evalue_cb.addItem('1e-8')
        self.blastrun_evalue_cb.addItem('1e-9')
        self.blastrun_evalue_cb.addItem('1e-10')
        self.blastrun_evalue_cb.addItem('1e-20')
        self.blastrun_evalue_cb.addItem('1e-50')
        self.blastrun_evalue_cb.addItem('1e-100')
        self.blastrun_evalue_cb.addItem('1e-200')
        self.blastrun_evalue_cb.addItem('1e-300')
        self.blastrun_evalue_cb.addItem('1e-500')
        self.blastrun_evalue_cb.addItem('1e-700')
        self.blastrun_evalue_cb.setCurrentIndex(0)
        layout.addWidget(self.blastrun_evalue_cb)

        self.blastrun_out_type_cb = QComboBox()
        self.blastrun_out_type_cb.addItem('Output Type')
        self.blastrun_out_type_cb.addItem('0. Pairwise')
        self.blastrun_out_type_cb.addItem('1. Query-anchored showing identities')
        self.blastrun_out_type_cb.addItem('2. Query-anchored no identities')
        self.blastrun_out_type_cb.addItem('3. Flat query-anchored, show identities')
        self.blastrun_out_type_cb.addItem('4. Flat query-anchored, no identities')
        self.blastrun_out_type_cb.addItem('5. XML Blast output')
        self.blastrun_out_type_cb.addItem('6. Tabular')
        self.blastrun_out_type_cb.addItem('7. Tabular with comment lines')
        self.blastrun_out_type_cb.addItem('8. Text ASN.1')
        self.blastrun_out_type_cb.addItem('9. Binary ASN.1')
        self.blastrun_out_type_cb.addItem('10 Comma-separated values')
        self.blastrun_out_type_cb.addItem('11 BLAST archive format (ASN.1)')
        self.blastrun_out_type_cb.setCurrentIndex(0)

        self.blastrun_out_type_cb.currentIndexChanged.connect(self.blastrun_out_type_changed)

        layout.addWidget(self.blastrun_out_type_cb)

        self.blastrun_cpu_cb = QComboBox()
        self.blastrun_cpu_cb.addItem('CPU to run (defualt: 1)')
        for i in range(1, cpu_count()+1):
            self.blastrun_cpu_cb.addItem('%i' % i)
        self.blastrun_cpu_cb.setCurrentIndex(0)
        layout.addWidget(self.blastrun_cpu_cb)

        main_layout.addLayout(layout)

        ## option
        option_layout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Raw Options'))

        self.blastdb_option_editor = QLineEdit()
        layout.addWidget(self.blastdb_option_editor)

        option_layout.addLayout(layout)

        more_options_box = CollapsibleBox('More Options Manually')
        more_options_box.setContentLayout(option_layout)
        main_layout.addWidget(more_options_box)

        # Run
        blastdb_fourth_layout = QHBoxLayout()
        blastdb_fourth_layout.addStretch()
        self.qprocess_button = QPushButton('Run')
        blastdb_fourth_layout.addWidget(self.qprocess_button)

        self.qprocess_button.clicked.connect(self.run_blast)

        main_layout.addLayout(blastdb_fourth_layout)

    def blastrun_out_type_changed(self):
        outfile = self.blastrun_outfile_editor.text()
        if outfile:
            out_type = self.blastrun_out_type_cb.currentIndex() - 1
            if out_type == 5:
                outfile = replace_ext(outfile, 'xml', out_type)
            elif out_type == 11:
                outfile = replace_ext(outfile, 'asn', out_type)
            else:
                outfile = replace_ext(outfile, 'txt', out_type)

            self.blastrun_outfile_editor.setText(outfile)

    def get_dbfile(self):
        """pick up db file"""
        db_filename, _ = QFileDialog.getOpenFileName(
                                self,
                                'Open File',
                                project_folder_path(),
                                options=QFileDialog.DontUseNativeDialog,
                                filter="Fasta Files(*.fa *.fas *.fna *.fasta);;All Files(*.*)")
                                # filter='All Files(*.*)')

        # self.dbpath = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if self.window and db_filename:
            self.blastrun_db_editor.setText(db_filename)

    def get_infile(self):
        infilepath, _ = QFileDialog.getOpenFileName(
                            self,
                            'Open File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)')
        if self.window and infilepath:
            self.blastrun_infile_editor.setText(infilepath)
            
            outfilename_path = replace_ext(infilepath, 'txt')
            self.blastrun_outfile_editor.setText(outfilename_path)
            self.blastrun_out_type_changed()

    def blastrun_out_path(self):
        infilepath = self.blastrun_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfile_path:
            self.blastrun_outfile_editor.setText(outfile_path)

    def is_valid_inputs(self):
        blastrun_db = self.blastrun_db_editor.text()
        if not is_valid(self, blastrun_db, 'Please check a database file.'):
            return False

        blastrun_infile = self.blastrun_infile_editor.text()
        if not is_valid(self, blastrun_infile, 'Please check a input query file.'):
            return False

        if self.blastrun_tool_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a tool.')
            return False

        if self.blastrun_evalue_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check an E-value.')
            return False

        if self.blastrun_out_type_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check an output type.')
            return False

        return True

    def run_blast(self):
        if not self.is_valid_inputs():
            return

        reply = QMessageBox.question(
                    self,
                    'Run Blast', 'Do you want to run blast?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes)

        if reply == QMessageBox.No:
            return

        self._run_blast()

    def _run_blast(self):
        tool_sel = self.blastrun_tool_cb.currentText()
        cmd = get_cmd(tool_sel)

        options = []

        dbfile = self.blastrun_db_editor.text()
        options.append('-db')
        options.append(dbfile)

        options.append('-query')
        infilename = self.blastrun_infile_editor.text()

        _infilename = self.extract(infilename, btn=self.qprocess_button)
        if not _infilename:
            return

        options.append(_infilename)

        evalue_sel = self.blastrun_evalue_cb.currentIndex()
        evalue_sel = 4 if evalue_sel == 0 else evalue_sel
        evalue_dict = {
            1: '1e-1',
            2: '1e-2',
            3: '1e-3',
            4: '1e-4',
            5: '1e-5',
            6: '1e-6',
            7: '1e-7',
            8: '1e-8',
            9: '1e-9',
            10: '1e-10',
            11: '1e-20',
            12: '1e-50',
            13: '1e-100',
            14: '1e-200',
            15: '1e-300',
            16: '1e-500',
            17: '1e-700'
        }

        evalue = evalue_dict.get(evalue_sel)

        options.append('-evalue')
        options.append(evalue)

        out_type_sel = self.blastrun_out_type_cb.currentIndex()
        out_type_dict = {
            1: '0',
            2: '1',
            3: '2',
            4: '3',
            5: '4',
            6: '5',
            7: '6',
            8: '7',
            9: '8',
            10: '9',
            11: '10',
            12: '11'
        }

        out_type = out_type_dict.get(out_type_sel)

        options.append('-outfmt')
        options.append(out_type)

        options.append('-out')
        out_filename = self.blastrun_outfile_editor.text()
        options.append(out_filename)

        cpucount = self.blastrun_cpu_cb.currentIndex()

        if cpucount == 0:
            cpucount = 1

        options.append('-num_threads')
        options.append('%i' % cpucount)

        more_options = self.blastdb_option_editor.text()
        if more_options:
            options.extend(comamnds_to_list(more_options))

        try:
            self.qprocess_start(cmd, options, '')
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))


class BlastConvertWidget(QWidget, QProcessWidgetUtil, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(BlastConvertWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        main_layout.addWidget(IconLabel('ASN(BLAST Archive format) is generated with Blast option 11. Please select an ASN format file and an anthor format option you want to convert.'))
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Input File'))

        self.blastconvert_infile_editor = QLineEdit()
        layout.addWidget(self.blastconvert_infile_editor)

        browser_infile_button = QPushButton('Browse')
        layout.addWidget(browser_infile_button)

        browser_infile_button.clicked.connect(self.browse_infile)

        main_layout.addLayout(layout)

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out File'))

        self.blastconvert_outfile_editor = QLineEdit()
        layout.addWidget(self.blastconvert_outfile_editor)
        
        self.blastconvert_out_type_cb = QComboBox()
        self.blastconvert_out_type_cb.addItem('Output Type')
        self.blastconvert_out_type_cb.addItem('0. Pairwise')
        self.blastconvert_out_type_cb.addItem('1. Query-anchored showing identities')
        self.blastconvert_out_type_cb.addItem('2. Query-anchored no identities')
        self.blastconvert_out_type_cb.addItem('3. Flat query-anchored, show identities')
        self.blastconvert_out_type_cb.addItem('4. flat query-anchored, no identities')
        self.blastconvert_out_type_cb.addItem('5. XML Blast output')
        self.blastconvert_out_type_cb.addItem('6. Tabular')
        self.blastconvert_out_type_cb.addItem('7. Tabular with comment lines')
        self.blastconvert_out_type_cb.addItem('8. Text ASN.1')
        self.blastconvert_out_type_cb.addItem('9. Binary ASN.1')
        self.blastconvert_out_type_cb.addItem('10 Comma-separated values')
        self.blastconvert_out_type_cb.addItem('11 BLAST archive format (ASN.1)')

        self.blastconvert_out_type_cb.currentIndexChanged.connect(self.blastrun_out_type_changed)
        layout.addWidget(self.blastconvert_out_type_cb)

        self.blastconvert_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.blastconvert_out_path_button)

        self.blastconvert_out_path_button.clicked.connect(self.blastconvert_out_path)

        # self.blastconvert_out_file_view_button = QPushButton('View')
        # layout.addWidget(self.blastconvert_out_file_view_button)
        # self.blastconvert_out_file_view_button.clicked.connect(self.blastconvert_out_file_view)

        main_layout.addLayout(layout)

        ## option
        option_layout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Raw Options'))

        self.blastconvert_option_editor = QLineEdit()
        self.blastconvert_option_editor.setPlaceholderText('e.g. -outfmt "7 qseqid sseqid pident qlen length mismatch gapopen evalue bitscore" ')
        layout.addWidget(self.blastconvert_option_editor)

        option_layout.addLayout(layout)

        more_options_box = CollapsibleBox('More Options Manually')
        more_options_box.setContentLayout(option_layout)
        main_layout.addWidget(more_options_box)

         # output type
        layout = QHBoxLayout()
        layout.addStretch()
        self.qprocess_button = QPushButton('Convert')
        layout.addWidget(self.qprocess_button)

        self.qprocess_button.clicked.connect(self.run_convert)

        main_layout.addLayout(layout)

    def blastrun_out_type_changed(self):
        outfile = self.blastconvert_outfile_editor.text()
        if outfile:
            out_type = self.blastconvert_out_type_cb.currentIndex() - 1
            if out_type == 5:
                outfile = replace_ext(outfile, 'xml', out_type)
            elif out_type == 11:
                outfile = replace_ext(outfile, 'asn', out_type)
            else:
                outfile = replace_ext(outfile, 'txt', out_type)

            self.blastconvert_outfile_editor.setText(outfile)

    def browse_infile(self):
        infilename, _ = QFileDialog.getOpenFileName(self,
                            'Open File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='ASN Files(*.asn);;All Files(*.*)')

        if self.window and infilename:

            self.blastconvert_infile_editor.setText(infilename)

            out_filename = replace_ext(infilename, 'txt')
            self.blastconvert_outfile_editor.setText(out_filename)

    def blastconvert_out_path(self):
        infilepath = self.blastconvert_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfile_path:
            self.blastconvert_outfile_editor.setText(outfile_path)
            self.blastrun_out_type_changed()

    def run_convert(self):
        if not self.is_valid_inputs():
            return;

        self._run_convert()

    def is_valid_inputs(self):
        blastconvert_infile = self.blastconvert_infile_editor.text()
        if not is_valid(self, blastconvert_infile, 'Please check a input file.'):
            return False

        if not self.blastconvert_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'Please check a out file.')
            return False

        if self.blastconvert_infile_editor.text() == self.blastconvert_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'You have selected the same file.')
            return False

        return True

    def _run_convert(self):
        cmd = get_cmd('blast_formatter')

        # target test file - sequence.fasta
        options = []
        options.append('-archive')
        infilename = self.blastconvert_infile_editor.text()

        _infilename = self.extract(infilename, btn=self.parsing_button)
        if not _infilename:
            return
        options.append(_infilename)

        out_type_sel = self.blastconvert_out_type_cb.currentIndex()
        out_type_dict = {
            1: '0',
            2: '1',
            3: '2',
            4: '3',
            5: '4',
            6: '5',
            7: '6',
            8: '7',
            9: '8',
            10: '9',
            11: '10',
            12: '11'
        }

        out_type = out_type_dict.get(out_type_sel)

        if out_type:
            options.append('-outfmt')
            options.append(out_type)

        more_options = self.blastconvert_option_editor.text()
        if more_options:
            options.extend(comamnds_to_list(more_options))

        options.append('-out')
        outfile = self.blastconvert_outfile_editor.text()
        options.append(outfile)


        # self.qprocess_start(cmd, options)
        try:
            self.qprocess_start(cmd, options)
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))



class BlastPaserWidget(QWidget, QProcessWidgetUtil, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(BlastPaserWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)


        main_layout.addWidget(IconLabel('This tool generates CSV and alignment files.'))

        layout = QHBoxLayout()
        layout.addWidget(QLabel('Input File'))

        self.blastparser_infile_editor = QLineEdit()
        layout.addWidget(self.blastparser_infile_editor)

        browser_infile_button = QPushButton('Browse')
        layout.addWidget(browser_infile_button)

        browser_infile_button.clicked.connect(self.browse_infile)

        main_layout.addLayout(layout)

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out File'))

        self.blastparser_outfile_editor = QLineEdit()
        layout.addWidget(self.blastparser_outfile_editor)

        self.blastparser_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.blastparser_out_path_button)

        self.blastparser_out_path_button.clicked.connect(self.blastparser_out_path)

        main_layout.addLayout(layout)

        # opation1
        groupBox = QGroupBox('Query Information')

        layout = QHBoxLayout()
        
        self.query_id_cb = QCheckBox('Query-ID')
        self.query_id_cb.setChecked(True)
        layout.addWidget(self.query_id_cb)
        self.query_length_cb = QCheckBox('Query-Length')
        self.query_length_cb.setChecked(True)
        layout.addWidget(self.query_length_cb)
        self.query_start_cb = QCheckBox('Query_Start')
        self.query_start_cb.setChecked(True)
        layout.addWidget(self.query_start_cb)
        self.query_end_cb = QCheckBox('Query_End')
        self.query_end_cb.setChecked(True)
        layout.addWidget(self.query_end_cb)

        groupBox.setLayout(layout)
        main_layout.addWidget(groupBox)

        # opation2
        groupBox = QGroupBox('Target Information')

        layout = QHBoxLayout()
        self.target_length_cb = QCheckBox('Target_Length')
        self.target_length_cb.setChecked(True)
        layout.addWidget(self.target_length_cb)
        self.target_start_cb = QCheckBox('Target_Start')
        self.target_start_cb.setChecked(True)
        layout.addWidget(self.target_start_cb)
        self.target_end_cb = QCheckBox('Target_End')
        self.target_end_cb.setChecked(True)
        layout.addWidget(self.target_end_cb)
        
        groupBox.setLayout(layout)
        main_layout.addWidget(groupBox)

        # opation3
        groupBox = QGroupBox('Matches Information')

        layout = QHBoxLayout()
        self.match_length_cb = QCheckBox('Match_Length')
        self.match_length_cb.setChecked(True)
        layout.addWidget(self.match_length_cb)
        self.score_cb = QCheckBox('Score')
        self.score_cb.setChecked(True)
        layout.addWidget(self.score_cb)
        self.matches_strain_cb = QCheckBox('Matches_Strain')
        self.matches_strain_cb.setChecked(True)
        layout.addWidget(self.matches_strain_cb)
        
        groupBox.setLayout(layout)
        main_layout.addWidget(groupBox)

        groupBox = QGroupBox('Cut off Values')
        layout = QHBoxLayout()

        self.rank_cb = QComboBox()
        self.rank_cb.addItem('Rank ≤ 1')
        self.rank_cb.addItem('Rank ≤ 2')
        self.rank_cb.addItem('Rank ≤ 3')
        self.rank_cb.addItem('Rank ≤ 5')
        self.rank_cb.addItem('Rank ≤ 10')
        self.rank_cb.addItem('Rank ≤ 30')
        self.rank_cb.addItem('Rank ≤ 50')
        self.rank_cb.addItem('Rank ≤ 100')
        self.rank_cb.setCurrentIndex(0)
        layout.addWidget(self.rank_cb)

        self.hsp_number_cb = QComboBox()
        self.hsp_number_cb.addItem('HSP number ≤ 1')
        self.hsp_number_cb.addItem('HSP number ≤ 2')
        self.hsp_number_cb.addItem('HSP number ≤ 3')
        self.hsp_number_cb.addItem('HSP number ≤ 5')
        self.hsp_number_cb.addItem('HSP number ≤ 10')
        self.hsp_number_cb.addItem('HSP number ≤ 30')
        self.hsp_number_cb.addItem('HSP number ≤ 50')
        self.hsp_number_cb.addItem('HSP number ≤ 100')
        self.hsp_number_cb.setCurrentIndex(0)
        layout.addWidget(self.hsp_number_cb)
        
        self.e_value_cb = QComboBox()
        # self.e_value_cb.addItem('E value ≤')
        # self.e_value_cb.addItem('1e-1')
        self.e_value_cb.addItem('E value ≤ 1e-1')
        self.e_value_cb.addItem('E value ≤ 1e-2')
        self.e_value_cb.addItem('E value ≤ 1e-3')
        self.e_value_cb.addItem('E value ≤ 1e-5')
        self.e_value_cb.addItem('E value ≤ 1e-10')
        self.e_value_cb.addItem('E value ≤ 1e-30')
        self.e_value_cb.addItem('E value ≤ 1e-50')
        self.e_value_cb.addItem('E value ≤ 1e-100')
        self.e_value_cb.addItem('E value ≤ 1e-200')
        self.e_value_cb.addItem('E value ≤ 1e-300')
        self.e_value_cb.setCurrentIndex(0)
        layout.addWidget(self.e_value_cb)
        
        self.identify_cb = QComboBox()
        self.identify_cb.addItem('Identify(%) ≥ 0')
        self.identify_cb.addItem('Identify(%) ≥ 70')
        self.identify_cb.addItem('Identify(%) ≥ 75')
        self.identify_cb.addItem('Identify(%) ≥ 80')
        self.identify_cb.addItem('Identify(%) ≥ 85')
        self.identify_cb.addItem('Identify(%) ≥ 90')
        self.identify_cb.addItem('Identify(%) ≥ 95')
        self.identify_cb.addItem('Identify(%) ≥ 100')
        self.identify_cb.setCurrentIndex(0)
        layout.addWidget(self.identify_cb)
        
        self.query_converage_cb = QComboBox()
        self.query_converage_cb.addItem('Query Converage(%) ≥ 0')
        # self.query_converage_cb.addItem('0')
        self.query_converage_cb.addItem('Query Converage(%) ≥ 10')
        self.query_converage_cb.addItem('Query Converage(%) ≥ 20')
        self.query_converage_cb.addItem('Query Converage(%) ≥ 30')
        self.query_converage_cb.addItem('Query Converage(%) ≥ 50')
        self.query_converage_cb.addItem('Query Converage(%) ≥ 100')
        self.query_converage_cb.setCurrentIndex(0)
        layout.addWidget(self.query_converage_cb)

        groupBox.setLayout(layout)
        main_layout.addWidget(groupBox)

         # output type
        layout = QHBoxLayout()
        layout.addStretch()
        self.parsing_button = QPushButton('Parsing')
        layout.addWidget(self.parsing_button)

        self.parsing_button.clicked.connect(self.run_paser)

        main_layout.addLayout(layout)


    def browse_infile(self):
        infilename, _ = QFileDialog.getOpenFileName(self,
                            'Open File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter='Blast XML Files(*.xml *.gz);;All Files(*.*)')

        if self.window and infilename:

            self.blastparser_infile_editor.setText(infilename)
            outfile_path = replace_ext(infilename, 'csv')
            self.blastparser_outfile_editor.setText(outfile_path)

    def blastparser_out_path(self):
        infilepath = self.blastparser_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfile_path:
            self.blastparser_outfile_editor.setText(outfile_path)

    def is_valid_inputs(self):
        blastparser_infile = self.blastparser_infile_editor.text()
        if not is_valid(self, blastparser_infile, 'Please check a input file.'):
            return False

        if not self.blastparser_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'Please check a out file.')
            return False

        if self.blastparser_infile_editor.text() == self.blastparser_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'You have selected the same file.')
            return False
        
        return True

    def run_paser(self):
        if not self.is_valid_inputs():
            return;

        # self._run_convert()
        try:
            self._run_convert()
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))

    def _run_convert(self):
        filter_values = {}

        infilename = self.blastparser_infile_editor.text()
        _infilename = self.extract(infilename, btn=self.parsing_button)
        if not _infilename:
            return

        filter_values['infile'] = _infilename
        filter_values['outfile'] = self.blastparser_outfile_editor.text()
        filter_values['alignment_outfile'] = replace_ext(filter_values['outfile'], 'txt', 'ali')

        # filter_values['BD'] = self.blastoutput_def.isChecked()
        # filter_values['BL'] = self.blastoutput_length.isChecked()
        filter_values['QI'] = self.query_id_cb.isChecked()
        filter_values['QL'] = self.query_length_cb.isChecked()
        filter_values['QS'] = self.query_start_cb.isChecked()
        filter_values['QE'] = self.query_end_cb.isChecked()

        filter_values['TL'] = self.target_length_cb.isChecked()
        filter_values['TS'] = self.target_start_cb.isChecked()
        filter_values['TE'] = self.target_end_cb.isChecked()
        
        filter_values['ML'] = self.match_length_cb.isChecked()
        filter_values['S'] = self.score_cb.isChecked()
        filter_values['MS'] = self.matches_strain_cb.isChecked()
        # filter_values['MQS'] = self.matches_query_sequence.isChecked()
        # filter_values['C'] = self.comparison.isChecked()
        # filter_values['MTS'] = self.matches_target_sequence.isChecked()
        
        rank_sel = self.rank_cb.currentIndex()
        rank_dict = {
            0: '1',
            1: '2',
            2: '3',
            3: '5',
            4: '10',
            5: '30',
            6: '50',
            7: '100'
        }
        filter_values['R'] = rank_dict.get(rank_sel)


        hsp_number_sel = self.hsp_number_cb.currentIndex()
        hsp_number_dict = {
            0: '1',
            1: '2',
            2: '3',
            3: '5',
            4: '10',
            5: '30',
            6: '50',
            7: '100'
        }
        filter_values['HN'] = hsp_number_dict.get(hsp_number_sel)

        e_value_sel = self.e_value_cb.currentIndex()
        e_value_dict = {
            0: '1e-1',
            1: '1e-2',
            2: '1e-3',
            3: '1e-5',
            4: '1e-10',
            5: '1e-30',
            6: '1e-50',
            7: '1e-100',
            8: '1e-200',
            9: '1e-300',
        }
        filter_values['E'] = e_value_dict.get(e_value_sel)


        identify_sel = self.identify_cb.currentIndex()
        identify_dict = {
            0: '0',
            1: '70',
            2: '75',
            3: '80',
            4: '85',
            5: '90',
            6: '95',
            7: '100'
        }
        filter_values['I'] = identify_dict.get(identify_sel)

        query_converage_sel = self.query_converage_cb.currentIndex()
        query_converage_dict = {
            0: '0',
            1: '10',
            2: '20',
            3: '30',
            4: '50',
            5: '100'
        }
        filter_values['QC'] = query_converage_dict.get(query_converage_sel)

        self.xml_filter_worker = XMLFilterWorker(filter_values)
        self.xml_filter_worker.started.connect(self.xml_filter_worker_started_callback)
        self.xml_filter_worker.finished.connect(self.xml_filter_worker_finished_callback)
        self.xml_filter_worker.start()

    def xml_filter_worker_started_callback(self):
        self.parsing_button.setText('Processing...')
        self.parsing_button.setEnabled(False)

    def xml_filter_worker_finished_callback(self):
        outfile = self.blastparser_outfile_editor.text()
        alignment_outfile =  replace_ext(outfile, 'txt', 'ali')
        QMessageBox.about(self, 'Finished Pasring', '{}\n and {}\n are saved.'.format(outfile, alignment_outfile))
        self.parsing_button.setText('parsing')
        self.parsing_button.setEnabled(True)


class XMLFilterWorker(QThread):
    def __init__(self, filter_values, parent=None):
        super(XMLFilterWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.filter_values = filter_values

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False

        parse_xml(self.filter_values)