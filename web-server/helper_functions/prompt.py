def get_instructions():
    instructions = """Your response should have these sections:
<answer> - a one number response of either "1" if it is dissinformation or "0" if it is factual.
<confidence_level> - a level from 1-12 on how confident you are that your answer from Section 1 is correct.
<truth_level> - a level from 1-12 on how truthful the twitter post is.
<explanation> - An explanation of why the post is fact or fake and why you gave the confidence level you did.
Your response should be in XML format, with the following structure:
<response>
<SECTION_NAME> <!-- Replace SECTION_NAME with the name of the section. Include your answer for the section within. --> </SECTION_NAME>
<!-- Do this for all sections -->
</response>
Here is the post you should evaluate:"""
    return instructions

def append_instructions(prompt):
    instructions = get_instructions()
    fixed_prompt = str(prompt) + "\n" + instructions
    return fixed_prompt