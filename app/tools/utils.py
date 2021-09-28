import os
import urllib.request
import platform
import multiprocessing
import logging
import datetime
import subprocess
import re
from distutils.dir_util import copy_tree
from configparser import SafeConfigParser
import gzip
import shutil

import gffutils

from app.tools.config import config, preference


def init_tool():
    """set up"""
    read_config()
    init_dirs()
    # setup_log()


def init_dirs():
    project_folder = project_folder_path()
    if not os.path.exists(project_folder):
        os.makedirs(project_folder)
        

def setup_log():
    filename = os.path.join(config['log'], 'app.log')
    if os.path.exists(filename):
        newfile = datetime.datetime.today().strftime('%d-%b-%Y')
        os.rename(filename, os.path.join(config['log'], newfile + '.log'))

    logging.basicConfig(filename=filename, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.info('Set up log')
    # logging.error("Exception occurred", exc_info=True)


def log(msg):
    logging.info(msg)


def get_cmd(command, category='blast'):
    lib_path = config['libs']

    if category == 'blat':
        if platform.system() == 'Windows':
            return os.path.normpath(os.path.join(lib_path, './blat/exes', command + ".exe"))
        elif platform.system() == 'Linux':
            return os.path.normpath(os.path.join(lib_path, './blat/bins', command))
        else:
            return os.path.normpath(os.path.join(lib_path, './blat/bins', command))
    elif category == 'blast':
        if platform.system() == 'Windows':
            return os.path.normpath(os.path.join(lib_path, './ncbi-blast/exes', command + ".exe"))
        elif platform.system() == 'Linux':
            return os.path.normpath(os.path.join(lib_path, './ncbi-blast/bins', command))
        else:
            return os.path.normpath(os.path.join(lib_path, './ncbi-blast/bins', command))
    elif category == 'bin':
        if platform.system() == 'Windows':
            return os.path.normpath(os.path.join(config['script'], command + ".exe"))
        elif platform.system() == 'Linux':
            return os.path.normpath(os.path.join(config['bin'], command))

    return "";

def cpu_count():
    return multiprocessing.cpu_count()

def get_filesize(infile):
    file_size = os.path.getsize(infile)
    return convert_unit(file_size)

def convert_unit(size_in_bytes):
    """ Convert the size from bytes to other units like KB, MB or GB"""
    for i in range(3, 0, -1):
        s = size_in_bytes / pow(1024, i)
        if s > 1:
            if i == 3:
                return '%10.2f GB' % s
            elif i == 2:
                return '%10.2f MB' % s
            else:
                return '%10.2f KB' % s

    return ''

def get_fasta_info(filename):
    import pyfastx

    fa = pyfastx.Fasta(filename)

    fasta_info = {}
    # fasta_info['File'] = filename
    # fasta_info['Size'] = get_filesize(filename)
    fasta_info['Type'] = fa.type
    fasta_info['Total Sequence(bp)'] = '{:,}'.format(fa.size)
    fasta_info['Sequence Counts'] = '{:,}'.format(len(fa))
    fasta_info['Sequence Average Length(bp)'] = '{:,}'.format(fa.mean)
    fasta_info['Seqeunce Median Length(bp)'] = '{:,}'.format(fa.median)
    fasta_info['GC Content(%)'] = '{:.2f}'.format(fa.gc_content)
    fasta_info['N50 and L50(bp)'] = fa.nl(50)
    fasta_info['N75 and L75(bp)'] = fa.nl(75)
    fasta_info['N90 and L90(bp)'] = fa.nl(90)
    return fasta_info


def project_folder_path():
    return preference['project_folder'] if preference and 'project_folder'in preference else config['app']


def replace_ext(file_path, new_file_extension, extra=None):
    filename, file_extension = os.path.splitext(file_path)
    f, e = os.path.splitext(filename) # remove .
    return '{}.{}.{}'.format(f, extra, new_file_extension) if extra else '{}.{}'.format(f, new_file_extension)


def replace_folder(folder_path, file_path):
    folder, filename = os.path.split(file_path)
    return os.path.join(folder_path, filename)


def read_config():
    parser = SafeConfigParser()

    if os.path.exists(os.path.join(config['app'], '.config')):
        parser.read(os.path.join(config['app'], '.config'))
        for section_name in parser.sections():
            for name, value in parser.items(section_name):
                preference[name] = value


def write_config():
    parser = SafeConfigParser()
    parser.add_section('preference')

    for key, value in preference.items():
        parser.set('preference', key, value)

    with open(os.path.join(config['app'], '.config'), 'w') as writer:
        parser.write(writer)

    # update config
    read_config()


def open_default_application(filepath):
    if platform.system() == 'Darwin':
        subprocess.call(('open', filepath))
    elif platform.system() == 'Windows':
        os.startfile(filepath)
    else:
        subprocess.call(('xdg-open', filepath))


def open_default_texteditor(filepath):
    try:
        if platform.system() == 'Darwin':
            subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':
            subprocess.Popen(['notepad.exe', filepath])
        else:
            os.system('gedit {}'.format(filepath))
    except Exception as e:
        raise e


def get_filepath_project(filepath):
    filename = os.path.basename(filepath)
    return os.path.join(project_folder_path(), filename)


def get_compressed_file_type(filepath):
    filename, ext = os.path.splitext(filepath)
    if ext.lower() in ('.gz', '.zip'):
        if is_fasta_file(filename):
            return 'fa'

        if is_fastq_file(filename):
            return 'fq'

    return None


def is_fasta_file(filepath):
    return True if get_ext(filepath) in ('.fa', '.fasta', '.fas', '.fna') else False


def is_fastq_file(filepath):
    return True if get_ext(filepath) in ('.fq', '.fastaq') else False


def is_fastx_file(filepath):
    return True if is_fasta_file(filepath) or is_fastq_file(filepath) else False
    # if is_fasta_file(filepath) or is_fastq_file(filepath):
    #     return True
    # return False


def is_table_file(filepath):
    return True if get_ext(filepath) in ('.psl') else False


def get_ext(filepath):
    filename, ext = os.path.splitext(filepath)
    return ext.lower()


def get_valid_filename(filename):
    filename = str(filename).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', filename)


def get_gff_features(infilepath):
    data = []
    seqs = set()
    ftypes = set()

    with open(infilepath, 'r') as f:
        feature_line = f.readline()
        while feature_line:
            if feature_line.startswith('#'):
                feature_line = f.readline()
                continue
            features = feature_line.split('\t')
            seqs.add(features[0])
            ftypes.add(features[2])
            data.append(features)
            feature_line = f.readline()

    return data, seqs, ftypes


def filter_gff_features(features, seq=None, ftype=None, strand=None):
    data = []
    for feature in features:
        if seq == None and ftype == None and strand == None:
            data.append(feature)
        elif seq and ftype == None and strand == None:
            if feature[0] == seq:
                data.append(feature)
        elif seq == None and ftype and strand == None:
            if feature[2] == ftype:
                data.append(feature)
        elif seq == None and ftype == None and strand:
            if feature[6] == strand:
                data.append(feature)
        elif seq and ftype and strand == None:
            if feature[0] == seq and feature[2] == ftype:
                data.append(feature)
        elif seq and ftype == None and strand:
            if feature[0] == seq and feature[6] == strand:
                data.append(feature)
        elif seq == None and ftype and strand:
            if feature[2] == ftype and feature[6] == strand:
                data.append(feature)
        elif seq and ftype and strand:
            if feature[0] == seq and feature[2] == ftype and feature[6] == strand:
                data.append(feature)
    return data


def comamnds_to_list(options_string):
    temp_options_string = options_string

    l = []
    i, c = get_next_option(temp_options_string)
    while i>=0:
        if c:
            e = temp_options_string[1::].find('"')
            w = '\"{}\"'.format(temp_options_string[1:e+1])
            l.append(w)
            temp_options_string = temp_options_string[e+3::]
            i, c  = get_next_option(temp_options_string)
            continue
            
        w = temp_options_string[0:i]
        l.append(w)
        temp_options_string = temp_options_string[i+1::]
        i, c  = get_next_option(temp_options_string)

    if temp_options_string:
        l.append(temp_options_string)

    return l


def get_next_option(options_string):
    s = options_string.find(' ')
    c = options_string.find('"')
    if c!= -1 and c < s:
        return c, True

    return s, False