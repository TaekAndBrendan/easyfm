import unittest

from blastapp.tools.biofiles import *

class TestFastautils(unittest.TestCase):
 
    # def test_hello(self):
    #     self.assertEqual('hellwso', say_hello())

    # def test_create_db(self):
    #     path = config['data']
    #     dbfile = os.path.normpath(os.path.join(path, './pdbaa'))
    #     create_blast_database(dbfile, dbtype='prot')

    # def test_blast_file(self):
    #     data = config['data']
    #     infile = os.path.normpath(os.path.join(data, 'test.fna'))
        # blast_file('pdbaa', infile, cmd='blastp')


    def test_find_orfs_with_trans(self):
        data = config['data']
        infile = os.path.normpath(os.path.join(data, 'NC_005816.fna'))
        find_orfs_with_trans(infile)

if __name__ == '__main__':
    unittest.main()