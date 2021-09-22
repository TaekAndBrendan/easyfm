import os
import unittest

from blastapp.tools.config import config
from blastapp.tools.utils import *

class TestToolsUtils(unittest.TestCase):

    """
    def test_fetch_file_from(self):
        path = config['libs'] + '/any2fasta'
        
        fetch_file_from('https://github.com/tseemann/any2fasta/blob/cdec1f06c580c966a7a18874bf5c6e048bbe597f/any2fasta', 'any2fasta')
        self.assertTrue(os.path.exists(path))
     """

    # def test_get_cmd(self):
    #     path = config['libs']
    #     cmd = os.path.normpath(os.path.join(path, './ncbi-blast/bins', 'blastn'))
    #     self.assertEqual(get_cmd('blastn'), cmd)

    # def test_cpu_count(self):
    #     self.assertEqual(cpu_count(), 2)

    def test_init(self):
        init()
if __name__ == '__main__':
    unittest.main()