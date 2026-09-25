---
category: projects
---

## Nutrient Profiles Analysis: Food Group Classification Overview

I built a machine learning pipeline that classifies foods into 23 major food groups using the AUSNUT 2023 taxonomy (AFCD 3 dataset, sheet "All solids & liquids per 100 g") based solely on their nutrient composition and measurements.

The core question of the project was whether major food groups can be accurately recovered from nutrient profiles alone, despite severe class imbalance, high dimensionality, and extensive missingness. The dataset contains 1,588 food items and 268 nutrient fields. After dropping 6 classes with fewer than 15 samples, I worked with 17 classes split via a stratified 80/20 split into 1,235 training and 309 test samples.

My final tuned Gradient Boosted Trees model achieved a **92.6% test accuracy** and **0.88 macro F1** score on the 17-class classification task.

## Exploratory Data Analysis and Feature Insights

Through exploratory data analysis, I uncovered several strong structural patterns in the nutrient data:

* **Moisture Content as a Discriminator:** Moisture content proved to be a powerful single discriminator. Dry and processed foods (fats and oils, snacks, confectionery) cluster near 0g, while fresh and minimally-processed foods (meat, fish, vegetables, dairy) cluster at 64 to 90g.
* **Feature Prevalence and Redundancy:** Out of 268 features, 35 were zero across every category, 53 were non-zero in only 1 to 2 categories, and 128 spanned 6 or more categories. Group-level correlation analysis revealed strong within-group redundancy and a meaningful negative correlation between carbohydrates and fatty acids.
* **Nutrient Exclusivity:** A deep dive into alcohol, caffeine, lactose, and cholesterol showed each acts as a near-perfect signal for a specific category (e.g., alcohol for alcoholic beverages, cholesterol for egg products with a median around 450mg).

## Preprocessing and Handling Missing Data

To tackle high dimensionality and missing values, I implemented a rigorous preprocessing pipeline that reduced the feature space from **288 to 80 features**:

* **Dimensionality Reduction:** Dropped 23 constant features and 165 features with greater than 30% missingness while carefully preserving predictive signal.
* **Transformations and Imputation:** Applied a log1p transform on features with a skew greater than 2.0 (66 features transformed). For remaining nulls, I used EM-based iterative imputation (`IterativeImputer`, max_iter=10) rather than naive mean or median imputation, which was justified by the strong inter-nutrient correlation structure uncovered during EDA.
* **Resampling Pipeline:** To correct severe class imbalance (where raw class counts ranged from 22 to 354), I applied a three-stage training-set-only pipeline using **SMOTE** (for classes below 50 samples), **RandomUnderSampler** (capping classes above 200 samples), and **TomekLinks** (removing borderline synthetic samples at class boundaries), followed by standard scaling and stratified 5-fold cross-validation.

## Modelling Strategy and Performance Results

To evaluate whether the problem was linearly separable or required complex non-linear models, I trained and tuned three distinct models using `RandomizedSearchCV` and Optuna (TPE sampler, 50 trials per model):

* **Logistic Regression:** Served as the linear baseline to test linear separability. It yielded a 0.929 CV balanced accuracy and 0.906 test accuracy (0.836 macro F1).
* **Random Forest:** Tested whether non-linear, feature-interaction-aware methods beat the linear baseline, achieving a 0.920 test accuracy and 0.860 macro F1.
* **Gradient Boosted Trees:** (`HistGradientBoostingClassifier`) Won on every test metric, achieving **0.926 test accuracy** and an **0.882 macro F1** (0.883 test balanced accuracy).

All three models exceeded 90% test accuracy despite the dataset's challenges. Interestingly, Logistic Regression had the best CV score but the worst test score, pointing to mild overfitting on the resampled training distribution. Gradient Boosting concentrated its feature importance heavily on **starch** (2x the next-ranked feature), followed by moisture and sodium, whereas Random Forest spread importance more evenly across roughly 20 features.

## Key Findings and Future Improvements

The project yielded four primary takeaways:

1. **Linear Separability:** The problem is largely linearly separable, as a regularized linear model reached 90.6% accuracy on its own.
2. **Non-Linear Gains:** Non-linear models earn their complexity narrowly, with gains concentrated on nutritionally overlapping categories like Legumes versus Vegetables.
3. **Nutritional Alignment:** Alcohol, cholesterol, moisture, and starch behave as near-exclusive biomarkers that align directly with nutrition science.
4. **Validation Realities:** Confidence intervals overlap across all three models, confirming that test-set performance is a more reliable comparison axis than CV scores.

**Limitations & Next Steps:**
Applying SMOTE and undersampling before cross-validation introduced a minor resampling leakage risk that likely inflated CV estimates. Furthermore, dropping 165 features at a 30% missingness cutoff was conservative. In future iterations, I plan to wrap resampling inside an `imblearn` pipeline, explore dimensionality reduction across correlated nutrient groups, and extend classification to finer-grained 4-digit food categories.