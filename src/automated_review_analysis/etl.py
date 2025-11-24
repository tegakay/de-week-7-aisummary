from typing import Dict
import pandas as pd
import numpy as np
import logging
from pathlib import Path

from src.automated_review_analysis.utils import get_workbook, batch_update,send_to_groq, summarize_to_groq,protect_sheet,is_sheet_protected
from src.automated_review_analysis.viz import plot_sentiment_distribution




workbook = get_workbook()
# batch_update = batch_update()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="ETL INFO: %(message)s")

logging.info("ETL module for e-commerce review analysis initialized.")

class EcommerceETL:
    def __init__(self,file:str):
        self.file = file
    
    def extract(self, file) -> pd.DataFrame:
        """Extract data from a CSV file."""
        if file is None or not Path(file).is_file():
            file = self.file
        try:
            df = pd.read_csv(self.file)
            logging.info(f"Data extracted successfully from {self.file}")
            return df
        except Exception as e:
            logging.error(f"Error extracting data: {e}")
            raise
    
    def splice_data(self, file:pd.DataFrame, num_samples: int = 200) -> pd.DataFrame:
        """Sample a subset of the data."""
        df = file[:num_samples]
        return df
    
    def load_to_gsheet(self, df: pd.DataFrame,  worksheet_name: str = "raw_data", protect: bool = False, add_staging: bool = False) -> None:
        if df is None or df.empty:
            logging.error("DataFrame is empty. Cannot load to Google Sheets.")
            return
        try:
            logging.info(f"attempting to load data to gsheet...{worksheet_name}")
            num_rows, num_cols = df.shape
            # Check if worksheet exists, if not create it
            worksheet_list = map(lambda x: x.title, workbook.worksheets())
            if worksheet_name in worksheet_list:
                logger.info('Sheet exists. Using existing worksheet.')
                sheet = workbook.worksheet(worksheet_name)
            else:
                logger.info('Sheet does not exist. Creating new worksheet.')
                workbook.add_worksheet(title=worksheet_name, rows=str(num_rows + 1), cols=str(num_cols))
                if add_staging:
                    workbook.add_worksheet(title="staging", rows=str(num_rows + 1), cols=str(num_cols))
                sheet = workbook.worksheet(worksheet_name)
            
            self.update_gsheet(sheet, df,protect=protect)

        except Exception as e:
            logging.error(f"Error getting DataFrame shape: {e}")
            return
    
    def update_gsheet(self, sheet, df: pd.DataFrame, protect: bool = False ) -> None:
        """Update Google Sheet with DataFrame data."""
        if df is None or df.empty:
            logging.error("DataFrame is empty. Cannot update Google Sheets.")
            return
        # sheet_props = sheet.__dict__['_properties']
        is_protected = is_sheet_protected(sheet,workbook)
        if is_protected:
            logging.info(f"Worksheet {sheet.title} is protected. Skipping update.")
            return
        try:
            df = df.replace([np.inf, -np.inf], np.nan).fillna("")
            data_with_headers = [df.columns.values.tolist()] + df.values.tolist()
            # dt = {"range": "A1",
            #       "values": data_with_headers}
            batch_update(sheet,  data_with_headers)
            #protect sheet after update
            if protect and not is_protected:
                    protect_sheet(sheet)
            
            
        except:
            pass

        
    def get_sheet(self,name: str):
        """Get a worksheet by name."""
        try:
            sheet = workbook.worksheet(name)
            data = sheet.get_all_values()  
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        except Exception as e:
            logging.error(f"Error getting worksheet {name}: {e}")
            raise
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the data in the DataFrame."""
        if df is None or df.empty:
            logging.error("DataFrame is empty. Cannot clean data.")
            return df
        try:
            df = df.drop_duplicates()
            df.rename(columns={df.columns[0]: "Number"}, inplace=True)

            no_cols = ["Recommended IND", "Positive Feedback Count", "Rating", "Age","Positive Feedback Count"]
            # df[no_cols] = df[no_cols].apply(lambda col: pd.to_numeric(col, errors="coerce"))
            # df[no_cols] = df[no_cols].apply(pd.to_numeric, errors='coerce')
            
            return df
        except Exception as e:
            logging.error(f"Error cleaning data: {e}")
            raise
    
    def transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the data in the DataFrame."""
        if df is None or df.empty:
            logging.error("DataFrame is empty. Cannot transform data.")
            return df
        try:
            # df['AI Sentiment'] = df['Review Text'].apply(self.analyze_sentiments) #time.sleep
            # df["AI Summary"] = df['Review Text'].apply(self.summarize_review)
            df[['AI Sentiment', 'AI Summary']] =   df['Review Text'].apply(self.analyze_sentiments).apply(pd.Series)
            # df.loc[:9, ['AI Sentiment', 'AI Summary']] =   df.loc[:9, 'Review Text'].apply(self.analyze_sentiments).apply(pd.Series)
            df["Action Needed?"] = df['AI Summary'].apply(lambda x: 'Yes' if x == 'Negative' else 'No')
            logging.info(f"Data transformation complete.{df.head(12)}"  )
            return df
        except Exception as e:
            logging.error(f"Error transforming data: {e}")
            raise
        
    def analyze_sentiments(self, text: str) -> pd.DataFrame:
        """Analyze sentiments using Groq API."""
        if pd.isna(text) or str(text).strip() == '':
            return ''
        return send_to_groq(text)
    
    def summarize_review(self, text: str) -> pd.DataFrame:
        """Summarize review using Groq API."""
        if pd.isna(text) or str(text).strip() == '':
            return ''
        return summarize_to_groq(text)
        
    def group_sort( self, df:pd.DataFrame, early:bool = False) ->  pd.DataFrame:
        """Group and sort the DataFrame by a specified key."""
        result = df.groupby('Class Name')["AI Sentiment"].count().reset_index(name="count").sort_values("count", ascending=False)
        if early:
            return result
        plot_sentiment_distribution(result, file_name="sentiment_distribution.png")
        return df
    
    def get_sentiment(self, df:pd.DataFrame) -> pd.DataFrame:
        """Get reviews by sentiment."""
        df = df[df["AI Sentiment"].notna()]
        df = df[df["AI Sentiment"].str.strip() != ""]
        for i in df["AI Sentiment"].unique():
            if pd.isna(i) or str(i).strip() == "":
                continue
        try:
            result = df[df["AI Sentiment"] == i]
            df = self.group_sort(result,True)
            plot_sentiment_distribution(df, file_name=f"{i}_sentiment_distribution.png")
        except Exception as e:
            logging.error(f"Error getting sentiment {i}: {e}")
            
            

            
        


