import os
import uvicorn
from openai import OpenAI
from fastapi import FastAPI
from pydantic import BaseModel

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


app = FastAPI()

class InputData(BaseModel):
    chiro_text:str

billing_code_context = """
Patient Exam Codes:
New Patients:
- 99202: First 15 minutes
- 99203: 16-30 minutes (industry standard)
- 99204: 31 minutes or longer

Established Patients:
- 99212: 15 minute exam
- 99213: 16-30 minutes
- 99214: 31 minutes or longer

Chiropractic Adjustment Codes:
- 98940: Spinal regions 1-2 (neck, upper back)
- 98941: Spinal regions 3-4 (lower back, sacrum, tailbone)
- 98943: Extremities (shoulders, arms, hands, hips, legs, ankles, feet, jaw, ribs)

Procedure/Exercise Codes:
- 97110: Exercise done in office or sent home for strengthening
- 97112: Rehabilitation exercises (head weights, wobble cushions, stability)
- 97140: Manual Therapy (massage, scar tissue, trigger point therapy, pin and stretch, massage gun)
- 97012: Traction

Choose codes based on:
1. Patient type (new/established) and exam duration
2. Adjusted spinal regions
3. Any extremity adjustments
4. Specific procedures or exercises performed
"""

billing_code_descriptions = {
    "99202": "Evaluation and Management, Initial Visit",
    "99203": "Evaluation and Management, Initial Visit",
    "99204": "Evaluation and Management, Initial Visit",
    "99212": "Evaluation and Management, Established Patient",
    "99213": "Evaluation and Management, Established Patient",
    "99214": "Evaluation and Management, Established Patient",
    "98940": "Chiropractic manipulative treatment (CMT). Spinal, 1-2 regions",
    "98941": "Chiropractic manipulative treatment (CMT). Spinal, 3-4 regions",
    "98942": "Chiropractic manipulative treatment (CMT). Spinal, 5 regions",
    "98943": "Chiropractic manipulative treatment (CMT). Extraspinal, 1 or more regions",
    "97110": "Therapeutic Exercise",
    "97112": "Neuromuscular Re-education",
    "97140": "Manual Therapy",
    "97012": "Mechanical Traction"
}

icd_context = """
ICD Code Mapping:
neck: M99.01
upper back: M99.02
mid back: M99.02
lower back: M99.03
sacrum: M99.04
tail bone: M99.04
pelvis: M99.05
hips: M99.05
lower extremity: M99.06
upper extremity: M99.07
ribs: M99.08
headache: M99.00
"""

icd_code_descriptions = {
    "M99.00": "Segmental and somatic dysfunction of head region",
    "M99.01": "Segmental and somatic dysfunction of cervical region",
    "M99.02": "Segmental and somatic dysfunction of thoracic region",
    "M99.03": "Segmental and somatic dysfunction of lumbar region",
    "M99.04": "Segmental and somatic dysfunction of sacral region",
    "M99.05": "Segmental and somatic dysfunction of pelvic region",
    "M99.06": "Segmental and somatic dysfunction of lower extremity",
    "M99.07": "Segmental and somatic dysfunction of upper extremity",
    "M99.08": "Segmental and somatic dysfunction of rib cage",
    "M99.09": "Segmental and somatic dysfunction of abdomen and other regions"
}

def billing_codes(text, billing_code_context):
    response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": f"You are an assistant specialized in providing billing codes. Given a context and user input text, you will output only the relevant billing codes without any additional explanatory text."},
        {"role": "user", "content": f"context:{billing_code_context}, user_input:{text}"}
    ]
    )
    billing_codes = response.choices[0].message.content
    return billing_codes

def icd_codes(text, icd_context):
    response_i = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": f"You are an expert in suggesting ICD Codes from the given context based on the examination details. Your response should contain only the ICD Codes listed in the context that are relevant to the examination details. Provide only the codes without any additional text."},
        {"role": "user", "content": f"context:{icd_context}, Examination details:{text}"}
    ]
    )
    icd_codes = response_i.choices[0].message.content
    return icd_codes

def format_codes(codes, descriptions):
    formatted_codes = []
    for code in codes.split():
        code = code.strip().strip(',')
        if code in descriptions:
            formatted_codes.append(f"{code} - {descriptions[code]}")
    return "\n".join(formatted_codes)

       

@app.post("/billing_and_icd_codes")
def code_generator(data: InputData):
    billing_code_result = billing_codes(data.chiro_text, billing_code_context)
    bcs = format_codes(billing_code_result, billing_code_descriptions)
    icd_code_result = icd_codes(data.chiro_text, icd_context)
    ics = format_codes(icd_code_result, icd_code_descriptions)
    return {"billing_codes_": bcs, "icd_codes_": ics}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
