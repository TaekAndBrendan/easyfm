import os
import gzip
import xml.etree.ElementTree as etree
from xml.etree.ElementTree import tostring

from Bio import SeqIO
from Bio.SeqIO import FastaIO
from Bio.SearchIO.BlastIO.blast_xml import BlastXmlWriter
from Bio.Blast import NCBIXML

from app.tools.utils import get_ext, is_fasta_file, replace_ext, get_compressed_file_type


def parse_xml(filter_values):
    infile = filter_values['infile']
    outfile = filter_values['outfile']
    alignment_outfile = filter_values['alignment_outfile']

    # BD = filter_values['BD']
    # BL = filter_values['BL']
    QI = filter_values['QI']
    QL = filter_values['QL']
    QS = filter_values['QS']
    QE = filter_values['QE']

    TL = filter_values['TL']
    TS = filter_values['TS']
    TE = filter_values['TE']
    
    ML = filter_values['ML']
    S = filter_values['S']
    MS = filter_values['MS']

    # MQS = filter_values['MQS']
    # C = filter_values['C']
    # MTS = filter_values['MTS']

    R = int(filter_values['R'])
    HN = int(filter_values['HN'])
    E = float(filter_values['E'])
    I = float(filter_values['I'])
    QC = float(filter_values['QC'])
    
    heads = []

    # heads =['Input_query-ID', 
    #         'Query_Length', 
    #         'Rank',
    #         'Target_Definition',
    #         'Target_Length',
    #         'Hsp_num',
    #         'Score',
    #         'E-Value',
    #         'Query_Start',
    #         'Query_End',
    #         'Query_Coverage(%)',
    #         'Target_Start',
    #         'Target_End',
    #         'Strand',
    #         'Identity(%)',
    #         'Match_Length',
    #         'Accession']

    if QI:
        heads.append('Input_query-ID')
    if QL:
        heads.append('Query_Length')

    heads.append('Rank')
    heads.append('Target_Definition')

    if TL:
        heads.append('Target_Length')

    heads.append('Hsp_num')

    if S:
        heads.append('Score')
    
    heads.append('E-Value')

    if QS:
        heads.append('Query_Start')
    if QE:
        heads.append('Query_End')

    heads.append('Query_Coverage(%)')
    
    if TS:
        heads.append('Target_Start')
    if TE:
        heads.append('Target_End')
    if MS:
        heads.append('Strand')
    
    heads.append('Identity(%)')
    
    if ML:
        heads.append('Match_Length')

    heads.append('Accession')

    result_handle = open(infile)

    blast_records = NCBIXML.parse(result_handle)

    # separator = '\t'
    separator = ','
    with open(outfile, 'w') as out_handler, open(alignment_outfile, 'w') as ali_out_handler:
        line = separator.join(heads)
        out_handler.write(line + '\n')

        for blast_record in blast_records:
            items = []
            ali_items = []

            if not blast_record.alignments:
                continue

            # sort for rank
            blast_record.alignments.sort(key = lambda align: max(hsp.score for hsp in align.hsps), reverse=True)

            if QI:
                items.append(blast_record.query) #input query-id
            if QL:
                items.append(blast_record.query_length) #query-length
            
            rank = 1

            for alignment in blast_record.alignments:

                if rank > R:
                    continue
                if len(alignment.hsps) > HN:
                    continue

                items.append(rank) #rank
                ali_items.append('rank = {}'.format(rank))
                rank = rank + 1

                items.append(alignment.hit_def) #target def

                if TL:
                    items.append(alignment.length) #target length
                
                items.append(len(alignment.hsps)) #Hsp_num


                for hsp in alignment.hsps: #Multiple hits means multiple hsps 

                    if hsp.expect > E: 
                        continue

                    identities = hsp.identities / hsp.align_length * 100
                    if identities < I:
                        continue

                    # https://www.biostars.org/p/180510/
                    # coverage = hsp.align_length / blast_record.query_length * 100
                    # coverage = (hsp.query_end - hsp.query_start +1) / blast_record.query_length * 100
                    coverage = (hsp.align_length - hsp.gaps) / blast_record.query_length * 100
                    if coverage < QC:
                        continue                        

                    if S:
                        items.append(hsp.bits) #score
                        ali_items.append('Score = {}'.format(hsp.bits)) #score
                        
                    items.append(hsp.expect) #e-value
                    ali_items.append('Expect = {}'.format(hsp.expect))#e-value

                    if QS:
                        items.append(hsp.query_start) #query_start
                    if QE:
                        items.append(hsp.query_end) #query_end
                    
                    items.append(coverage) #Query_Coverage(%)
                    if TS:
                        items.append(hsp.sbjct_start) #target start
                    if TE:
                        items.append(hsp.sbjct_end) #target end

                    if MS:
                        strand = '1' if hsp.strand==('Plus', 'Plus') else '0'
                        items.append(strand) #strand
                        ali_items.append('Strand = {}'.format(strand))
                    
                    items.append(identities) #identitiy
                    ali_items.append('Identities = {}'.format(identities))

                    if ML:
                        items.append(hsp.align_length) #match length
                    
                    items.append(alignment.accession) #accession


                    line = separator.join(list(map(lambda x: str(x), items)))

                    out_handler.write(line + '\n')

                    ############################
                    ali_out_handler.write('> {}\n'.format(alignment.hit_def))
                    ali_out_handler.write('{}\n'.format('\t'.join(list(map(lambda x: str(x), ali_items)))))
                    ali_out_handler.write('Query\n')
                    ali_out_handler.write('|\n')
                    ali_out_handler.write('Sbjct\n')
                    ali_out_handler.write('{}\n'.format(hsp.query))
                    ali_out_handler.write('{}\n'.format(hsp.match))
                    ali_out_handler.write('{}\n'.format(hsp.sbjct))


