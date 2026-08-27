
# SpaceX Falcon 9 Landing Prediction

End-to-end data science project analyzing SpaceX Falcon 9 launches and predicting whether the first stage lands successfully.

## Business Context

Falcon 9 reusability is a major driver of SpaceX's launch-cost advantage. Predicting first-stage landing success can support launch-cost estimation and competitive bidding decisions for commercial spaceflight providers.

## Project Questions

- Which launch sites and orbital profiles are associated with higher landing success?
- How do payload mass, booster version, and launch history relate to landing outcomes?
- Which classification algorithm performs best for predicting landing success?

## Workflow

1. Collect launch data from the SpaceX REST API.
2. Scrape historical Falcon launch records from Wikipedia.
3. Clean and transform launch and landing outcomes.
4. Explore patterns with Pandas, Matplotlib, Seaborn, and Plotly.
5. Query launch records with SQLite.
6. Visualize launch sites and nearby features with Folium.
7. Train and compare Logistic Regression, SVM, Decision Tree, and KNN models.
8. Explore the results through an interactive Dash dashboard.

## Repository Structure

```text
data/
├── raw/          # Source data collected through web scraping
└── processed/    # Analysis-ready datasets and SQLite database
notebooks/        # Ordered data collection, analysis, SQL, mapping, and ML work
app/              # Dash dashboard
reports/          # Project report and generated figures
src/              # Reserved for reusable production code
tests/            # Reserved for automated tests
```

## Model Results

The notebooks compare four supervised classification algorithms using train/test splitting and cross-validated hyperparameter search. The best recorded cross-validation accuracy was approximately **87.3%**, achieved by the Decision Tree model.

These results are exploratory rather than production benchmarks. The modeling dataset is small, historical, and highly dependent on the feature engineering and split strategy used in the notebook.

## Run Locally

### Option 1: Python venv

Create and activate the project environment:

```powershell
python -m venv .venv
.\<>.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the dashboard from the repository root:

```powershell
python app\spacex_dash_app.py
```

Then open `http://127.0.0.1:8051/` in a browser.

### Option 2: Docker (Recommended)

Build and run with Docker:

```powershell
docker build --tag spacex-project . docker buildx build --tag spacex-project -f Dockerfile
docker run -it -p 8051:8051 spacex-project
```

## Development Tools

| File | Description |
|------|-------------|
| `Dockerfile` | Container configuration for reproducible builds |
| `.dockerignore` | Files to exclude when using Docker |

## Data Sources

- SpaceX API: https://api.spacexdata.com/v4/
- Wikipedia historical Falcon launch records, collected in the web-scraping notebook.
- IBM Skills Network course datasets used for the modeling and SQL exercises.

## Limitations

- The data covers a limited historical period and a relatively small number of launches.
- The raw scraped file contains duplicated and inconsistently formatted records; the SQL workflow uses the normalized `my_data1.db` source.
- Accuracy alone may hide errors in the minority class; precision, recall, F1-score, and confusion matrices should also be considered.
- The dashboard is an analytical prototype and is not intended for operational launch decisions.

## Technologies

Python, Pandas, NumPy, Requests, BeautifulSoup, SQLite, Matplotlib, Seaborn, Plotly, Folium, Scikit-learn, and Dash.

## License and Attribution

This project is an independent portfolio adaptation of the IBM Data Science capstone workflow. External data sources and educational materials remain attributed to their respective owners.
