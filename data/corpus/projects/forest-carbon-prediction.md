---
category: projects
---

## Project Overview: Predicting Forest Carbon Stocks

Forests absorb carbon and play a significant role in combating climate change, but quantifying and predicting forest carbon sequestration across countries and time is difficult given how fragmented and multi-sourced the underlying data is. I built a predictive analytics pipeline that estimates forest carbon stocks using climate indicators and per-capita CO2 emissions data, implemented on cloud infrastructure to support distributed data processing and model training. The goal was to integrate three independent datasets—NOAA GSOY, FAO FRA, and Our World in Data—preprocess and join them at scale, then train and evaluate multiple predictive models using Spark MLlib.

## Data Sources and Requirements

The project integrates three key datasets: FAO FRA 2020 for carbon in above-ground and below-ground biomass from 1990 to 2020; NOAA GSOY for station-level annual climate summaries including temperature, precipitation, wind, and degree-days; and Our World in Data for national CO2 emissions per-capita indicators. None of these datasets are included in the repository due to size; they must be downloaded from their respective sources and placed in `nbs/` or `nbs/data/` before running the notebook.

## Cloud Architecture and Local Environment

The project's cloud infrastructure was built on Google Cloud Platform (GCP), using Dataproc for the managed Spark cluster, Cloud Storage (GCS) for dataset staging, and Compute Engine for training instances. I used Docker to package a local development environment running Hadoop HDFS, Spark master/workers, and Jupyter notebooks. This mirrors the cluster architecture, allowing the pipeline to run identically both locally and in the cloud via `docker-compose.yml`. HDFS served as the distributed backend storage layer for Spark computations.

## Pipeline Implementation

### Preprocessing and EDA

The pipeline parses multi-header FAO Excel sheets, matches NOAA weather stations to countries via nearest-centroid geospatial lookup to aggregate climate averages, and filters out aggregate rows from OWID CO2 data. Exploratory data analysis was performed on each cleaned dataset individually before merging all three sources on country and year, summing AGB and BGB into a single `carbon_total` target.

### Training and Visualization

For model training, I used a feature set of average temperature, precipitation, wind, and per-capita CO2 emissions with a 70/30 train-test split. I trained Linear Regression, Random Forest, Gradient Boosted Trees, and K-Means/PCA models via Spark MLlib. All intermediate and final tables are cached to HDFS as Parquet, and model performance metrics are visualized directly in the notebook.

## Cloud Resources and Cost

The cloud environment utilized a single `n1-standard-4` instance with 4 vCPUs, 16 GB of RAM, and a 50 GB persistent disk hosted in the Sydney (`australia-southeast1`) region. The total usage time was 20 hours, resulting in a total monthly cost of $8.49.

## Model Results

Among the tested algorithms, Random Forest was the best performer with an R² of 0.240 and RMSE of 36.45, roughly 2.5 times the baseline R². It identified CO2 per capita as the most important feature at about 39% of split importance, followed by wind and temperature. Gradient Boosted Trees achieved an R² of 0.101 and Linear Regression achieved 0.091. K-Means clustering and PCA explored feature space structure, loosely separating countries by climate and emissions profile.

## Limitations and Underperformance

An R² of 0.24 means the best model explains less than a quarter of the variance in forest carbon stocks. Key reasons include feature-target mismatch, since national climate averages and per-capita CO2 emissions are economic signals rather than direct drivers of forest biomass like deforestation or soil type. Additionally, spatial resolution mismatch washed out local carbon signals, CO2 per capita likely acted as an economic proxy rather than a causal driver, and the sample was a small, noisy set of roughly 190 countries by 5 years.

## Future Work

To improve future iterations, I plan to incorporate satellite-derived vegetation indices like NDVI or higher-resolution land-cover data. Other next steps include adding deforestation and land-use-change features, modeling forest biome types separately instead of pooling all countries into one global regression, and moving from country-year rows to grid-cell rows via sources like NASA GEDI to test whether resolution was the primary limitation.

## Tech Stack

The project relies on Google Cloud Platform including Dataproc, GCS, and Compute Engine, alongside Docker and Hadoop HDFS. For modeling and data manipulation, I used PySpark and Spark MLlib components including `VectorAssembler`, `StandardScaler`, `LinearRegression`, `RandomForestRegressor`, `GBTRegressor`, `KMeans`, and `PCA`, combined with pandas, seaborn, and matplotlib for EDA and visualization.