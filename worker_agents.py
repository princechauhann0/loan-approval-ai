from fpdf import FPDF
import requests

DUMMY_DATA = {
    "cust101": {
        "kyc": {
            "name": "Rohan Sharma",
            "phone": "9876543210",
            "age": 28,
            "city": "Mumbai",
            "pannumber": "ABCD1233",
            "currentloan": 0
        },
        "salary": 60000,
        "credit_score": 780,
        "pre_approved_limit": 100000
    },
    "cust102": {
        "kyc": {
            "name": "Priya Singh",
            "phone": "8765432109",
            "age": 29,
            "city": "Delhi",
            "pannumber": "ABCD4353",
            "currentloan": 0
        },
        "salary": 40000,
        "credit_score": 650,
        "pre_approved_limit": 50000
    }
}

FIREBASE_URL = "https://loan-ai-564d3-default-rtdb.firebaseio.com/customers"

def get_from_firebase(customer_id):
    try:
        url = f"{FIREBASE_URL}/{customer_id}.json"
        res = requests.get(url)

        if res.status_code == 200 and res.text != "null":
            data = res.json()
            return {
                "name": data["kyc"]["name"],
                "phone": data["kyc"]["phone"],
                "age": data["kyc"]["age"],
                "city": data["kyc"]["city"],
                "pannumber": data["kyc"]["pannumber"],
                "currentloan": data["kyc"]["currentloan"],
                "salary": data["salary"],
                "credit_score": data["credit_score"],
                "pre_approved_limit": data["pre_approved_limit"],
                "source": "firebase"
            }
    except:
        pass

    return None

def build_from_dummy(c):
    return {
        "name": c["kyc"]["name"],
        "phone": c["kyc"]["phone"],
        "age": c["kyc"]["age"],
        "city": c["kyc"]["city"],
        "pannumber": c["kyc"]["pannumber"],
        "currentloan": c["kyc"]["currentloan"],
        "salary": c["salary"],
        "credit_score": c["credit_score"],
        "pre_approved_limit": c["pre_approved_limit"],
        "source": "dummy"
    }

def verify_customer_details(customer_id: str):

    # 1. Try Firebase first
    fb_data = get_from_firebase(customer_id)
    if fb_data:
        return fb_data

    # 2. Try Dummy DB
    if customer_id in DUMMY_DATA:
        return build_from_dummy(DUMMY_DATA[customer_id])

    # 3. Not found in both
    return None

def perform_underwriting(customer_id: str, loan_amount: int, emi: float):

    # Get CUSTOMER from Firebase or dummy
    customer = verify_customer_details(customer_id)

    if not customer:
        return "REJECTED: Customer not found."

    credit_score = customer["credit_score"]
    pre_limit = customer["pre_approved_limit"]
    salary = customer["salary"]

    # Credit score check
    if credit_score < 700:
        return "REJECTED: Credit score is below 700."

    # Amount vs pre-limit
    if loan_amount > 2 * pre_limit:
        return "REJECTED: Loan amount exceeds 2x the pre-approved limit."

    # Within pre-approved limit
    if loan_amount <= pre_limit:
        return "APPROVED: Loan is within the pre-approved limit."

    # EMI rule for extended limit
    if emi <= 0.5 * salary:
        return "APPROVED: Salary verification passed."

    return "REJECTED: EMI is more than 50% of salary."

def generate_sanction_letter_pdf(customer_name: str, loan_amount: int, tenure: int) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Loan Sanction Letter", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Dear {customer_name},", ln=True)
    pdf.cell(200, 10, txt=f"Your loan of INR {loan_amount} for {tenure} months has been approved.", ln=True)

    file_path = f"Sanction_Letter_{customer_name.replace(' ', '_')}.pdf"
    pdf.output(file_path)

    return file_path
