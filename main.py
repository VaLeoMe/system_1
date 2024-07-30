import json
import time

from CommunicateToSmartContract import CommunicateToSmartContract
from HandleData import HandleData

import os
from web3 import Web3
from dotenv import load_dotenv

# make instances Global
d = HandleData()
c = CommunicateToSmartContract()

f = open("Config.json", 'r+', encoding='utf-8')
config = json.load(f)

def main():
    """
    Main function, calling the most important functions. Everything before the while true loop is executed only
    once. The while true loop is a infinite loop, meaning the DigitalQM is always checked for new forms and the RUNNING
    ones are updated.

    """
    add_and_unlock_account()
    d.refreshToken()
    d.saveAsJson(d.getAllWorkingItems(d.getAllWorkingItemsQuery), "AllWorkingItems")
    firstTimeRun()
    remaining_time = config["config"]["form_fetch_interval"]
    token_fetch_interval = config["config"]["token_fetch_interval"]
    while True:
        d.refreshToken()
        if remaining_time <= 0:
            refetchingFreezingAndUpdating()
            new_files, local_names = d.checkForNewFiles()
            creteNewFormOnSC(new_files, local_names)
            remaining_time = config["config"]["form_fetch_interval"]
        remaining_time -= token_fetch_interval
        time.sleep(token_fetch_interval)

def refetchingFreezingAndUpdating():
    """
    Calls the updateFiles function, which returns a list of the forms that need to be updated and the ones that need to be
    frozen. The local names are also returned by the update function, as the names need to bed the same in the local BC.
    The updateFiles function already saved the files locally, only the BC need to updated.
    """
    updated_ids, ids_to_freeze, local_names = d.updateFiles()
    # If there are forms to update: Iterate, and call the function updateFormOnSmartContract to update the BC.
    if updated_ids:
        print("to update: ", updated_ids)
        for id in updated_ids:
            c.updateFormOnSmartContract(id, d.nameNewestBackupFile,
                                        [item for item in local_names if item.startswith(id)][0])
    else:
        print("nothing to update")
    # If there are forms that got frozen: Freeze on the BC and locally.
    if ids_to_freeze:
        # Freeze locally
        d.freezeForm(ids_to_freeze)
        # Freeze on BC
        [c.freezeForm(id) for id in ids_to_freeze]



def creteNewFormOnSC(newFiles, local_names):
    """
    Creates new instance on the BC.
    :param newFiles: A dict with the new form that need to be created on the BC. Key is the ID and val the content.
    :param local_names: Their local names, to have constant naming on the BC and the host.
    """
    if newFiles:
        for id, new_file in newFiles.items():
            c.createNewFormSmartContract(id, new_file, [item for item in local_names if item.startswith(id)][0])


def firstTimeRun():
    """
    Helper function when the script is first ran. Creating the Backup file, saving the forms and their answers locally.
    """
    back_up_file_name = 'BackUp' + str(int(time.time())) + ".json"
    with open(r'AllWorkingItems.json', encoding='utf-8') as f:
        loaded = json.load(f)
        # save the relevant data inside a nested json called BackUp
        d.nameNewestBackupFile = back_up_file_name
        with open(back_up_file_name, 'w', encoding='utf-8') as jsonFile:
            # Pass the json with AllWorkingItems into the helperFunctionForExtractionAndSaving to first save and
            # extract. The Returns the local names and the json for the BackUp file.
            final, local_names = d.helperFunctionForExtractionAndSaving(loaded)
            json.dump(final, jsonFile, indent=2)
            # send the created BackUp JSON to the local BC
            for id, val in final.items():
                # For each form create an instance on the BC
                c.createNewFormSmartContract(id, val, [item for item in local_names if item.startswith(id)][0])
    print("ran for the fist time")

def get_secret(secret_name):
    secret_file_path = os.getenv(f"{secret_name.upper()}_FILE")
    if secret_file_path:
        with open(secret_file_path, 'r') as file:
            secret_value = file.read().strip()
        return secret_value
    else:
        raise FileNotFoundError(f"{secret_name.upper()}_FILE environment variable not set or file not found")

def add_and_unlock_account():
    load_dotenv()

    http_provider = get_secret('http_provider')
    private_key = get_secret('private_key')
    metamask_pw = get_secret('metamask_password')

    # Connect to the Ethereum node
    web3 = Web3(Web3.HTTPProvider(http_provider))
    # Check if connected to the node
    if web3.isConnected():
        print("Connected to Ethereum node")
    else:
        print("Failed to connect to Ethereum node")

    # List accounts before
    accounts = web3.eth.accounts
    print("Accounts on the node:", accounts)

    try:
        account = web3.eth.account.privateKeyToAccount(private_key)
        if account.address not in accounts:
            web3.geth.personal.importRawKey(private_key, metamask_pw)
        web3.geth.personal.unlockAccount(account.address, metamask_pw, 300)
        print(f"Account {account.address} unlocked")
    except Exception as e:
        print("Failed to import/unlock account:", e)

    # List accounts after
    accounts = web3.eth.accounts
    print("Accounts on the node:", accounts)


if __name__ == '__main__':
    main()