def parse_xml2(filter_values, infile, outfile):
    infile_path = filter_values['infile']
    outfile_path = filter_values['outfile']

    BD = filter_values['BD']
    BL = filter_values['BL']
    QI = filter_values['QI']
    QL = filter_values['QL']
    QS = filter_values['QS']
    QE = filter_values['QE']
    TL = filter_values['TL']
    TS = filter_values['TS']
    TE = filter_values['TE']
    ML = filter_values['ML']
    S = filter_values['S']
    MS = filter_values['MS']
    MQS = filter_values['MQS']
    C = filter_values['C']
    MTS = filter_values['MTS']

    R = filter_values['R']
    HN = int(filter_values['HN'])
    E = float(filter_values['E'])
    I = filter_values['I']
    QC = filter_values['QC']

    with open(outfile_path, 'w') as of:
        of.write('<?xml version="1.0"?>\n')
        of.write('<!DOCTYPE BlastOutput PUBLIC "-//NCBI//NCBI BlastOutput/EN" "http://www.ncbi.nlm.nih.gov/dtd/NCBI_BlastOutput.dtd">\n')

        for event, node in etree.iterparse(infile_path, events=('start', 'end')):
            if node.tag == 'BlastOutput':
                if event == 'start':
                    of.write('<BlastOutput>\n')
                if event == 'end':
                    of.write('</BlastOutput>\n')
            elif event == 'start'  and node.tag == 'BlastOutput_program':
                of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_version':
                of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_reference':
                of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_db':
                of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_query-ID':
                if QI:
                    of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_query-def':
                if BD:
                    of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_query-len':
                if BL:
                    of.write(tostring(node,  encoding='unicode'))
            elif event == 'start'  and  node.tag == 'BlastOutput_param':
                of.write(tostring(node,  encoding='unicode'))
            elif node.tag == 'BlastOutput_iterations':
                if event == 'start':
                    of.write('<BlastOutput_iterations>\n')
                if event == 'end':
                    of.write('</BlastOutput_iterations>\n')
            elif event == 'start' and node.tag == 'Iteration':
                # if len(node.findall('./Iteration_query-ID')) == 1:
                #     if TL:

                if len(node.findall('./Iteration_hits/Hit/Hit_hsps/Hsp')) == 1:
                    hsp = node.findall('./Iteration_hits/Hit/Hit_hsps/Hsp')[0]
                    
                    hsp_evalue = hsp.find('Hsp_evalue')
                    # print('float(hsp_evalue.text)')
                    # print(float(hsp_evalue.text))
                    if E != 0 and float(hsp_evalue.text) > E:
                        continue


                    hsp_num = hsp.find('Hsp_num')
                    # print('int(hsp_num.text)')
                    # print(int(hsp_num.text))
                    if HN != 0 and int(hsp_num.text) > HN:
                        continue
                    
                    hsp_evalue = hsp.find('Hsp_evalue')
                    # print('float(hsp_evalue.text)')
                    # print(float(hsp_evalue.text))
                    if E != 0 and float(hsp_evalue.text) > E:
                        continue

                    if not S:
                        hsp_score = hsp.find('Hsp_score')
                        hsp.remove(hsp_score)
                    
                    if not MQS:
                        hsp_qseq = hsp.find('Hsp_qseq')
                        hsp.remove(hsp_qseq)
                    if not C:
                        hsp_midline = hsp.find('Hsp_midline')
                        hsp.remove(hsp_midline)
                    if not MTS:
                        hsp_hseq = hsp.find('Hsp_hseq')
                        hsp.remove(hsp_hseq)
            
                    of.write(tostring(node,  encoding='unicode'))
            else:
                pass


def fasta_to_records(infile):
    handle = open(infile, 'fasta')
    return list(SeqIO.parse(handle, 'fasta'))


def fasta_to_dataframe(infile, key='name', seqkey='sequence'):
    """Get fasta proteins into dataframe"""
    recodes = SeqIO.parse(infile, 'fasta')
    keys = [key, seqkey, 'description']
    data = [(rec.name, str(rec.seq), str(rec.description)) for rec in recodes]
    return None
    # return pd.DataFrame(data, columns=(keys))


