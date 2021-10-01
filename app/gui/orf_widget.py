from PyQt5.QtCore import (
    Qt,
    QDir,
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
    QMessageBox,
)

from app.tools.orf import find_orf
from app.gui.utils import (
    QProcessWidgetUtil,
    BaseWidgetUtil,
    IconLabel,
    is_valid,
)
from app.tools.utils import (
    project_folder_path,
    replace_ext,
    get_filepath_project,
)


class ORFWidget(QWidget):
    def __init__(self, window=None, parent=None):
        super(ORFWidget, self).__init__(parent)
        self.window = window

        orf_tab = QTabWidget()
        orf_tab.tabBar().setObjectName("orf_tab_tab")

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(orf_tab)

        # run widget
        blastrun_widget = ORFFinderWidget(window=window)
        orf_tab.addTab(blastrun_widget, 'ORF Run')
        orf_tab.setCurrentIndex(0)


class ORFFinderWidget(QWidget, BaseWidgetUtil):
    def __init__(self, window=None, parent=None):
        super(ORFFinderWidget, self).__init__(parent)
        self.window = window
        self.init_ui()


    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setLayout(main_layout)

        main_layout.addWidget(IconLabel('Light weight only (Recommended to use a small set data).'))

        layout = QHBoxLayout()
        layout.addWidget(QLabel('Input File'))

        self.browser_file_editor = QLineEdit()
        layout.addWidget(self.browser_file_editor)

        browser_file_button = QPushButton('Browse')
        layout.addWidget(browser_file_button)

        browser_file_button.clicked.connect(self.browse_file)

        main_layout.addLayout(layout)

        # Out file
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Nucleotide Out File'))

        self.orf_nucl_outfile_editor = QLineEdit()
        layout.addWidget(self.orf_nucl_outfile_editor)

        self.orf_nucl_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.orf_nucl_out_path_button)

        self.orf_nucl_out_path_button.clicked.connect(self.orf_nucl_out_path)

        main_layout.addLayout(layout)

        layout = QHBoxLayout()
        layout.addWidget(QLabel('Protein Out File'))

        self.orf_prot_outfile_editor = QLineEdit()
        layout.addWidget(self.orf_prot_outfile_editor)

        self.orf_prot_out_path_button = QPushButton('Change Folder')
        layout.addWidget(self.orf_prot_out_path_button)

        self.orf_prot_out_path_button.clicked.connect(self.orf_prot_out_path)

        main_layout.addLayout(layout)

        layout = QHBoxLayout()

        # genetic code, dropbox
        self.genetic_code_cb = QComboBox()
        self.genetic_code_cb.addItem('Genetic code')
        self.genetic_code_cb.addItem('1. The Standard Code')
        self.genetic_code_cb.addItem('2. The Vertebrate Mitochondrial Code')
        self.genetic_code_cb.addItem('3. The Yeast Mitochondrial Code')
        self.genetic_code_cb.addItem('4. The Mold, Protozoan, and Coelenterate Mitochondrial Code and the Mycoplasma/Spiroplasma Code')
        self.genetic_code_cb.addItem('5. The Invertebrate Mitochondrial Code')
        self.genetic_code_cb.addItem('6. The Ciliate, Dasycladacean and Hexamita Nuclear Code')
        self.genetic_code_cb.addItem('9. The Echinoderm and Flatworm Mitochondrial Code')
        self.genetic_code_cb.addItem('10. The Euplotid Nuclear Code')
        self.genetic_code_cb.addItem('11. The Bacterial, Archaeal and Plant Plastid Code')
        self.genetic_code_cb.addItem('12. The Alternative Yeast Nuclear Code')
        self.genetic_code_cb.addItem('13. The Ascidian Mitochondrial Code')
        self.genetic_code_cb.addItem('14. The Alternative Flatworm Mitochondrial Code')
        self.genetic_code_cb.addItem('16. Chlorophycean Mitochondrial Code')
        self.genetic_code_cb.addItem('21. Trematode Mitochondrial Code')
        self.genetic_code_cb.addItem('22. Scenedesmus obliquus Mitochondrial Code')
        self.genetic_code_cb.addItem('23. Thraustochytrium Mitochondrial Code')
        self.genetic_code_cb.addItem('24. Rhabdopleuridae Mitochondrial Code')
        self.genetic_code_cb.addItem('25. Candidate Division SR1 and Gracilibacteria Code')
        self.genetic_code_cb.addItem('26. Pachysolen tannophilus Nuclear Code')
        self.genetic_code_cb.addItem('27. Karyorelict Nuclear Code')
        self.genetic_code_cb.addItem('28. Condylostoma Nuclear Code')
        self.genetic_code_cb.addItem('29. Mesodinium Nuclear Code')
        self.genetic_code_cb.addItem('30. Peritrich Nuclear Code')
        self.genetic_code_cb.addItem('31. Blastocrithidia Nuclear Code')
        self.genetic_code_cb.addItem('33. Cephalodiscidae Mitochondrial UAA-Tyr Code')
        self.genetic_code_cb.setCurrentIndex(0)
        layout.addWidget(self.genetic_code_cb)

        # min length, edit
        min_label = QLabel("Minimum Length")
        layout.addWidget(min_label)

        self.min_editor = QLineEdit()
        self.min_editor.setText('10')
        layout.addWidget(self.min_editor)

        # max length, edit
        max_label = QLabel("Maximum Length")
        layout.addWidget(max_label)

        self.max_editor = QLineEdit()
        self.max_editor.setText('Max')
        layout.addWidget(self.max_editor)

        main_layout.addLayout(layout)

        # buttons
        layout = QHBoxLayout()
        layout.addStretch()

        self.qprocess_button = QPushButton('Find ORF')
        layout.addWidget(self.qprocess_button)
        self.qprocess_button.clicked.connect(self.run_orfs)

        main_layout.addLayout(layout)

    def browse_file(self):
        filename, _ = QFileDialog.getOpenFileName(
                            self,
                            'Open File',
                            project_folder_path(),
                            options=QFileDialog.DontUseNativeDialog,
                            filter="Fasta Files(*.fa *.fna *.fasta *.gz);;All Files(*.*)")

        if self.window and filename:
            self.browser_file_editor.setText(filename)
           
            nucl_out_filename = replace_ext(filename, 'nucl.fa')
            self.orf_nucl_outfile_editor.setText(nucl_out_filename)

            prot_out_filename = replace_ext(filename, 'prot.fa')
            self.orf_prot_outfile_editor.setText(prot_out_filename)

    def orf_nucl_out_path(self):
        infilepath = self.orf_nucl_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfilepath, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfilepath:
            self.orf_nucl_outfile_editor.setText(outfilepath)

    def orf_prot_out_path(self):
        infilepath = self.orf_prot_outfile_editor.text()
        filepath_project = get_filepath_project(infilepath)
        outfilepath, _ = QFileDialog.getSaveFileName(self, 
                                            'Select Folder',
                                            filepath_project,
                                            '.fa')

        if self.window and outfilepath:
            self.orf_prot_outfile_editor.setText(outfilepath)


    def is_valid_inputs(self):
        browser_file = self.browser_file_editor.text()
        if not is_valid(self, browser_file, 'Please check a input file.'):
            return False

        if not self.orf_nucl_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'Please check a nucleotide out file.')
            return False

        if not self.orf_prot_outfile_editor.text():
            QMessageBox.about(self, 'Information', 'Please check a protein out file.')
            return False

        if self.genetic_code_cb.currentIndex() == 0:
            QMessageBox.about(self, 'Information', 'Please check a genetic code.')
            return False
        
        if not self.min_editor.text().isdigit():
            QMessageBox.about(self, 'Information', 'Please check a minimum length ORF.')
            return False

        if not self.max_editor.text() == 'Max' and not self.max_editor.text().isdigit():
            QMessageBox.about(self, 'Information', 'Please check a maximum length ORF.')
            return False

        return True

    def run_orfs(self):
        if not self.is_valid_inputs():
            return

        # TODO : check QMessageBox to change
        reply = QMessageBox.question(self, 'Find open reading frame',
                                    'Do you want to find open reading frame?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.Yes)
        if reply == QMessageBox.No:
            return

        try:
            self._run_orfs()
        except Exception as e:
            QMessageBox.about(self, 'Error', str(e))    

    def _run_orfs(self):
        infilename = self.browser_file_editor.text()

        _infilename = self.extract(infilename, btn=self.qprocess_button)
        if not _infilename:
            return

        nucl_outfilename = self.orf_nucl_outfile_editor.text()
        prot_outfilename = self.orf_prot_outfile_editor.text()

        min_text = self.min_editor.text()
        minProLen = int(min_text)

        max_text = self.max_editor.text()
        maxProLen = 0 if max_text == 'Max' else int(max_text)

        translationTable = self.genetic_code_cb.currentIndex()
        orf_dict = {}
        orf_dict['fileName'] = _infilename
        orf_dict['nuclfileName'] = nucl_outfilename
        orf_dict['protfileName'] = prot_outfilename
        orf_dict['minProLen'] = minProLen
        orf_dict['maxProLen'] = maxProLen
        orf_dict['translationTable'] = translationTable

        self.orf_save_worker = ORFSaveWorker(orf_dict)
        self.orf_save_worker.started.connect(self.worker_started_callback)
        self.orf_save_worker.finished.connect(self.worker_finished_callback)
        self.orf_save_worker.start()

    def worker_started_callback(self):
        self.qprocess_button.setText('Processing...')
        self.qprocess_button.setEnabled(False)

    def worker_finished_callback(self):
        nucl_outfilename = self.orf_nucl_outfile_editor.text()
        prot_outfilename = self.orf_prot_outfile_editor.text()
        QMessageBox.about(self, 'Saved Fasta', 'Saved fasta in <b>{}</b> and <b>{}</b>.'.format(nucl_outfilename, prot_outfilename))
        self.qprocess_button.setText('Find ORFs')
        self.qprocess_button.setEnabled(True)


class ORFSaveWorker(QThread):
    # data = pyqtSignal(dict)
    def __init__(self, orf_dict, parent=None):
        super(ORFSaveWorker, self).__init__(parent)
        self._stopped = True
        self._mutex = QMutex()
        self.orf_dict = orf_dict

    def stop(self):
        self._mutex.lock()
        self._stopped = True
        self._mutex.unlock()

    def run(self):
        self._stopped = False
        find_orf(self.orf_dict)
