# Where the evidence comes from

Wenzhang Du’s PAIRSAFE study appears in the AACL-IJCNLP 2026 long-paper proceedings. The [official paper](https://aclanthology.org/2026.aacl-long.124/) anchors the main claims. The camera-ready manuscript is dated September 22, 2026. The May 2026 submission supplement preserves the underlying scores and original replay code.

## Submission inputs

The release preserves the contents of both submission archives byte-for-byte under shorter directory names. The ZIP containers are identified here by their original SHA-256. Each source directory retains its own manifest or checksum list, copyright notices and license.

| Submission archive | SHA-256 | Public directory |
| --- | --- | --- |
| `2525_PAIRSAFE_Proxy_Resistant__Data.zip` | `19590c1c52e1026049517d5c308bef35fdb8aa8bb5306366838b8d18e1ab16f4` | [data](data/) |
| `2525_PAIRSAFE_Proxy_Resistant__Software.zip` | `f6e38d1e2e39038d886ad0973701371e311e33ed50c3287da0837e0e6ab824ae` | [software](software/) |

The indices describe 150 distinct safe/unsafe XSTest-derived pairs. Each primary model has 300 member records. An independent Qwen robustness cache contributes 300 rows of candidate likelihoods, and 300 Qwen generation rows contain rule decisions and response hashes. All records use the same pair identities. The raw source prompts, generated responses, checkpoints and original inference environment are outside the release. The accompanying [data card](data/DATA_CARD.md) describes the redaction policy.

## From archive to publication

| Evidence | Origin and treatment |
| --- | --- |
| Primary model metrics and gaps, paper Table 2 | Computed from archived member scores. Single- and two-sided likelihood baselines are also checked. |
| Exact-focus subset, categories and four Qwen candidate-margin variants | Computed from pair metadata and archived scores. Archive tables supply the independent numerical expectations. |
| Qwen generation PCGA and component rates | Computed from rule labels for each member, including the complete four-cell joint outcome table. |
| Earlier metadata, matching and uncertainty tables | Preserved as supplied in [data/tables](data/tables/). The source software reads the early metadata table when displaying proxy summaries. |
| Final nested metadata and residualization, paper Table 1 | [Transcribed values](reference/paper-table-1.csv) from the published PDF. The archived scripts and inputs do not supply the final nested run, its fold predictions or all modelled note metadata. |
| Original model inference | The paper identifies the model families and score configurations. The original immutable model revisions, precision/device details, and full command logs were not preserved. The release begins at the archived scores. |

The official XSTest reference is [Röttger et al., 2024](https://aclanthology.org/2024.naacl-long.301/). The model identities are [Qwen2.5-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct) and [SmolLM2-1.7B-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct). Material from those upstream projects remains governed by its upstream terms.

## Rights

The [submission data license](data/LICENSE) grants use, copying and evaluation of the derived files for scholarly review and reproducibility, and asks redistributors to preserve the license and redaction policy. The [submitted software](software/LICENSE) retains its original MIT notice. The [repository MIT license](LICENSE) applies to the new replay, figure and publication software. The publisher hosts the official text and PDF.
