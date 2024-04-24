import csv
import datetime
import json
import requests

API_ENDPOINT = 'https://ogqu3gaykqgcydt43moibcjmfq0jgnxv.lambda-url.us-west-1.on.aws/'

def create_transaction_object(patient_bank, patient_card_number, charge_amount, patient_card_security_code):
    return {
        'bank': patient_bank,
        'merchant_name': 'Okefenokee Rural Healthcare',
        'merchant_token': 'okefenokee1token',
        'cc_num': patient_card_number,
        'card_type': 'Credit',
        'security_code': patient_card_security_code,
        'amount': charge_amount,
        'card_zip': '12345',
        'timestamp': str(datetime.datetime.now())
    }

def send_request_and_log(transaction):
    response = requests.post(API_ENDPOINT, json=transaction)
    log_message = f"Timestamp: {transaction['timestamp']}, Response: {response.text}\n"
    with open('healthcare_transactions_log.txt', 'a') as log_file:
        log_file.write(log_message)

def process_healthcare_transactions(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            patient_bank = row['patient_bank']
            patient_card_number = row['patient_card_number']
            charge_amount = row['charge_amount']
            patient_card_security_code = row['patient_card_security_code']
            
            # Create transaction object with the necessary details
            transaction = create_transaction_object(patient_bank, patient_card_number, charge_amount, patient_card_security_code)
            
            # Send the transaction to the API and log the response
            send_request_and_log(transaction)

process_healthcare_transactions('healthcare_transactions.csv')

