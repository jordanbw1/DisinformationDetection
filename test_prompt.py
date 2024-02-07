import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel(
    model_name='gemini-pro')

prompt = """
    Tell me if the following twitter post is factual or dissinformation. Your answer will have 4 sections seperated by a ";". 
    Section 1 - a one word response of either "0" if it is factual or "1" if it is dissinformation. 
    Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct. Be Honest with you answer.
    Section 3 - a level from 1-12 on how truthful the twitter post is. (1 being dissinformation and 12 being truthful). Be Honest with you answer.
    Section 4 - A explanation of why the post is fact or fake and why you gave the confidence level you did. Here is the twitter post: Suzanne Bonamici supports a plan that will cut choice for Medicare Advantage seniors.
"""

completion = model.generate_content(
    prompt,
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
    ]
)

print(completion.text)

"""
        {
            "category": "HARM_CATEGORY_DEROGATORY",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_TOXICITY",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_VIOLENCE",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUAL",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_MEDICAL",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
"""