# [DeepTumour](/README.md)

## About the DeepTumour Algorithm

The DeepTumour algorithm predicts the tissue of origin of a tumour based on the pattern of passenger mutations identified by whole genome sequencing.
"Passengers" are incidental mutations that accrue in the genome over time due to random mutational processes,
and are functionally distinct from the "driver" mutations that are responsible for the cancer's malignant behaviour.
In adult cancers, passenger mutations typically outnumber drivers by a hundred or thousand-fold;
critically, the vast majority of passengers arise in the normal cell lineage that precedes the malignant
transformation event and hence reflects mutational processes existing in the cancer's precursor cell and its ancestors.

Passenger mutations are not uniformly distributed across the genome,
but are concentrated in areas of the genome that have a locally high mutation rate.
Mutation rates are highest at places in the genome where chromatin is tightly packed and less accessible to the DNA repair machinery.
Each distinct cell type has a different pattern of chromatin packing due to epigenetic modifications.
DeepTumour takes advantage of this to infer the chromatin state in the cell of origin from the distribution of passenger mutations in the tumour.

Another characteristic of passenger mutations is that the probability of a particular type of mutation occurring
(e.g. replacement of C by T) depends on the mutational processes that were active in the cell of origin and its ancestors.
For example, the type of mutations seen after UV exposure are distinct from those that accompany chronic cigarette smoking.
Because certain cancers are associated with distinct mutational exposures (e.g. lung cancer and smoking),
DeepTumour uses the tumour's distribution of passenger mutation type as well as position on the genome.

The DeepTumour algorithm itself is a fully connected, feed-forward neural network which we trained using 29 cohorts
representing different tumour types from the [Pan-Cancer Analysis of Whole Genomes](https://www.nature.com/articles/s41586-020-1969-6) project.
When applied to independent sets of tumours, the algorithm is able to achieve an overall accuracy of 88% on primary tumours and 83% on metastatic tumours.
When you upload a VCF file containing somatic mutations, the algorithm assigns a match probability from 0.0 to 1.0 for each of the 29 tumour types
on which it was trained and chooses the tumour type with the highest probability score.
The algorithm also calculates a type of confidence score based on the probability scores' distributione.
A low entropy (< 2.0) is considered a confident score. HIgher values are unreliable (but might be correct).

The 29 tumour types recognized by DeepTumour are listed below.
If you upload a tumour that is not on this list,
you are likely to get a high entropy score and a low maximum match score.

```
Biliary-AdenoCA, Bladder-TCC, Bone-Leiomyo, Bone-Osteosarc, Breast-AdenoCA, CNS-GBM, CNS-Medullo, CNS-Oligo, CNS-PiloAstro, Cervix-SCC, ColoRect-AdenoCA, Eso-AdenoCA, Head-SCC, Kidney-ChRCC, Kidney-RCC, Liver-HCC, Lung-AdenoCA, Lung-SCC, Lymph-BNHL, Lymph-CLL, Myeloid-MPN, Ovary-AdenoCA, Panc-AdenoCA, Panc-Endocrine, Prost-AdenoCA, Skin-Melanoma, Stomach-AdenoCA, Thy-AdenoCA, Uterus-AdenoCA
```

A full description of the DeepTumour algorithm and benchmarking results can be found in
[Jiao et al. A deep learning system accurately classifies primary and metastatic cancers using passenger mutation patterns](https://doi.org/10.1038/s41467-019-13825-8).
