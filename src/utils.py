import os
from pathlib import Path
import re
import pickle
import sys
import pandas as pd
import allel  # type: ignore[import-untyped]
import math
from Bio.Seq import reverse_complement  # type: ignore[import-untyped]
from liftover import ChainFile  # type: ignore[import-untyped]
from pyfaidx import Fasta  # type: ignore[import-untyped]

REPO_ROOT = Path(__file__).parent.parent
MODEL_DIR = REPO_ROOT / 'src' / 'trained_models'

def hg38tohg19(vcf:pd.DataFrame, fasta:Fasta) -> pd.DataFrame:

    """
    Convert hg38 coordinates to hg19
    """

    converter = ChainFile(REPO_ROOT / 'requirements/hg38ToHg19.over.chain.gz', one_based=True)
    for i, row in vcf.iterrows():
        chrom: str = str(row['CHROM'])
        pos: int = int(row['POS'])  # 1-based position
        vcf_REF: str = row['REF']
        vcf_ALT: str = row['ALT']

        # Only process SNPs and MNPs, discard indels
        if len(vcf_REF) != len(vcf_ALT):
            vcf.at[i, 'CHROM'] = 'Remove'
            continue
        
        # Try different chromosome name formats, get matching targets
        for chr in [chrom, chrom.replace('chr', ''), f'chr{chrom}']:
            try:
                targets = converter[chr][pos]
                break
            except IndexError:
                continue
        else:
            print(
                f'Liftover Warning: no mapping for hg38 {chrom}:{pos}', 
                file=sys.stderr
            )
            vcf.at[i, 'CHROM'] = 'Remove'
            continue

        # Only keep one-to-one mappings
        if len(targets) > 1:
            print(
                f'Liftover Warning: multiple mappings for hg38 {chrom}:{pos} -> {targets}', 
                file=sys.stderr
            )
            vcf.at[i, 'CHROM'] = 'Remove'
            continue
        elif len(targets) == 0:  # No mappings
            vcf.at[i, 'CHROM'] = 'Remove'
            continue
        
        target_chr, target_pos, target_strand = targets[0]

        if target_strand == '+':
            target_start = target_pos
            target_end = target_pos + len(vcf_REF) - 1
        elif target_strand == '-':
            target_start = target_pos - len(vcf_REF) + 1
            target_end = target_pos
            vcf_REF = reverse_complement(vcf_REF)
            vcf_ALT = reverse_complement(vcf_ALT)
        else:
            print(
                f'Liftover Warning: invalid strand for hg38 {chrom}:{pos} -> hg19 {target_chr}:{target_pos} ({target_strand})', 
                file=sys.stderr
            )
            vcf.at[i, 'CHROM'] = 'Remove'
            continue

        ref_context = fasta[target_chr][target_start-2:target_end+1].seq.upper()  # uses 0-based

        if vcf_REF != ref_context[1:-1]:
            print((
                f'Liftover Warning: ref mismatch at hg38 {chrom}:{pos} -> hg19 {target_chr}:{target_start}-{target_end} '
                f'-- VCF REF: {vcf_REF} (ALT: {vcf_ALT}) vs Reference hg19: {ref_context[1:-1]} '
                f'-- Reference context: {ref_context}'
            ), file=sys.stderr)
            vcf.at[i, 'CHROM'] = 'Remove'
            continue

        vcf.at[i, 'CHROM'] = target_chr
        vcf.at[i, 'POS'] = target_start
        vcf.at[i, 'REF'] = vcf_REF
        vcf.at[i, 'ALT'] = vcf_ALT

    return(vcf)

def process_dnp(vcf:pd.DataFrame) -> pd.DataFrame:

    """
    Split DNPs into two different SNPs
    """

    # Select DNPs positions
    dnps = vcf[(vcf['REF'].str.len() == 2) & (vcf['ALT'].str.len() == 2)]

    # Duplicate the DNPs and create the second SNP
    dnps_dup = dnps.copy()
    dnps_dup['REF'] = dnps_dup['REF'].str[1]
    dnps_dup['ALT'] = dnps_dup['ALT'].str[1]
    dnps_dup['POS'] = dnps_dup['POS'] + 1
    dnps_dup['is_snp'] = True

    # Modify the original DNPs to create the first SNP
    vcf.loc[dnps.index, 'REF'] = dnps['REF'].str[0]
    vcf.loc[dnps.index, 'ALT'] = dnps['ALT'].str[0]
    vcf.loc[dnps.index, 'is_snp'] = True

    # Concatenate the original df with the duplicated rows
    new_vcf = pd.concat([vcf, dnps_dup], ignore_index=True).sort_values(by=['CHROM', 'POS'])

    return(new_vcf.reset_index(drop=True))

