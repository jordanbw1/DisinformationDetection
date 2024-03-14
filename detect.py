import csv
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Declare main variables
#in_file = "./Datasets/ISOT_Dataset/Fake.csv"
#in_file = "./Datasets/ISOT_Dataset/True.csv"
#in_file = "./Datasets/Liar/Liar_Test.csv"
#in_file = "./Datasets/WELFake/WELFake_Dataset.csv"
#in_file = "./Datasets/Fake_or_Real/fake_or_real_news.csv"
#in_file = "./Datasets/Russian_info/RussianPropagandaSubset.csv"
#in_file = "./Datasets/example_data.csv"
#out_file = "./results.csv"
script_directory = os.path.dirname(os.path.abspath(__file__))
in_file = os.path.join(script_directory, "Datasets\\WELFake\\WELFake_Dataset_5000.csv")
out_file = os.path.join(script_directory, "results.csv")
data = []
dataset_name = "WELFake Dataset"
subject = "US_politics"
prompts = [
"""
    Tell me if the following twitter post is factual or dissinformation. Your answer will have 4 sections seperated by a ";". 
    Section 1 - a one number response of either "1" if it is factual or "0" if it is dissinformation. 
    Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct.
    Section 3 - a level from 1-12 on how truthful the twitter post is. 
    Section 4 - A explanation of why the post is fact or fake and why you gave the confidence level you did. Here is the twitter post: 
""",
"""
    Tell me if the following dissinformation twitter post is indeed dissinformation or if it is actually factual. Your answer will have 4 sections seperated by a ";". 
    Section 1 - a one number response of either "1" if it is factual or "0" if it is dissinformation. 
    Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct.
    Section 3 - a level from 1-12 on how truthful the twitter post is. 
    Section 4 - A explanation of why the post is fact or fake and why you gave the confidence level you did. Here is the twitter post: 
""",
"""
    Tell me if the following factual twitter post is indeed factual or actually dissinformation. Your answer will have 4 sections seperated by a ";". 
    Section 1 - a one number response of either "1" if it is factual or "0" if it is dissinformation. 
    Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct.
    Section 3 - a level from 1-12 on how truthful the twitter post is. 
    Section 4 - A explanation of why the post is fact or fake and why you gave the confidence level you did. Here is the twitter post: 
"""
]
i = 0


# Configure Gemini API
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel(model_name='gemini-pro')

# Pulls data in from csv file and organizes it in a list of dictionaries
if in_file == "./example_data.csv":
    with open(in_file, 'r') as in_csv: # For Example Dataset (not utf-8)
        reader = csv.DictReader(in_csv)
        in_data = list(reader)
else:
    with open(in_file, 'r', encoding='utf-8', errors='ignore') as in_csv: # For all datasets encoded in utf-8
        reader = csv.DictReader(in_csv)
        in_data = list(reader)

# Establish headers
headers = [
    "id", "dataset", "text", "subject", "prompt id", "prompt", "label", "response", "confidence_level", "truth_level", "correct", "response_explanation"
]

# Write the header row
with open(out_file, mode="a", newline="", encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(headers)

# Loops through every row of data in the csv file
for current in in_data:
    i += 1
    j = 1
    print(str(i) + ":")

    try:

        # For testing purposes
        """
        if i < 8749:
            continue
        """
        if i > 5:
            break
        

        # Loops through every prompt in the prompts list
        for current_prompt in prompts:
            j += 1

            # Add text to current prompt and strips text of any ";"
            full_prompt = current_prompt + current["text"].replace(";", "")

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
            
            # Determines if PaLM 2 was correct or not
            if current["label"] == res[0]:
                correct = 1
            else:
                correct = 0

            # Create the new row of data for output csv
            new_list = []
            new_list.append(i) # id
            new_list.append(dataset_name) # dataset
            new_list.append(current["text"]) # text
            new_list.append(subject) # subject
            new_list.append(j) # prompt id
            new_list.append(current_prompt.replace("\n", "")) # prompt
            new_list.append(current["label"]) # label
            new_list.append(res[0]) # response
            new_list.append(res[1]) # confidence_level
            new_list.append(res[2]) # truth_level
            new_list.append(correct) # correct
            new_list.append(res[3]) # response_explanation

            data.append(new_list)

            if i % 50 == 0:
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