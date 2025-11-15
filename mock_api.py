# mock_api.py
from flask import Flask, jsonify, request

app = Flask(__name__)

# Dummy database [cite: 33]
DUMMY_DATA = {
    "cust101": {
        "kyc": {"name": "Rohan Sharma", "phone": "9876543210", "address": "Mumbai"},
        "credit_score": 780,
        "pre_approved_limit": 100000,
        "salary": 60000
    },
    "cust102": {
        "kyc": {"name": "Priya Singh", "phone": "8765432109", "address": "Delhi"},
        "credit_score": 650, 
        "pre_approved_limit": 50000,
        "salary": 40000
    }
}

@app.route('/crm/<customer_id>', methods=['GET'])
def get_kyc_details(customer_id):
    """Dummy CRM server to provide KYC details.""" 
    customer_info = DUMMY_DATA.get(customer_id, {})
    return jsonify(customer_info.get("kyc", {}))

@app.route('/credit_bureau/<customer_id>', methods=['GET'])
def get_credit_score(customer_id):
    """Mock credit bureau API to fetch credit scores.""" 
    score = DUMMY_DATA.get(customer_id, {}).get("credit_score", 0)
    return jsonify({"customer_id": customer_id, "credit_score": score})

@app.route('/offer_mart/<customer_id>', methods=['GET'])
def get_pre_approved_limit(customer_id):
    """Mock server hosting pre-approved loan offers.""" 
    limit = DUMMY_DATA.get(customer_id, {}).get("pre_approved_limit", 0)
    return jsonify({"customer_id": customer_id, "pre_approved_limit": limit})

@app.route('/upload_salary_slip', methods=['POST'])
def upload_salary_slip():
    """Simulated salary slip upload."""
    if 'file' in request.files:
        return jsonify({"message": "Salary slip received for validation."}), 200
    return jsonify({"error": "No file part"}), 400

if __name__ == '__main__':
    app.run(port=5000)


