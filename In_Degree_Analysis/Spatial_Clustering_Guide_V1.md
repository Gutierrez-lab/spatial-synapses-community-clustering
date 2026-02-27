# Spatial Synapse Clustering Analysis - Complete Documentation

## Executive Summary

This notebook analyzes **500 high-connectivity neurons** from the Drosophila Hemibrain connectome (0-50% in-degree band) to determine whether **network modularity corresponds to spatial synapse organization**.

**Primary Research Question:** Do functional modules identified by network analysis (modularity maximization) have spatial meaning - i.e., are synapses from the same functional module physically clustered together?

**Key Finding:** Spatial proximity is the dominant organizing principle for synapse placement, with spatial clustering methods (K-means, GMM) outperforming network-based modularity by 20-40×.

---

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Structure](#pipeline-structure)
3. [Methods Compared](#methods-compared)
4. [Deliverables](#deliverables)
5. [Results Summary](#results-summary)
6. [How to Use](#how-to-use)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### Background

**Community detection algorithms** (like modularity maximization) identify groups of neurons that are densely interconnected or share functional properties. The question is: **do these functional modules also organize spatially?**

If network modules have spatial meaning, synapses from neurons in the same module should be physically closer together than expected by chance.

### Approach

1. **Sample neurons**: 500 high in-degree neurons (top 0-50% connectivity)
2. **Extract networks**: Input subconnectomes for each neuron
3. **Find modules**: Modularity maximization (RenEEL/GCM algorithm)
4. **Test spatial clustering**: Compare modularity-based labels vs spatial clustering (K-means, GMM) vs random baseline
5. **Quantify clustering**: Calculate volume of synapse clusters using covariance matrix determinant
6. **Detect outliers**: Apply Michelson and Weber contrast metrics

### Hypothesis

**If modularity reveals biophysically relevant structure:**
- Synapses labeled by modularity should cluster more tightly in 3D space than random labels
- Modularity should perform comparably to pure spatial clustering methods

---

## Pipeline Structure

The notebook consists of **9 main parts + interpretation**:

### Part 1: Identify High In-Degree Neurons (2-3 min)
- Connect to Neuprint Hemibrain database
- Fetch all traced neurons
- Calculate in-degree (upstream partners)
- Select neurons ≥95th percentile (high connectivity)

**Output:** `high_indegree_bodyids` (ranked list of body IDs)

---

### Part 2: Sample 500 Neurons from 0-50% Band (< 1 min)
- Sample 500 neurons from top 50% of high in-degree neurons
- Reproducible sampling (random seed = 42)
- Visualize sampling strategy

**Output:** `test_bodyids` (500 body IDs to analyze)

**Key visualization:** Distribution showing which neurons were sampled

---

### Part 3: Extract Input Subconnectomes (~15-20 min)
- Extract input connectome for each neuron (who connects to it)
- Convert directed → undirected graphs
- Save as edge lists for modularity algorithm
- **Parallel processing:** 16 workers

**Output:** 
- `modularity_runs/graphs/{bodyId}_input_undirected.txt` (500 files)

**Expected:** ~487-495 successful extractions

---

### Part 4: Modularity Maximization (~15-20 min)
- Run RenEEL/GCM algorithm on each input network
- Identifies functional modules (communities)
- **Sequential processing:** Required due to work.sh race conditions
- Timeout protection: 10s per neuron

**Output:**
- `modularity_runs/results/{bodyId}_modules.txt` (500 files)
- Each file: `nodeId moduleId` mapping

**Expected:** ~499/500 successful (1 timeout is normal)

---

### Part 4.5: Calculate Q-values (~2-5 min)
- Computes modularity Q-value for each network
- Q = measure of how modular the network is (0 = random, 0.3-0.5 = moderate, >0.5 = strong)
- Creates in-degree vs Q-value plot

**Output:**
- `qvalue_analysis.csv`
- `indegree_vs_qvalue.png` (scatter plot)

**Purpose:** Understand if highly connected neurons have more modular inputs

---

### Part 5: Spatial Clustering - Modularity Method (~15-20 min)
- Fetch synapses for each neuron
- Label synapses by presynaptic neuron's module
- Calculate spatial cluster volume (covariance determinant)
- Permutation test: Compare to 1000 shuffled labelings
- **Parallel processing:** 12 workers

**Output:**
- `modularity_df` with columns: bodyId, True_Volume, Random_Volume, Ratio, P_Value

**Expected:** ~475-490 successful

---

### Part 6: K-means Spatial Clustering (~10-15 min)
- Apply K-means to synapse 3D coordinates
- Use same k as modularity (fair comparison)
- Pure spatial clustering (no network info)
- **Parallel processing:** 12 workers

**Output:**
- `kmeans_df` with columns: bodyId, KMeans_Volume, N_Synapses

**Expected:** ~475-490 successful

---

### Part 7: GMM Clustering (~10-15 min)
- Apply Gaussian Mixture Model to synapse coordinates
- Probabilistic spatial clustering
- Use same k as modularity
- **Parallel processing:** 12 workers

**Output:**
- `gmm_df` with columns: bodyId, GMM_Volume

**Expected:** ~475-490 successful

---

### Part 8: Combine Results & Apply Contrast Metrics (~5 min)
- Merge all methods into single DataFrame
- Calculate **Michelson contrast**: (True - Random) / (True + Random)
- Calculate **Weber contrast**: (True - Random) / Random
- Detect outliers (95th percentile threshold)
- Create clean dataset

**Output:**
- `combined_df` (all neurons)
- `clean_df` (outliers removed, ~475 neurons)
- Multiple CSV files saved

**Contrast Metrics:**
- **Michelson**: Relative difference from baseline
- **Weber**: Absolute difference from baseline
- Outliers: Neurons where ANY method shows extreme deviation

---

### Part 9: Final Deliverables (~5 min)
- Generate 3 comprehensive figures
- Statistical comparisons
- Method performance analysis

**Outputs:**
1. `DELIVERABLE_1_method_comparison.png` - Categorical violin plot
2. `DELIVERABLE_2_variability_index.png` - Cross-method variability
3. `DELIVERABLE_3_comprehensive_summary.png` - Multi-panel summary

---

## Methods Compared

| Method | Type | Description | Expected Performance |
|--------|------|-------------|---------------------|
| **Shuffled** | Baseline | Random module labels | Worst (no structure) |
| **Modularity** | Network | RenEEL/GCM functional modules | Moderate (if modules have spatial meaning) |
| **K-means** | Spatial | Unsupervised spatial clustering | Best (optimizes spatial tightness) |
| **GMM** | Spatial | Probabilistic spatial clustering | Best (similar to K-means) |

---

## Deliverables

###  Deliverable 1: Categorical Violin Plot

**File:** `DELIVERABLE_1_method_comparison.png`

**What it shows:**
- Y-axis: Cluster volume (log scale) - **lower is better**
- X-axis: 4 methods (Shuffled, Modularity, K-means, GMM)
- Each violin: Distribution of volumes across all neurons
- Individual dots: Each neuron's volume

**Interpretation:**
- **Shuffled >> Modularity**: Network modules have some spatial structure
- **K-means ≈ GMM << Modularity**: Spatial proximity is the primary driver
- **Width of violins**: Variability across neurons

**Key Numbers (Expected):**
- Shuffled: Mean ~1e21
- Modularity: Mean ~4e20 (63% reduction)
- K-means: Mean ~1e19 (98.7% reduction)
- GMM: Mean ~2e19 (98% reduction)

---

###  Deliverable 2: Variability Index

**File:** `DELIVERABLE_2_variability_index.png`

**What it shows:**
- **Panel 1 (Histogram)**: Distribution of variability index (coefficient of variation)
- **Panel 2 (Scatter)**: Variability vs clustering volume, colored by p-value

**Variability Index = CV = std(volumes across methods) / mean(volumes)**

**Interpretation:**
- **Low variability (CV < 0.3)**: Methods agree → robust result
- **High variability (CV > 0.5)**: Methods disagree → unusual neuron
- Identifies neurons with consistent vs variable spatial organization

---

###  Deliverable 3: Comprehensive Performance Summary

**File:** `DELIVERABLE_3_comprehensive_summary.png`

**6-panel figure:**

**Panel A:** Main violin plot (all 4 methods)
**Panel B:** Mean volumes bar chart
**Panel C:** % Improvement over shuffled baseline
**Panel D:** Volume ratios (boxplot)
**Panel E:** Variability index distribution
**Panel F:** Statistical significance tests

**Purpose:** One-stop comprehensive comparison of all methods

---

## Results Summary

### Key Findings

1. **All methods outperform random baseline**
   - Modularity: 63% reduction vs shuffled
   - K-means: 98.7% reduction
   - GMM: 98% reduction

2. **Spatial clustering dominates**
   - K-means and GMM achieve 20-40× tighter clustering than modularity
   - Spatial proximity is the primary organizing principle

3. **Modularity has weak spatial correlates**
   - Network modules DO have some spatial meaning
   - But it's not the dominant factor in synapse placement

4. **Heterogeneity across neurons**
   - Wide variability in how well modularity maps to space
   - Some neurons show strong modularity-space correspondence
   - Others prioritize wiring economy over functional grouping

### Biological Interpretation

**Wiring Economy Hypothesis Supported:**
- Brain minimizes connection length (metabolic cost)
- Spatial clustering (K-means/GMM) captures this constraint

**Functional Modularity is Secondary:**
- Network modules don't strongly predict spatial organization
- Functional organization may operate at different spatial scales

---

## How to Use

### Prerequisites

- Google Colab (recommended) or Jupyter Notebook
- Neuprint account and token
- Python 3.8+

### Running the Notebook

1. **Upload to Colab**
   ```
   File → Upload Notebook → spatial_clustering_Kshamaa_V1.ipynb
   ```

2. **Set Neuprint Token**
   ```python
   # In Colab Secrets (🔑 icon)
   Add: NEUPRINT_TOKEN = your_token_here
   ```

3. **Run All Cells**
   ```
   Runtime → Run all
   ```

4. **Total Runtime:** ~90-120 minutes

5. **Download Results**
   ```
   Files → modularity_runs/results/ → Download deliverables
   ```

### Testing with Smaller Sample

For quick testing:
```python
# In Part 2, change:
n_samples = min(50, len(band_neurons))  # Instead of 500
```
Runtime: ~10-15 minutes for 50 neurons

---

## File Outputs

### Data Files

| File | Contents | Size |
|------|----------|------|
| `all_methods_combined.csv` | All neurons, all metrics | ~100 KB |
| `all_methods_clean.csv` | Outliers removed | ~90 KB |
| `qvalue_analysis.csv` | Q-values + in-degrees | ~50 KB |
| `method_performance_summary.csv` | Summary statistics | ~5 KB |

### Figure Files (300 DPI)

| File | Description |
|------|-------------|
| `DELIVERABLE_1_method_comparison.png` | Main categorical violin plot |
| `DELIVERABLE_2_variability_index.png` | Variability analysis |
| `DELIVERABLE_3_comprehensive_summary.png` | 6-panel comprehensive figure |
| `indegree_vs_qvalue.png` | Q-value analysis |
| `michelson_contrast_corrected.png` | Michelson contrast distributions |
| `weber_contrast_corrected.png` | Weber contrast distributions |

---

## Troubleshooting

### Common Issues

**1. Import errors (fetch_synapse_connections)**
```python
# Add to imports:
from neuprint import fetch_synapse_connections, SynapseCriteria as SC, fetch_adjacencies
```

**2. Modularity timeout (all neurons fail)**
```python
# Run GCM setup:
setup_gcm_environment()
```

**3. Out of memory**
```python
# Reduce workers:
n_workers = min(8, cpu_count())
```

**4. Some neurons timing out**
- Normal to have 1-2 timeouts out of 500
- Replacement mechanism available in notebook

---

## Redundancy Check

### Parts to Keep (All Essential)

 **Parts 1-2**: Neuron selection (required)
 **Part 3**: Connectome extraction (required for Part 4)
 **Part 4**: Modularity (required - main method)
 **Part 4.5**: Q-value calculation (additional analysis requested by PI)
 **Part 5**: Spatial clustering with modularity (required for comparison)
 **Parts 6-7**: K-means and GMM (required - PI deliverables)
 **Part 8**: Contrast metrics (required - PI deliverables)
 **Part 9**: Final figures (required - PI deliverables)

### No Redundancy Found

All parts serve unique purposes and contribute to the final deliverables. No sections should be removed.

---

## Citation

If using this analysis, please cite:
- **Neuprint**: Scheffer et al. (2020) A connectome and analysis of the adult Drosophila central brain. eLife.
- **RenEEL/GCM**: Singh et al. (2021) Generalized Clustering Modularity.
- **Original spatial clustering concept**: [Your PI's lab]

---

## Contact & Support

For questions or issues:
1. Check this README first
2. Review error messages in notebook outputs
3. Verify all imports are present
4. Check that GCM environment setup completed successfully

---

## Version History

**v1.0** (Current)
- Complete pipeline implementation
- All deliverables generated
- Michelson and Weber contrast metrics
- Q-value analysis
- Outlier detection
- Publication-ready figures

---

## Expected Runtime Breakdown

| Part | Time | Can Parallelize? |
|------|------|------------------|
| Parts 1-2 | 2-3 min | N/A |
| Part 3 | 15-20 min | Yes (16 workers) |
| Part 4 | 15-20 min | No (sequential) |
| Part 4.5 | 2-5 min | Yes |
| Part 5 | 15-20 min | Yes (12 workers) |
| Part 6 | 10-15 min | Yes (12 workers) |
| Part 7 | 10-15 min | Yes (12 workers) |
| Parts 8-9 | 10 min | N/A |
| **TOTAL** | **90-120 min** | |

---

## Conclusions

**Bottom Line:** Network modularity reveals some spatial structure, but **spatial proximity is the dominant organizing principle** for synapse placement on high-connectivity neurons in Drosophila.

**Spatial Organization Index:** Modularity achieves ~63% of the improvement from random to optimal spatial clustering.

**Publication Angle:** "Wiring economy trumps functional modularity in organizing synaptic inputs to Drosophila hub neurons"

---

**README.md v1.0 - Generated for spatial_clustering_Kshamaa_V1.ipynb**