def process_tnp(vcf:pd.DataFrame) -> pd.DataFrame:

    """
    Split TNPs into three different SNPs
    """

    # Select TNPs positions
    tnps = vcf[(vcf['REF'].str.len() == 3) & (vcf['ALT'].str.len() == 3)]

    # Duplicate the TNPs and create the second SNP
    tnps_dup_second = tnps.copy()
    tnps_dup_second['REF'] = tnps_dup_second['REF'].str[1]
    tnps_dup_second['ALT'] = tnps_dup_second['ALT'].str[1]
    tnps_dup_second['POS'] = tnps_dup_second['POS'] + 1
    tnps_dup_second['is_snp'] = True

    # Duplicate the TNPs and create the third SNP
    tnps_dup_third = tnps.copy()
    tnps_dup_third['REF'] = tnps_dup_third['REF'].str[2]
    tnps_dup_third['ALT'] = tnps_dup_third['ALT'].str[2]
    tnps_dup_third['POS'] = tnps_dup_third['POS'] + 2
    tnps_dup_third['is_snp'] = True

    # Modify the original TNPs to create the first SNP
    vcf.loc[tnps.index, 'REF'] = tnps['REF'].str[0]
    vcf.loc[tnps.index, 'ALT'] = tnps['ALT'].str[0]
    vcf.loc[tnps.index, 'is_snp'] = True

    # Concatenate the original df with the duplicated rows
    new_vcf = pd.concat([vcf, tnps_dup_second, tnps_dup_third], ignore_index=True).sort_values(by=['CHROM', 'POS'])

    return(new_vcf.reset_index(drop=True))

def vcf2df(vcf_path:str, prefix:bool, liftOver:bool, fasta: Fasta) -> pd.DataFrame:

    """
    Filter SNVs in chr1-chr22 from VCF file and return a dataframe
    """

    # Open VCF
    vcf:pd.DataFrame = allel.vcf_to_dataframe(vcf_path, fields='*', alt_number=1)
    vcf.drop_duplicates(inplace=True)
    vcf.reset_index(drop=True, inplace=True)

    # LiftOver coordinates if the original VCF is in hg38
    if liftOver:
        vcf = hg38tohg19(vcf, fasta)

    # Select chromosomes
    chr_list: list
    if prefix:
        chr_list = [f"chr{str(chrom)}" for chrom in range(1, 23)]
    else:
        chr_list = [str(chrom) for chrom in range(1, 23)]

    # Update chromosome names
    if prefix and not (vcf['CHROM'][0].startswith('chr')):
        vcf['CHROM'] = [f"chr{str(chrom)}" for chrom in vcf['CHROM']]
    elif not prefix and (vcf['CHROM'][0].startswith('chr')):
        vcf['CHROM'] = [str(chrom).replace('chr', '') for chrom in vcf['CHROM']]
    else:
        pass

    # Split DNPs and TNPs
    vcf = process_dnp(vcf)
    vcf = process_tnp(vcf)

    # Filter SNVs in chr1-chr22
    if 'FILTER_PASS' in vcf.columns:
        pass_filter = vcf['FILTER_PASS'] == True
    elif 'FILTER' in vcf.columns:
        pass_filter = vcf['FILTER'] == 'PASS'
    else:
        pass_filter = True  # No filter column, keep all

    vcf_filter:pd.DataFrame = vcf[(vcf['is_snp'] == True) & (vcf['CHROM'].isin(chr_list)) & (vcf['REF'] != '-') & (vcf['ALT'] != '-') & pass_filter]

    return(vcf_filter.reset_index(drop=True))

def df2bins(df:pd.DataFrame, sample_name:str, prefix:bool) -> pd.DataFrame:

    """
    Convert the dataframe to bin counts
    """

    # Load the header of the bins
    header_bins:pd.DataFrame = pd.read_csv(MODEL_DIR / 'hg19.1Mb.header.gz', compression='gzip', header=None)

    # Update chromosome names
    if not prefix:
        header_bins.iloc[:, 0] = header_bins.iloc[:, 0].apply(lambda x: str(x).replace('chr', ''))

    # Get bins from the df
    df_bins:pd.Series = df.CHROM + '.' + df.POS.apply(lambda x: int(math.floor(float(x) / 1000000))).astype(str)
    bins:pd.DataFrame = pd.DataFrame({'bins': pd.Series(pd.Categorical(df_bins, categories=header_bins.iloc[:, 0]))})

    # Group bins and count
    bins = bins.groupby('bins').size().reset_index(name=sample_name)

    return(bins)

