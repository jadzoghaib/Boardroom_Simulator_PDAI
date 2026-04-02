import pandas as pd
import numpy as np
import os
import subprocess

def download_kaggle_dataset(filepath: str):
    """
    Attempts to download the dataset directly using the Kaggle API.
    Requires 'kaggle' to be installed and your kaggle.json API token configured.
    """
    dataset_name = "dhrubangtalukdar/startup-funding-and-outcome-dataset"
    download_dir = os.path.dirname(filepath)
    os.makedirs(download_dir, exist_ok=True)
    
    print(f"Attempting to download {dataset_name} from Kaggle...")
    try:
        # Run the kaggle CLI command to download and unzip
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d", dataset_name, "-p", download_dir, "--unzip"],
            check=True, text=True, capture_output=True
        )
        print("Download successful!")
        
        # Note: Depending on the zip contents, you may need to rename the extracted CSV 
        # to match 'startup_funding_and_outcome.csv' if it extracts to a different name.
    except FileNotFoundError:
        print("Error: The 'kaggle' CLI tool is not installed. Run 'pip install kaggle'.")
        print("Falling back to generating mock data...")
        generate_mock_kaggle_data(filepath)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download dataset. Ensure you have your kaggle.json configured.")
        print(f"Error details: {e.stderr}")
        print("Falling back to generating mock data...")
        generate_mock_kaggle_data(filepath)

def generate_mock_kaggle_data(filepath: str, num_records: int = 1000):
    """
    Generates a synthetic version of the Kaggle Startup Funding Dataset
    so the project can be run immediately without manual downloading.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    np.random.seed(42)
    sectors = ['Fintech', 'Healthtech', 'SaaS', 'E-commerce', 'AI']
    outcomes = ['IPO', 'Acquisition', 'Failure']
    
    data = {
        'burn_rate': np.random.uniform(10000, 500000, num_records),
        'revenue': np.random.uniform(0, 1000000, num_records),
        'founder_experience': np.random.randint(1, 15, num_records),
        'sector': np.random.choice(sectors, num_records),
    }
    
    df = pd.DataFrame(data)
    
    # Simple logic to make the model learnable
    # Higher revenue + experience - extreme burn rate = Success
    score = (df['revenue'] / 1000) + (df['founder_experience'] * 100) - (df['burn_rate'] / 1000)
    
    # Assign outcomes based on score percentiles
    conditions = [
        score > np.percentile(score, 80),
        score > np.percentile(score, 40),
        score <= np.percentile(score, 40)
    ]
    df['outcome'] = np.select(conditions, ['IPO', 'Acquisition', 'Failure'])
    
    df.to_csv(filepath, index=False)
    print(f"Mock dataset generated at {filepath}")

if __name__ == "__main__":
    download_kaggle_dataset("../../data/startup_funding_and_outcome.csv")
