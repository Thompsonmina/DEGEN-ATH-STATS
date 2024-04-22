import requests
import json
import pytz

from datetime import datetime

def bridged_after_ath_creation(reference_timestamp):
    ath_creation_date = "Apr 03 2024 02:46:20 AM (+01:00 UTC)"
    input_format = '%b %d %Y %I:%M:%S %p (%z %Z)'
    reference_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    
    # Parse the input timestamp into a datetime object
    input_time = datetime.strptime(ath_creation_date, input_format)
    input_time = input_time.astimezone(pytz.utc)
    
    # Parse the reference timestamp into a datetime object
    reference_time = datetime.strptime(reference_timestamp, reference_format)
    # Adjust timezone info for reference timestamp (assume it's already in UTC)
    reference_time = reference_time.replace(tzinfo=pytz.utc)

    # Compare the two timestamps
    return input_time < reference_time

def fetch_page(url, page_params):
    headers = {
        "accept": "application/json"
    }
    
    # GET request with the page parameters
    response = requests.get(url, headers=headers, params=page_params)
    response.raise_for_status()  # This will raise an error for a bad response
    return response.json()



def fetch_bridged_degens():
    # Base API endpoint
    base_url = "https://explorer.degen.tips/api/v2/addresses/0x888F05D02ea7B42f32f103C089c1750170830642/transactions"

    initial_page_params = {
        "filter": "to | from"
    }

    # Fetch the initial page of results
    data = fetch_page(base_url, initial_page_params)



    accounts = []
    count = 1
    while 1:
        # get all the successful transactions that arent transfered to the 0x000000000000000000000000000000000000006E account (burn address)
        accounts.extend([{"timestamp":x["timestamp"], "to":x["to"]["hash"], "val":x["value"], "transaction_hash":x["hash"]} for x in data["items"]
                            if x["result"]== "success" and x["to"]["hash"] != "0x000000000000000000000000000000000000006E" and bridged_after_ath_creation(x["timestamp"]) ])
        
        # accounts.sort(key=lambda x: datetime.strptime(x["timestamp"],'%Y-%m-%dT%H:%M:%S.%fZ'), reverse=True)
        
        if not bridged_after_ath_creation(min(accounts, key=lambda x: x["timestamp"])["timestamp"]):
            break

        if data["next_page_params"]:
            data = fetch_page(base_url, data["next_page_params"])
            count += 1
            print(count)


            # testing smaller output
            # if count % 200 == 0:
            #     with open(f"bridged/accounts_bridged_mod2{count}.json", "w") as outfile:
            #         json.dump(accounts, outfile, indent=2)

            #     print(data["next_page_params"])
        

    
    with open("accounts_bridged.json", "w") as outfile:
        json.dump(accounts, outfile, indent=2)   
    return accounts 


def get_last_address_in_path(decoded_input):
    
    # Extract the 'parameters' list
    parameters = decoded_input['parameters']
    
    # Find the object with the name 'path' and extract the last address
    for param in parameters:
        if param['name'] == 'path':
            # Ensure the value is a list and not empty
            if isinstance(param['value'], list) and param['value']:
                return param['value'][-1]

        

def fetch_accounts_where_next_transaction_is_ATH_SWAP(accounts):

    valid_swap_transactions = {}
    count = 0
    # for each of the accounts previously gotten that bridged over degen
    for bridge_transaction in accounts:
        print(bridge_transaction)
        user_transactions = []
        url = f"https://explorer.degen.tips/api/v2/addresses/{bridge_transaction['to']}/transactions"
        initial_page_params = {
            "filter": "to | from"
        }
        data = fetch_page(url, initial_page_params)

        while 1:
            user_transactions.extend([x for x in data["items"] if x["result"]== "success"])

            if data["next_page_params"]:
                data = fetch_page(url, data["next_page_params"])
                # print(data["next_page_params"])
            else:
                break
        
        user_transactions.sort(key=lambda x: x["block"])
        bridge_index = None
        # get the index of the bridge transaction
        for i in range(len(user_transactions)):
            if user_transactions[i]["hash"] == bridge_transaction["transaction_hash"]:
                print(bridge_transaction["to"])
                bridge_index = i
                break

        print(bridge_index, "bridge index")

        # find the next transaction that isnt a bridge transaction and if it is an ath swap, record it
        for i in range(bridge_index + 1, len(user_transactions)):
            
            # if you encounter another bridge transaction skip it and keep searching
            if user_transactions[i]["from"]["hash"] == "0x888F05D02ea7B42f32f103C089c1750170830642":
                continue
            

            # if the very next transaction that isnt a bridge transaction is a swap for ath, then record it
            if user_transactions[i]["method"] == "swapExactETHForTokens":
                # ensure that the token that is being swapped for is ath by checking if it matches the address of ath
                if get_last_address_in_path(user_transactions[i]["decoded_input"]) and get_last_address_in_path(user_transactions[i]["decoded_input"]) == "0xeb1c32ea4e392346795aed3607f37646e2a9c13f":
                    valid_swap_transactions[user_transactions[i]["hash"]] = {"user_address": bridge_transaction["to"], "timestamp": user_transactions[i]["timestamp"],
                            "degen_swapped_value": user_transactions[i]["value"],
                            "min_ath_swapped_for":[x["value"] for x in user_transactions[i]["decoded_input"]["parameters"] if x["name"] == "amountOutMin"][0]}
            
            
            break
        
        count += 1
        print(count)
                
    return valid_swap_transactions

def get_unique_transactions(accounts):
    # the block explorer's pagination duplicates transactions, this gets the unique transactions
    seen_hashes = set()
    unique_transactions = []

    # Filter out duplicates based on transaction_hash
    for item in accounts:
        hash = item['transaction_hash']
        if hash not in seen_hashes:
            seen_hashes.add(hash)
            unique_transactions.append(item)

    return unique_transactions

if __name__ == "__main__":
    # fetch_bridged_degens()
    # fetch_accounts_where_next_transaction_is_ATH_SWAP()
    pass