def df2mut(df:pd.DataFrame, sample_name:str, fasta:Fasta) -> pd.DataFrame:

    """
    Convert the dataframe to mutation types
    """

    # Load the header of the mutation types
    header_muts:pd.DataFrame = pd.read_csv(MODEL_DIR / 'Mut-Type-Header.csv')

    # Load Z-Norm parameters
    with open(MODEL_DIR / "z-norm.pkl", "rb") as f:
        z_norm:dict = pickle.load(f)

    # Extract the mutation types
    changes:list = []
    for _,row in df.iterrows():
        chrom = str(row['CHROM'])
        pos = int(row['POS'])
        ref = str(row['REF'])
        alt = str(row['ALT'])

        # convert 1-based VCF POS to 0-based coordinate for pyfaidx
        pos0 = pos - 1
        start = pos0 - 1      # want one base upstream (0-based)
        end = pos0 + 2        # end-exclusive: pos0 + 2 will include pos0 and pos0+1 (3 total bases)

        # clamp start to 0 to avoid negative slice
        start_clamped = max(0, start)

        # Try fetching sequence, with a fallback to add/remove 'chr' if necessary
        try:
            ref_ctx = fasta[chrom][start_clamped:end].seq.upper()
        except KeyError:
            # try toggling 'chr' prefix
            alt_chrom = ('chr' + chrom) if not chrom.startswith('chr') else chrom[3:]
            try:
                ref_ctx = fasta[alt_chrom][start_clamped:end].seq.upper()
                chrom = alt_chrom  # use the fasta name going forward
            except Exception as e:
                print(f"Skipping {chrom}:{pos} — chromosome not in FASTA ({e})", file=sys.stderr)
                continue
        except Exception as e:
            print(f"Skipping {chrom}:{pos} — error fetching FASTA slice: {e}", file=sys.stderr)
            continue

        # If returned context is too short, report and skip
        if len(ref_ctx) < 3:
            print(
                f"Skipping {chrom}:{pos} — context too short (got {len(ref_ctx)} bp) "
                f"requested start={start} end={end} (clamped_start={start_clamped})",
                file=sys.stderr
            )
            continue

        if ref != ref_ctx[1]:
            print(
                '-----------------------------------\n'
                "WARNING: Reference base from VCF file doesn't match reference genome\n"
                f'{chrom}:{pos} -- VCF: {ref} vs Reference genome: {ref_ctx[1]} -- Reference context: {ref_ctx}\n'
                '-----------------------------------',
                file=sys.stderr
            )
            continue

        # Get the reverse complement if necessary
        if (re.search('[GT]', ref)):
            ref = reverse_complement(ref)
            alt = reverse_complement(alt)
            ref_ctx = reverse_complement(ref_ctx)

        # Calculate the mutation types
        ## Single context
        changes.append(f'{ref}..{alt}')
        ## Binucleotide context
        changes.append(f'{ref_ctx[:-1]}..{ref_ctx[0]}{alt}')
        changes.append(f'{ref_ctx[1:]}..{alt}{ref_ctx[-1]}')
        ## Trinucleotide context
        changes.append(f'{ref_ctx}..{ref_ctx[0]}{alt}{ref_ctx[-1]}')

    # Group mutation types and count
    mutations:pd.DataFrame = pd.DataFrame({"bins": pd.Series(pd.Categorical(changes, categories=header_muts.iloc[:, 0]))})
    mutations = mutations.groupby('bins').size().reset_index(name=sample_name)
    # Calculate proportions for each range
    if sum(mutations[sample_name]) > 0:
        sgl_prop = mutations[sample_name].iloc[0:6] / mutations[sample_name].iloc[0:6].sum()
        di_prop = mutations[sample_name].iloc[6:54] / mutations[sample_name].iloc[6:54].sum()
        tri_prop = mutations[sample_name].iloc[54:150] / mutations[sample_name].iloc[54:150].sum()
        mutations.loc[0:5, sample_name] = sgl_prop
        mutations.loc[6:53, sample_name] = di_prop
        mutations.loc[54:149, sample_name] = tri_prop

        ## z-norm
        mutations[mutations.columns[1:]] = mutations.apply(lambda x: (x[1:] - z_norm[x['bins']]['mean']) / z_norm[x['bins']]['std'], axis=1)

    return(mutations)

def vcf2input(vcf:str, refGenome:str, liftOver:bool) -> pd.DataFrame:

    """
    Process the VCF to get the input necessary for DeepTumour
    """

    # Create output name
    sample_name:str = os.path.basename(vcf).replace('.vcf', '')

    # Load the reference genome
    fasta:Fasta = Fasta(refGenome)
    prefix:bool = list(fasta.keys())[0].startswith('chr')

    # Load the VCF
    df:pd.DataFrame = vcf2df(vcf, prefix, liftOver, fasta)

    # Convert the dataframe to bin counts
    bins:pd.DataFrame = df2bins(df, sample_name, prefix)

    # Convert the dataframe to mutation types
    mutations:pd.DataFrame = df2mut(df, sample_name, fasta)

    # Merge the dataframes
    input:pd.DataFrame = pd.concat([bins, mutations]).set_index('bins')
    input = input.transpose()
    input.reset_index(drop=False, inplace=True)

    return(input)
