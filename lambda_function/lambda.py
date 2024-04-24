import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import hashlib
from datetime import datetime
import random 

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):

    if 'body' in event and event['body'] is not None:
        body = json.loads(event['body'])
        bank = body.get('bank')
        merchant_name = body.get('merchant_name')
        merchant_token = body.get('merchant_token')
        cc_num = body.get('cc_num')
        security_code = body.get('security_code')
        amount = body.get('amount')
        card_type = body.get('card_type')
    else:
        return format_return("There was an error in your post.")

    merchant_table = dynamodb.Table('Merchant')
    bank_table = dynamodb.Table('Bank')
    transaction_table = dynamodb.Table('Transactions')
    
    merchant_status = merchantAuth(merchant_name, merchant_token, merchant_table)
    if merchant_status != "authorized":
        return create_response(200, {'status': merchant_status})
    
    # Check bank name
    if not check_bank_name(bank, bank_table):
        return create_response(200, {'status': 'bank name not found'})

    # Check account and funds
    account_status = check_account_and_funds(bank, cc_num, amount, bank_table, card_type)
    
    if random.randint(1, 10) == 1:
        last_four = str(cc_num)[-4:]
        transaction_table.put_item(
        Item={
            'MerchantName': merchant_name,
            'DateTime': datetime.now().isoformat(),  # Ensure to import datetime
            'MerchantID': merchant_token,  # You'll need to ensure you have this info
            'LastFour': last_four,
            'Amount': Decimal(str(amount)),
            'Status': 'Bank Not Available'
        }
        )

        
    if account_status != "approved":
        last_four = str(cc_num)[-4:]
        
        transaction_table.put_item(
        Item={
            'MerchantName': merchant_name,
            'DateTime': datetime.now().isoformat(),  # Ensure to import datetime
            'MerchantID': merchant_token,  # You'll need to ensure you have this info
            'LastFour': last_four,
            'Amount': Decimal(str(amount)),
            'Status': 'Declined'
        }
        )
        return create_response(200, {'status': account_status})
        
    if account_status == "approved":
        last_four = str(cc_num)[-4:]
        
        transaction_table.put_item(
        Item={
            'MerchantName': merchant_name,
            'DateTime': datetime.now().isoformat(),  # Ensure to import datetime
            'MerchantID': merchant_token,  # You'll need to ensure you have this info
            'LastFour': last_four,
            'Amount': Decimal(str(amount)),
            'Status': 'Approved'
        }
    )
    
    response_body = {
        'status': 'transaction approved',
        'merchant_name': merchant_name,
        'amount': amount
    }

    # Return the constructed JSON object
    return {
        'statusCode': 200,
        'body': json.dumps(response_body),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

def merchantAuth(name,token,merchant_table):
    response = merchant_table.get_item(
        Key={
            'MerchantName' : name,
            'Token' : token
        }
        )
    if response != None:
        return "authorized"

    else:
        return "bad merchant token"
    
def check_bank_name(bank_name, bank_table):
    try:
        # Perform a query on the table to find if any item with the given BankName exists
        response = bank_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('BankName').eq(bank_name)
        )
        if response.get('Items', []):
            return True  # Bank name exists in the table
        else:
            return False  # Bank name does not exist in the table
    except Exception as e:
        print(f"Error - Bad Bank or Account Number.")
        return False  # Error encountered, assume bank name not found

def update_account_balance(bank_table, account, transaction_amount, card_type):
    try:
        account_num = account['AccountNum']
        bank_name = account['BankName']
        transaction_amount = Decimal(str(transaction_amount))  # Convert transaction amount to Decimal

        if card_type.lower() == 'credit':
            credit_used = Decimal(str(account['CreditUsed']))  # Convert to Decimal
            new_credit_used = credit_used + transaction_amount
            response = bank_table.update_item(
                Key={'BankName': bank_name, 'AccountNum': account_num},
                UpdateExpression='SET CreditUsed = :newval',
                ExpressionAttributeValues={
                    ':newval': new_credit_used
                },
                ReturnValues='UPDATED_NEW'
            )
        elif card_type.lower() == 'debit':
            balance = Decimal(str(account['Balance']))  # Convert to Decimal
            new_balance = balance - transaction_amount
            response = bank_table.update_item(
                Key={'BankName': bank_name, 'AccountNum': account_num},
                UpdateExpression='SET Balance = :newval',
                ExpressionAttributeValues={
                    ':newval': new_balance
                },
                ReturnValues='UPDATED_NEW'
            )
        return response
    except Exception as e:
        print(f"Error updating account balance: {str(e)}")
        raise e

def check_account_and_funds(bank_name, account_num, amount, bank_table, card_type):
    try:
        account_num = int(account_num)
        amount = Decimal(str(amount))  # Convert amount to Decimal for arithmetic
        
        response = bank_table.get_item(Key={'BankName': bank_name, 'AccountNum': account_num})
        
        if 'Item' in response:
            account = response['Item']

            balance = Decimal(str(account['Balance'])) if 'Balance' in account else None
            credit_limit = Decimal(str(account['CreditLimit'])) if 'CreditLimit' in account else None
            credit_used = Decimal(str(account['CreditUsed'])) if 'CreditUsed' in account else None

            if card_type.lower() == 'credit':
                if credit_limit is None or credit_used is None:
                    return "Account data incomplete: missing credit fields."
                
                available_credit = credit_limit - credit_used
                if available_credit >= amount:
                    update_response = update_account_balance(bank_table, account, amount, card_type)
                    return "approved"
                else:
                    return "Declined. Insufficient Funds."
                    
            elif card_type.lower() == 'debit':
                if balance is None:
                    return "Account data incomplete: missing balance field."
                
                if balance >= amount:
                    update_response = update_account_balance(bank_table, account, amount, card_type)
                    return "approved"
                else:
                    return "Declined. Insufficient Funds."
            else:
                return "Invalid card type."
        else:
            return "Error - Bad Bank or Account Number."
            
    except Exception as e:
        print(f"Error occurred while checking account and funds: {str(e)}")
        return "Error checking account."
        
def create_response(status_code, message):
    return {
        'statusCode': status_code,
        'body': json.dumps({'status': message}),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
