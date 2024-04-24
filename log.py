import csv
import datetime
import json
import requests
import random

API_ENDPOINT = 'https://ogqu3gaykqgcydt43moibcjmfq0jgnxv.lambda-url.us-west-1.on.aws/'

def create_transaction_object(bank, account_num, amount, card_type):
    # You can modify this to use different values or structures as necessary
    return {
        'bank': bank,
        'merchant_name': 'Fox Books',
        'merchant_token': 'fox1wekrj',
        'cc_num': account_num,
        'card_type': card_type,
        'security_code': '123',  # Assuming a placeholder value
        'amount': amount,
        'card_zip': '12345',  # Assuming a placeholder value
        'timestamp': str(datetime.datetime.now())
    }

def send_request_and_log(transaction):
    response = requests.post(API_ENDPOINT, json=transaction)
    log_message = f"Timestamp: {transaction['timestamp']}, Response: {response.text}\n"
    with open('merchant_log.txt', 'a') as log_file:
        log_file.write(log_message)

def process_file(file_path, card_type):
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            bank = row['BankName']
            account_num = row['AccountNum']
            a = 1.00  # start of your range
            b = 100.00  # end of your range
            random_float = round(random.uniform(a, b), 2)
            amount = random_float
            if card_type == 'Credit':
                # For credit transactions, use 'CreditLimit' and 'CreditUsed' if needed
                pass  # Placeholder for any specific logic for credit transactions
            transaction = create_transaction_object(bank, account_num, amount, card_type)
            send_request_and_log(transaction)

# Process debit transactions from bank.csv
process_file('bank.csv', 'Debit')

# Process credit transactions from ccs.csv
process_file('ccs.csv', 'Credit')
