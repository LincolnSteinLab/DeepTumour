# [DeepTumour](/README.md)

## Frequently Asked Questions

### What is the input format?
For formatting somatic mutation calls, please use
[VCF version 4.3](https://samtools.github.io/hts-specs/VCFv4.3.pdf) or higher.
You are free to use either GRCh37 (hg19) or GRCh38 genome build coordinates.
Other builds are not currently supported.

### What is the entropy score?
The consolidated entropy score is to indicate whether the sample is providing
enough information to make accurate prediction, i.e. good quality sample.
The maximum value of entropy for 29 cancer types is ln(29) =~ 3.367.
Currently, if the entropy score is less than 2.76, the sample is considered to
be a good quality sample.

### How do I know if I can trust DeepTumour's results?
Remember that DeepTumour is intended for research only and not for diagnosis.
Entropy scores give a rough idea of how trustworthy a particular tumour type
call is, but even "good" scores below the threshold of 2 do not guarantee correctness.

### DeepTumour produced a surprising result. What do I do now?
DeepTumour will not correctly classify a tumour that was absent from its training set.
Even for tumour types that it was trained on, it will still misclassify the tumour between 1 and 10% of the time,
depending on the tumour's true type
(see the [DeepTumour paper](https://www.nature.com/articles/s41467-019-13825-8#Abs1) for details).
It is also possible that the tumour's origin was misdiagnosed or suffered a technical artifact such as a sample swap.
Use your best judgment when tracking down the likely source of a discrepancy.

### I am studying tumour type X but DeepTumour doesn't support it. How do I get you to add this type?
We would very much like to increase the range of tumour types recognized by the algorithm.
If you have access to a cohort of at least 20 tumours of a new type and whole genome sequencing data,
we would be delighted to work with you to add this to the DeepTumour training set.

### How do I cite this?
Please cite the following publication: https://doi.org/10.1038/s41467-019-13825-8
```
Jiao, W., Atwal, G., Polak, P., Karlic, R., Cuppen, E., PCAWG Tumor Subtypes and Clinical Translation Working Group, Danyi, A., de Ridder, J., van Herpen, C., Lolkema, M. P., Steeghs, N., Getz, G., Morris, Q., Stein, L. D. & PCAWG Consortium. A deep learning system accurately classifies primary and metastatic cancers using passenger mutation patterns. Nat. Commun. 11, 728 (2020).
```

### How do I contact you for help and support?
Please send an email addressed to deeptumour@oicr.on.ca.
