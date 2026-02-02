# High In-Degree Neurons Analysis - Quick Start

## What This Does

The notebook analyzes the Hemibrain connectome to identify neurons with high in-degree (many presynaptic partners) and creates visualizations to help select an appropriate threshold for categorizing neurons as "high" vs "low" in-degree.

**This is Step 1 of the spatial synapse clustering project.**

---

## Quick Start

### Step 1: Get the Neuprint Authentication Token

**To obtain the free Neuprint token:**
1. Go to https://neuprint.janelia.org/
2. Click **"Sign in with Google"** (top right corner)
3. Sign in with a Google account (any Google account works - it's free!)
4. Once logged in, click on the **account icon** (top right)
5. Click **"Account"** from the dropdown menu
6. The **"Auth Token"** will be visible - copy this entire string

### Step 2: Set Up Authentication

**For Google Colab (Recommended - Most Secure):**
1. In Colab, click the **key icon** in the left sidebar ("Secrets")
2. Click **"+ Add new secret"**
3. Name: `NEUPRINT_TOKEN`
4. Value: Paste the token (the long string copied earlier)
5. Toggle the switch to **enable notebook access**

Then in the notebook's authentication cell, use:
```python
from google.colab import userdata
auth_token = userdata.get('NEUPRINT_TOKEN')
```

**For Jupyter/Local (Alternative):**

Option A - Direct paste (quick but less secure):
```python
# In the authentication cell, replace with:
auth_token = 'paste_your_entire_token_here'
```

Option B - Upload file:
```python
# Create flybrain.auth.txt locally with your token, then:
from google.colab import files
uploaded = files.upload()
auth_token = open('flybrain.auth.txt', 'r').read().strip()
```

### Step 3: Run the Notebook

Open `high_indegree_analysis.ipynb` and **run all cells in order** (Runtime > Run all, or Shift+Enter through each cell).

**What happens:**
- Installs `neuprint-python` package
- Connects to Neuprint Hemibrain database
- Fetches 21,739 traced neurons
- Calculates in-degree statistics
- Generates 4-panel histogram visualization
- Creates tables of high in-degree neurons
- Outputs variable `high_indegree_bodyids` for next step

**Runtime:** ~1-2 minutes

---

## What the Analysis Produces

### Visualizations (Displayed Inline)

**4-Panel Histogram:**
1. Zoomed histogram (0-5000 range) - shows distribution structure
2. Distribution by range - categorical breakdown
3. Percentile values - key threshold markers
4. Sample size vs threshold - helps choose cutoff

### Analysis Results

**Key Statistics:**
- Total neurons: 21,739
- Median in-degree: 494
- Mean in-degree: 872
- 95th percentile: 2,838 (recommended threshold)

**High In-Degree Neurons:**
- At 95th percentile (≥2,838): 1,088 neurons (5%)
- Includes major hubs: APL_R, MBONs, DPM, oviIN_R
- Displayed as interactive tables in notebook

### Output Variables

After running the notebook, the following variables are available:
- `high_indegree_bodyids` - **List of neuron IDs for Step 2**
- `high_indegree_neurons` - DataFrame with full neuron data
- `neurons_df` - All traced neurons
- `stats` - Distribution statistics dictionary

---

## Interpreting Results

### The Distribution

**What the histograms show:**
- Highly right-skewed distribution (most neurons have low in-degree)
- Natural break around 2,000 upstream partners
- Top 5% (≥2,838) are clearly distinct "hub" neurons
- Small number of extreme hubs (>10,000 partners)

### Threshold Selection

**Recommended: 95th percentile (2,838 upstream partners)**

**Why this threshold:**
- Statistically rigorous (top 5%)
- Captures ~1,088 neurons (good sample size)
- Includes all major known integrative centers
- Computationally manageable for modularity analysis
- Clear biological separation from bulk population

**Alternative thresholds:**
- 90th percentile (1,766): More neurons (2,174) but less selective
- 99th percentile (6,926): Very selective (217 neurons) but small sample
- Custom (e.g., 3,000): Round number, similar to 95th percentile

### Notable Findings

**Top neuron:** APL_R with 127,151 upstream partners
- Giant GABAergic neuron providing global inhibition to mushroom body

**The oviIN_R neuron:** Ranks #13 with 23,029 upstream partners
- Clearly a major integrative hub in egg-laying circuit

**Dominant types in top 20:**
- MBONs (7) - mushroom body output neurons
- DPM (2) - modulatory feedback neurons
- lLN2F (3) - local processing neurons

---

## Next Steps (Step 2)

After identifying the high in-degree neurons, proceed to modularity maximization:

### For Each Neuron in `high_indegree_bodyids`:

1. **Extract input subconnectome**
   ```python
   # Use code from mesoscale_connectivity.ipynb
   from get_connectome import get_connectome
   subconn = get_connectome(bodyid, exclude_main_neurons=True, connectome_scope='input')
   ```

2. **Convert to undirected graph**
   ```python
   from get_connectome import connectome_to_undirected
   subconn_undirected = connectome_to_undirected(subconn)
   ```

3. **Export for RenEEL**
   ```python
   subconn_undirected.to_csv(f'neuron_{bodyid}.txt', index=False, header=False)
   ```

4. **Run modularity maximization**
   ```python
   from gcm_script import gcm
   gcm(f'neuron_{bodyid}.txt', output_file=f'partition_{bodyid}.txt')
   ```

5. **Analyze spatial synapse clustering**
   - Use code from `spatial_synapse_clustering.ipynb`
   - Calculate covariance of synapse coordinates by module
   - Compare to shuffled labels

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'neuprint'"
**Solution:** Run the first cell that installs neuprint-python:
```python
!pip install neuprint-python
```

### "Authentication failed" or "Invalid token"
**Solutions:**
- Verify the entire token was copied (it's very long)
- Check there are no extra spaces before/after the token
- Make sure the user is signed into neuprint.janelia.org
- Try getting a fresh token (they can expire)

### "No data returned" or empty DataFrame
**Solutions:**
- Check internet connection
- Verify dataset is 'hemibrain:v1.2.1'
- Try the simple test query in the notebook first

### Plots don't display in Colab
**Solution:** Make sure the notebook includes:
```python
%matplotlib inline
```
at the top (already included)

### Out of memory
**Solutions:**
- The analysis fetches 21K neurons - this uses ~200MB RAM
- Close other tabs/notebooks
- Use Colab Pro for more RAM
- Or filter to specific neuron types first

---

## Customization

### Change Threshold
In the final cell, modify:
```python
selected_threshold = int(stats['q95'])  # Change to stats['q90'], 3000, etc.
```

### Filter by Neuron Type
After fetching neurons, add:
```python
neurons_df = neurons_df[neurons_df['type'].isin(['MBON', 'DPM'])]
```

### Adjust Histogram Bins
In the visualization cell:
```python
ax1.hist(indegree_values[mask], bins=100)  # Change bins=100 to desired number
```

### Display More Neurons in Tables
```python
display(display_df.head(50))  # Change 20 to 50
```

---

## Files & Documentation

- **`high_indegree_analysis.ipynb`** - Main notebook (run this)
- **`GUIDE.md`** - Detailed implementation guide
- **`README.md`** - This file

---

## Summary

**Objective:** Identify high in-degree neurons for modularity analysis  
**Method:** Statistical analysis of Hemibrain connectome  
**Output:** List of 1,088 hub neurons (≥2,838 upstream partners)  
**Next:** Extract input subconnectomes and run modularity maximization  