def open_blast_result_as_table(infile):
    header = ['query', 'subject',
               'pc_identity', 'aln_length', 'mismatches', 'gaps_opened',
               'query_start', 'query_end', 'subject_start', 'subject_end',
               'e_value', 'bitscore']

    return None
    # return pd.read_csv(infile, sep="\t", names=header)


def open_psl_as_table(infile):
    header = ['match', 'mis-match', 'rep.match', 'N\'s', 
                'Q gap count', 'Q gap bases', 'T gap count', 
                'T gap  bases', 'strand', 'Q name', 'Q size', 
                'Q start', 'Q end', 'T name', 'T size', 'T start', 
                'T end', 'block count', 'blockSizes', 'qStarts', 'tStarts']

    return None
    # return pd.read_csv(infile, sep='\t', skiprows=5, names=header)


def covnert_fastq_into_fasta(infilepath, outfilepath):
    if '.gz' == get_ext(infilepath):
        with gzip.open(infilepath, 'rt') as fasta_handler, open(outfilepath, 'w') as fastq_handler:
            fasta_out = FastaIO.FastaWriter(fastq_handler, wrap=None)
            for record in SeqIO.parse(fasta_handler, 'fastq'):
                fasta_out.write_record(record)
    else:
        with open(infilepath, 'r') as fasta_handler, open(outfilepath, 'w') as fastq_handler:
            fasta_out = FastaIO.FastaWriter(fastq_handler, wrap=None)
            for record in SeqIO.parse(fasta_handler, 'fastq'):
                fasta_out.write_record(record)


def reverse_complement(infilepath, outfilepath):
    if '.gz' == get_ext(infilepath):
        with gzip.open(infilepath, 'rt') as in_handler, open(outfilepath, 'w') as out_handler:
            ftype = 'fasta' if get_compressed_file_type(infilepath) == 'fa' else 'fastq'
            fasta_out = FastaIO.FastaWriter(out_handler, wrap=None)
            for record in SeqIO.parse(in_handler, ftype):
                new_record = record.reverse_complement()
                new_record.id = record.id
                new_record.name = record.name + '_R2.fasta'
                new_record.description = ''
                # SeqIO.write(new_record, out_handler, 'fasta')
                fasta_out.write_record(new_record)
    else:
        with open(infilepath, 'r') as in_handler, open(outfilepath, 'w') as out_handler:
            ftype = 'fasta' if is_fasta_file(infilepath) else 'fastq'
            fasta_out = FastaIO.FastaWriter(out_handler, wrap=None)
            for record in SeqIO.parse(in_handler, ftype):
                new_record = record.reverse_complement()
                new_record.id = record.id
                new_record.name = record.name + '_R2.fasta'
                new_record.description = ''
                # SeqIO.write(new_record, out_handler, 'fasta')
                fasta_out.write_record(new_record)


def reverse_complements(input_folder, out_folder):
    for f in os.listdir(input_folder):
        fpath = os.path.abspath(os.path.join(input_folder, f))
        if is_fasta_file(fpath):
            reverse_complement(fpath, os.path.join(out_folder, replace_ext(f, 'fa', 'R2')))
        if get_compressed_file_type(infilepath) == 'fa':
            reverse_complement(fpath, os.path.join(out_folder, replace_ext(f, 'gz', 'R2')))


def reverse(infilepath, outfilepath):
    if '.gz' == get_ext(infilepath):
        with gzip.open(infilepath, 'rt') as in_handler, open(outfilepath, 'w') as out_handler:
            ftype = 'fasta' if get_compressed_file_type(infilepath) == 'fa' else 'fastq'
            fasta_out = FastaIO.FastaWriter(out_handler, wrap=None)
            for record in SeqIO.parse(in_handler, ftype):
                new_record = record
                new_record.seq = record.seq[::-1]
                new_record.id = record.id
                new_record.name = record.name + '_R.fasta'
                new_record.description = ''
                # SeqIO.write(new_record, out_handler, 'fasta')
                fasta_out.write_record(new_record)       
    else:
        with open(infilepath, 'r') as in_handler, open(outfilepath, 'w') as out_handler:
            ftype = 'fasta' if is_fasta_file(infilepath) else 'fastq'
            fasta_out = FastaIO.FastaWriter(out_handler, wrap=None)
            for record in SeqIO.parse(in_handler, ftype):
                new_record = record
                new_record.seq = record.seq[::-1]
                new_record.id = record.id
                new_record.name = record.name + '_R.fasta'
                new_record.description = ''
                # SeqIO.write(new_record, out_handler, 'fasta')
                fasta_out.write_record(new_record)


def reverses(input_folder, out_folder):
    for f in os.listdir(input_folder):
        fpath = os.path.abspath(os.path.join(input_folder, f))
        if is_fasta_file(fpath):
            reverse(fpath, os.path.join(out_folder, replace_ext(f, 'fa', 'R')))
        if get_compressed_file_type(infilepath) == 'fa':
            reverse_complement(fpath, os.path.join(out_folder, replace_ext(f, 'gz', 'R')))