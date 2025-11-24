import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import logging
import os
from dotenv import load_dotenv
from groq import Groq
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="Utils INFO: %(message)s")

# creds file
data_dir = Path(__file__).parent.parent.parent
file = data_dir/'creds.json'

# logger.info("Google Sheets utility module initialized.")

# Define the scope
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_workbook(sheet_id: str="1PtcHdgyXccBDkJMJ6GLVJLUto241mjPGJJRwLD0ignQ") -> gspread.Spreadsheet:
    """Authenticate and return the Google Sheet object."""

    
    creds = Credentials.from_service_account_file(file, scopes=scopes)
    client = gspread.authorize(creds)

    worksheet = client.open_by_key("1PtcHdgyXccBDkJMJ6GLVJLUto241mjPGJJRwLD0ignQ")
    return worksheet

def batch_update(sheet: gspread.Worksheet,  values: list) -> None:
    """Update a range of cells in the Google Sheet."""
    try:
        # sheet.batch_update(values)
        sheet.update(values)
        # worksheet.update([dataframe.columns.values.tolist()] + dataframe.values.tolist())
        logging.info(f"Successfully updated range.")
    except Exception as e:
        logging.error(f"Error updating range  {e}")
        raise

def protect_sheet(sheet: gspread.Worksheet) -> None:
    """Protect the given worksheet."""
    try:
        sheetId = int(sheet._properties['sheetId'])
        request_body = {
            "requests": [
                {
                    "addProtectedRange": {
                        "protectedRange": {
                            "range": {
                                "sheetId": sheetId,
                            },
                            "warningOnly": True
                        }
                    }
                }
            ]
        }
        worksheet = get_workbook()
        res = worksheet.batch_update(request_body)
        logging.info(f"Worksheet {sheet.title} is now protected.")
    except Exception as e:
        logging.error(f"Error protecting worksheet {sheet.title}: {e}")
        raise

def is_sheet_protected(sheet: gspread.Worksheet,worksheet) -> bool:
    """Check if the given worksheet is protected."""
    try:
        sheet_id = sheet.id
        
        protected_ranges = worksheet.list_protected_ranges(sheet_id)
        logger.info(protected_ranges)

        protection = False

        for pr in protected_ranges:
            if pr["range"]["sheetId"] == sheet_id:
                protection = True
                break
        
        return protection
    except Exception as e:
        logging.error(f"Error checking protection status for worksheet {sheet.title}: {e}")
        raise

#Groq setup
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api_key)

def send_to_groq(prompt: str) -> str:
    """Send a prompt to Groq and return the response."""
    try:
        logging.info(f"Sending prompt to Groq...{prompt}")
        time.sleep(5)  #to avoid rate limits
        chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a market reviewer. For each review provided, return an object that contains the AI Sentiment (Positive, Negative, Neutral) and a one sentence summary of the review titled AI Summary. If unsure about the sentiment, reply with Neutral."},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-20b",
        )
        logging.info(chat_completion.choices[0].message.content)
        return chat_completion.choices[0].message.content   
    except Exception as e:
        logging.error(f"Error communicating with Groq: {e}")
        raise

def summarize_to_groq(prompt: str) -> str:
    """Send a prompt to Groq and return the response."""
    try:
        time.sleep(5)  #to avoid rate limits
        chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an AI assistant. Give a 1 sentence summary of the review provided"},
            {"role": "user", "content": prompt}
        ],
        model="openai/gpt-oss-20b",
        )
        return chat_completion.choices[0].message.content   
    except Exception as e:
        logging.error(f"Error communicating with Groq: {e}")
        raise



print(send_to_groq("This product is great! I loved using it every day."))



