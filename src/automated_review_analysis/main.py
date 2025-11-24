
from src.automated_review_analysis.etl import EcommerceETL
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="Main INFO: %(message)s")

def main():
    #step 1
    ecommerce = EcommerceETL(file=Path(__file__).parent.parent.parent/'reviews.csv')
    file = ecommerce.extract(None)
    spliced_data = ecommerce.splice_data(file, num_samples=200)

    ecommerce.load_to_gsheet(spliced_data, worksheet_name="raw_data",protect=True,add_staging=True)

    #step2
    #get sheet from raw_data
    staging_sheet = ecommerce.get_sheet("raw_data")
    # logger.info("raw sheet data retrieved.")
    print(staging_sheet.head())
    # clean data in raw_data sheet
    cleaned_data = ecommerce.clean_data(staging_sheet)
    #load cleaned data to staging sheet
    ecommerce.load_to_gsheet(cleaned_data, worksheet_name="staging")

    # #step 3 to 6
    # #load to processed sheet
    data_to_process = ecommerce.transform_data(cleaned_data)

    ecommerce.load_to_gsheet(data_to_process, worksheet_name="processed")
    #step 7
    sentiment_class = ecommerce.group_sort(data_to_process)
    #calculate positive, negative, neutral counts
    other_sentiments = ecommerce.get_sentiment( data_to_process)



if __name__ == "__main__":
    main()