def append_instructions(prompt):
    instructions = """\nYour answer will have 4 sections seperated by a ";".
Section 1 - a one number response of either "1" if it is dissinformation or "0" if it is factual.
Section 2 - a level from 1-12 on how confident you are that your answer from Section 1 is correct.
Section 3 - a level from 1-12 on how truthful the twitter post is.
Section 4 - An explanation of why the post is fact or fake and why you gave the confidence level you did.
Here is the twitter post:"""
    fixed_prompt = str(prompt) + instructions
    return fixed_prompt