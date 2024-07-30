import hashlib
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import ContractLogicError

f = open("Config.json", 'r', encoding='utf-8')
config = json.load(f)

class CommunicateToSmartContract:
    def __init__(self):
        self.__mySCAdress = config["config"]["blockchain"]["SENDER_ADDRESS"]
        self.abi = config["config"]["blockchain"]["abi"]
        self.ScAddress = config["config"]["blockchain"]["CREATED_CONTRACT_ADDRESS"]
        self.w3 = Web3(Web3.HTTPProvider(config["config"]["blockchain"]["RPC_SERVER"]))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract_instance = self.w3.eth.contract(address=self.ScAddress, abi=self.abi)

    def createHash(self, json_to_hash):
        """
        Hashes a JSON with the Sha 256 hash.
        :param json_to_hash: The file (dictionary) that needs to be hashed.
        :return:
        """
        return hashlib.sha256(json.dumps(json_to_hash).encode('utf8')).hexdigest()

    def createNewFormSmartContract(self, id, data, name_of_file):
        """
        Creates a new instance on the Blockchain, with the given parameters.
        :param id: ID of the form
        :param data: The file itself
        :param name_of_file: Name of the local file. "ID-Unix timestamp"
        """
        try:
            self.contract_instance.functions.createForm(id, data["name"], 1391, name_of_file,
                                                        self.createHash(data), "").transact({'from': self.__mySCAdress})
        except ContractLogicError:
            print("ContractLogicError occured, the form seems to have been created already.")
        except Exception as e:
            print("Unexpected error occured:", e)

    def updateFormOnSmartContract(self, id, backup_file_name, name_of_file):
        """
        Updates a form instance on the Blockchain, with the given parameters.
        :param id: ID of the form
        :param backup_file_name: Name of the BackUpFile.
        :param name_of_file: Name of the local file. "ID-Unix timestamp"
        """
        with open(backup_file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.contract_instance.functions.updateForm(id, 1391,  # additional answers may be given
                                                    name_of_file, self.createHash(data),
                                                    "").transact({'from': self.__mySCAdress})

    def freezeForm(self, id):
        """
        Freezes a from on the Blockchain
        :param id: ID of the form that needs to be frozen.
        """
        try:
            self.contract_instance.functions.freezeForm(id).transact({'from': self.__mySCAdress})
        except ContractLogicError:
            print("ContractLogicError occured, the form seems to be frozen already.")
        except Exception as e:
            print("Unexpected error occured:", e)
