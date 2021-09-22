from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)
from app.gui.utils import ScrollLabel

class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

        layout = QHBoxLayout()        
        text = "<h3>easyfm</h3>" \
               "<p><b>easyfm</b> has four main tools: <i>Blast</i>, <i>Blat</i>, <i>ORF</i> and <i>File Manipulation.</i></p>" \
               "<h4>Blast</h4>" \
               "<p><a href='https://www.ncbi.nlm.nih.gov/books/NBK279690/'>BLAST® Command Line Applications User Manual</a></p>" \
               "<p><ul>"\
               "<li>Create database - <a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/makeblastdb.txt'> command  options</a></li>" \
               "<li>Run Blast - command options</li>" \
               "<ul>" \
               "<li><a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/blastn.txt'>blastn</a></li>" \
               "<li><a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/blastp.txt'>blastp</a></li>" \
               "<li><a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/blastx.txt'>blastx</a></li>" \
               "<li><a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/tblastn.txt'>tblastn</a></li>" \
               "<li><a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/tblastx.txt'>tblastx</a></li>" \
               "</ul>" \
               "<li>Convert Blast result - <a href='https://home.cc.umanitoba.ca/~psgendb/doc/NCBI/blast_formatter.txt'> command  options</a> </li>"\
               "<li>Parse Blast XML result</li>"\
               "</ul></p>" \
               "<h4>Blat</h4>" \
               "<p><a href='https://www.blat.net'>What is Blat?</a> </p>" \
               "<p>Run Blat - <a href='https://genome.ucsc.edu/goldenpath/help/blatSpec.html'>command options</a></p>" \
               "<h4>ORFs (Open Reading Frames)</h4>" \
               "<p><a href='https://vlab.amrita.edu/index.php?sub=3&brch=273&sim=1432&cnt=1'>Finding ORF of a Given Sequence</a></p>" \
               "<p><a href='https://www.ncbi.nlm.nih.gov/orffinder/'>orffinder</a> on the web</p>" \
               "<h4>File Manipulation</h4>" \
               "<p><ul>"\
               "<li>Index/Extract</li>" \
               "<li>Sequence Reverse</li>" \
               "<li>Convert FastQ to FastA</li>"\
               "<li>Extract GFF/GTF</li>"\
               "</ul></p>"
        # creating scroll label
        label = ScrollLabel(self)
 
        # setting text to the label
        label.setText(text)

        layout.addWidget(label)

        main_layout.addLayout(layout)
