from PyQt5.QtCore import Qt
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
    QTableView,
)

from app.gui.utils import (
    QProcessWidgetUtil,
    BaseWidgetUtil,
    CollapsibleBox,
    IconLabel,
    is_valid,
)
from app.tools.utils import (
    project_folder_path,
    replace_ext, get_cmd,
    get_filepath_project,
    comamnds_to_list,
)


class BlatWidget(QWidget):
    """Blat main widget"""
    def __init__(self, window=None, parent=None):
        super(BlatWidget, self).__init__(parent)
        self.window = window

        blat_tab = QTabWidget()
        blat_tab.tabBar().setObjectName("blat_tab_tab")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(blat_tab)

        blastrun_widget = BlatRunWidget(window=window)
        blat_tab.addTab(blastrun_widget, 'Blat Run')
        blat_tab.setCurrentIndex(0)


class BlatRunWidget(QWidget, QProcessWidgetUtil, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(BlatRunWidget, self).__init__(parent)
        self.window = window
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        self.setLayout(main_layout)

        main_layout.addWidget(IconLabel('Light weight only (Recommended to use a small set data. For big genome in Database Name, please use each chromosome file, respectively).'))
        
        layout = QHBoxLayout()

        layout.addWidget(QLabel('Database Name'))

        self.blatrun_db_editor = QLineEdit()
        layout.addWidget(self.blatrun_db_editor)

        blatrun_db_button = QPushButton('Browse')
        layout.addWidget(blatrun_db_button)

        blatrun_db_button.clicked.connect(self.get_dbfile)

        main_layout.addLayout(layout)

        # Input file
        layout = QHBoxLayout()

        layout.addWidget(QLabel('Input File'))

        self.blatrun_infile_editor = QLineEdit()
        layout.addWidget(self.blatrun_infile_editor)

        blatrun_file_button = QPushButton('Browse')
        layout.addWidget(blatrun_file_button)

        blatrun_file_button.clicked.connect(self.get_infile)

        main_layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(QLabel('Out File'))

        self.blatrun_outfile_editor = QLineEdit()
        layout.addWidget(self.blatrun_outfile_editor)

        self.blatrun_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.blatrun_out_path_button)

        self.blatrun_out_path_button.clicked.connect(self.blatrun_out_path)

        main_layout.addLayout(layout)

        # Tools
        layout = QHBoxLayout()

        self.blatrun_dbtype_cb = QComboBox()
        self.blatrun_dbtype_cb.addItem('Database Type')
        self.blatrun_dbtype_cb.addItem('dna')
        self.blatrun_dbtype_cb.addItem('prot')
        self.blatrun_dbtype_cb.addItem('dnax')
        layout.addWidget(self.blatrun_dbtype_cb)

        self.blatrun_querytype_cb = QComboBox()
        self.blatrun_querytype_cb.addItem('Qeury Type')
        self.blatrun_querytype_cb.addItem('dna')
        self.blatrun_querytype_cb.addItem('rna')
        self.blatrun_querytype_cb.addItem('prot')
        self.blatrun_querytype_cb.addItem('dnax')
        self.blatrun_querytype_cb.addItem('rnax')
        layout.addWidget(self.blatrun_querytype_cb)

        self.blastrun_tilesize_cb = QComboBox()
        self.blastrun_tilesize_cb.addItem('Tile Size')
        for i in range(8, 15):
            self.blastrun_tilesize_cb.addItem(str(i))
        layout.addWidget(self.blastrun_tilesize_cb)

        self.blastrun_stepsize_cb = QComboBox()
        self.blastrun_stepsize_cb.addItem('Step Size')
        for i in range(1, 15):
            self.blastrun_stepsize_cb.addItem(str(i))
        layout.addWidget(self.blastrun_stepsize_cb)

        self.blastrun_oneoff_cb = QComboBox()
        self.blastrun_oneoff_cb.addItem('One Off')
        for i in range(1, 15):
            self.blastrun_oneoff_cb.addItem(str(i))
        layout.addWidget(self.blastrun_oneoff_cb)

        main_layout.addLayout(layout)

        ## option
        option_layout = QVBoxLayout()
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Options'))

        self.blat_option_editor = QLineEdit()
        self.blat_option_editor.setPlaceholderText('e.g. -minMatch=3')
        layout.addWidget(self.blat_option_editor)

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

    def get_dbfile(self):
        db_filename, _ = QFileDialog.getOpenFileName(
                                self,
                                'Open File',
                                project_folder_path(),
                                options=QFileDialog.DontUseNativeDialog,
                                filter="Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)")
                                # filter="All Files(*.*)")

        if self.window and db_filename:
            self.blatrun_db_editor.setText(db_filename)

    def get_infile(self):
        infilename, _ = QFileDialog.getOpenFileName(
                            self,
                            'Open File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter="Fasta Files(*.fa *.fas *.fna *.fasta *.gz);;All Files(*.*)")

        if self.window and infilename:
            self.blatrun_infile_editor.setText(infilename)
            out_filename = replace_ext(infilename, 'psl')
            self.blatrun_outfile_editor.setText(out_filename)

    def blatrun_out_path(self):
        infilepath = self.blatrun_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfile_path, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.psl')

        if self.window and outfile_path:
            self.blatrun_outfile_editor.setText(outfile_path)

    def is_valid_inputs(self):
        blatrun_db = self.blatrun_db_editor.text()
        if not is_valid(self, blatrun_db, 'Please check a database file.'):
            return False

        blatrun_infile =  self.blatrun_infile_editor.text()
        if not is_valid(self, blatrun_infile, 'Please check a input file.'):
            return False

        if not self.blatrun_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'Please check a out file.')
            return False

        if self.blatrun_dbtype_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a database type.')
            return False

        if self.blatrun_querytype_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a query type.')
            return False

        if self.blastrun_tilesize_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a tile size.')
            return False

        if self.blastrun_stepsize_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a step size.')
            return False

        if self.blastrun_oneoff_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a one off.')
            return False

        return True

    def run_blast(self):
        if not self.is_valid_inputs():
            return

        reply = QMessageBox.question(
                    self,
                    'Run Blat', 'Do you want to run blat?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes)

        if reply == QMessageBox.No:
            return

        try:
            self._run_blast()
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))

    def _run_blast(self):
        cmd = get_cmd('blat', category='blat')

        options = []
        
        ## db type
        dbtype_sel = self.blatrun_dbtype_cb.currentText()
        options.append('-t=' + dbtype_sel)

        ## query type
        qeurytype_sel = self.blatrun_querytype_cb.currentText()
        options.append('-q=' + qeurytype_sel)

        ## tile size
        tilesize_sel = self.blastrun_tilesize_cb.currentIndex()
        options.append('-tileSize=' + str(tilesize_sel+7))

        ## step Size
        step_sel = self.blastrun_stepsize_cb.currentIndex()
        options.append('-stepSize=' + str(step_sel))


        ## one Off
        one_sel = self.blastrun_oneoff_cb.currentIndex()
        options.append('-oneOff=' + str(one_sel))
        
        more_options = self.blat_option_editor.text()

        if more_options:
            options.extend(comamnds_to_list(more_options))
        
        dbfile = self.blatrun_db_editor.text()
        _dbfile = self.extract(dbfile, btn=self.qprocess_button)
        if not _dbfile:
            return

        options.append(_dbfile)

        ## input file
        infilename = self.blatrun_infile_editor.text()

        _infilename = self.extract(infilename, btn=self.qprocess_button)
        if not _infilename:
            return

        options.append(_infilename)

        ## output file
        out_filename = self.blatrun_outfile_editor.text()
        options.append(out_filename)

        self.qprocess_start(cmd, options)