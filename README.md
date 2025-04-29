# DeepTumour

The DeepTumour algorithm predicts the tissue of origin of a tumour based on the pattern of passenger mutations identified by Whole Genome Sequencing (WGS).


## Running DeepTumour

**Requirements:**
- [hg19](https://hgdownload.soe.ucsc.edu/goldenPath/hg19/bigZips/latest/) reference (`.fa` & `.fa.fai`)


### Docker

1. Study the command options:
    ```sh
    docker run --rm ghcr.io/LincolnSteinLab/DeepTumour:latest --help
    ```

2. Run DeepTumour _(assuming VCFs and reference are under the current working directory)_:
    ```sh
    docker run --rm -a stdout -a stderr -v .:/WORKDIR ghcr.io/LincolnSteinLab/DeepTumour:latest [OPTIONS] --stdout > [OUTPUT_JSON]
    ```


### Local Environment

**Requirements:**
- Python 3.9
- Pip

1. Install Python dependencies:
    ```sh
    pip install -r ./requirements/requirements.txt
    ```

2. Study the command options:
    ```sh
    python DeepTumour.py --help
    ```

3. Run DeepTumour:
    ```sh
    python DeepTumour.py [OPTIONS]
    ```


## Appendix

### [About the DeepTumour Algorithm](/docs/about.md)

### [Frequently Asked Questions](/docs/faq.md)

### Publications

> - Jiao, W., Atwal, G., Polak, P. et al. A deep learning system accurately classifies primary and metastatic cancers using passenger mutation patterns. _Nat Commun_ **11**, 728 (2020). https://doi.org/10.1038/s41467-019-13825-8
> - Lincoln David Stein, Wei Jiao, Gurnit Atwal, Quaid Morris; Abstract 5046: DeepTumour: Identify tumor origin from whole genome sequences. _Cancer Res_ 15 June 2022; **82** (12_Supplement): 5046. https://doi.org/10.1158/1538-7445.AM2022-5046
