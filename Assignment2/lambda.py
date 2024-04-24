def lambda_handler(event, context):
    print(event)

    if 'body' in event and event['body'] is not None:
        try:
            body = json.loads(event['body'])
            bank = body.get('bank')
            mechant_name = body.get('merchant_name')
            cc_num = body.get('cc_num')

            -----------------


    res = {
            "statusCode": 200,
            "headers": 
