import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

data_dir = Path(__file__).parent.parent.parent /'reports'




def plot_sentiment_distribution(df: pd.DataFrame,file_name:str ) -> None:
    """Plot the distribution of sentiments in the DataFrame."""
    
    plt.figure(figsize=(6,6))
    plt.pie(df["Class Name"], labels=df["AI Sentiment"], autopct="%1.1f%%")
    plt.title("Reviews by Class Name")
    output = data_dir/file_name
    plt.savefig(output)   # Save to file
    plt.close()