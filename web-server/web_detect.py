import csv
import google.generativeai as genai
import os
import uuid
from helper_functions.email_functions import send_email
import pandas as pd
from helper_functions.stats import compute_sheet_stats
from helper_functions.database import execute_sql, sql_results_one


def run_prompt(api_key, prompt, email, base_url, user_id, dataset_info, num_rows=300):
    if num_rows < 1:
        print("Too few rows requested, using the default of 300")
        num_rows = 300
    # Declare main variables
    script_directory = os.path.dirname(os.path.abspath(__file__))
    datasets_directory = os.path.join(script_directory, "static", "datasets")
    in_file = os.path.join(datasets_directory, dataset_info["folder"], dataset_info["filename"])
    uuid_name = str(uuid.uuid4())
    out_csv_file_name = f"{uuid_name}.csv"
    out_xlsx_file_name = f"{uuid_name}.xlsx"
    out_file = os.path.join(script_directory, "dynamic", "prompt_results", out_csv_file_name)
    csv_download_path = base_url + f"download/{out_csv_file_name}"
    xlsx_download_path = base_url + f"download/{out_xlsx_file_name}"
    data = []
    dataset_name = dataset_info["name"]
    subject = dataset_info["subject"]
    i = 0

    # TODO: Write code here to insert a new task into the database.
    # Make sure to insert these values into the database:
    # - user_id : the variable user_id
    # - uuid : the variable uuid_name
    # - status : "RUNNING"
    # For simplicty, use the function execute_sql to insert the values into the database.

    # Configure Gemini API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name='gemini-pro')

    # # Pulls data in from csv file and organizes it in a list of dictionaries
    # with open(in_file, 'r', encoding='utf-8', errors='ignore') as in_csv:
    #     reader = csv.DictReader(in_csv)
    #     in_data = list(reader)
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(in_file, header=0)

    # Skip the first row (headers)
    df = df.iloc[1:]

    # Shuffle the DataFrame
    df = df.sample(frac=1)

    # If the user requests more rows than are in the dataset, limit the number of rows to the number of rows in the dataset
    num_rows_df = len(df)
    if num_rows > num_rows_df:
        num_rows = num_rows_df

    # Grab the first num_rows rows
    random_rows = df.head(num_rows)

    # Establish headers
    headers = [
        "id", "dataset", "text", "subject", "prompt", "label", "response", "confidence_level", "truth_level", "correct", "response_explanation"
    ]

    # Write the header row
    with open(out_file, mode="a", newline="", encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

    # Loops through every row of data in the csv file
    num_iters = 0
    for index, row in random_rows.iterrows():
        print(str(num_iters) + ":")
        try:
            num_iters += 1
            # Add text to current prompt and strips text of any ";"
            full_prompt = prompt + row["text"].replace(";", "")

            # Interact with Gemini to fill out response, response_explanation, confidence, truthful_level, and correct
            res = model.generate_content(
            contents=full_prompt,
            generation_config={
            'temperature': 0,
            'max_output_tokens': 800
            },
            safety_settings=[
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS",
                "threshold": "BLOCK_NONE",
            },
            ])

            # Checks if the prompt was blocked
            if str(res.prompt_feedback).replace("\n", "") == "block_reason: OTHER":
                print(str(i) + ": Prompt Blocked")
                continue

            # Checks for if response is empty
            if res.parts == []:
                print(str(i) + ": Response is empty")
                continue

            #print(res.text)
            res = res.text.split(";")

            # Checks if response is correct length
            if len(res) <= 1:
                print("Prompt did not return correct response")
                continue
            
            # Determines if AI was correct or not
            label = int(row["label"])
            if label == 0:
                if str(label) == str(res[0]):
                    correct = 1
                else:
                    correct = 0
            else:
                if str(label) == str(res[0]):
                    correct = 1
                else:
                    correct = 0

            # Create the new row of data for output csv
            new_list = []
            new_list.append(index) # id
            new_list.append(dataset_name) # dataset
            new_list.append(row["text"]) # text
            new_list.append(subject) # subject
            new_list.append(prompt.replace("\n", "")) # prompt
            new_list.append(row["label"]) # label
            new_list.append(res[0]) # response
            new_list.append(res[1]) # confidence_level
            new_list.append(res[2]) # truth_level
            new_list.append(correct) # correct
            new_list.append(res[3]) # response_explanation

            data.append(new_list)

            if num_iters % 50 == 0:
                with open(out_file, mode="a", newline="", encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerows(data)
                
                # Clear the data list after writing to the CSV file
                data = []

        except Exception as e:
            print(f"(server error) Exception: {str(e)}")
            continue  # Move on to the next iteration


    # Write the data to the out_file csv
    if data:
        with open(out_file, mode="a", newline="", encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerows(data)

    # Create xlsx with stats
    stats = compute_sheet_stats(out_csv_file_name, out_xlsx_file_name)

    # Send CSV file as attachment via email
    send_email(email, csv_download_path, xlsx_download_path, stats, prompt)

    # TODO: Mark as completed in the database
    # Write code here to UPDATE the task in the database.
    # Update the following values
    # - end_time : the current time in UTC. You may need to use the Python datetime library.
    # - status : "COMPLETED"
    # You should update WHERE the "uuid" column in the db is equal to the uuid_name variable.
    # For simplicty, use the function execute_sql to insert the values into the database.

    return