// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;


contract CheeseChainPrivate {

    uint256 public amountForms; // starts with 0
    string[] public formsList;

    address public administrator;

    struct Participant {
        string name;
        string company;

    }
    struct Form {
        string name;
        Participant createdByUser;
        Participant lastModifiedBy;
        uint256 createdAt;
        uint256 lastModifiedAt;
        bool frozen;
        string fileName;
        string fileHash;
        string additionalData;
        uint256 changeCount; // counts the number of changes (i.e., filenames)
        string previousFileNames;// array was given too much trouble, changed to a format where the filenames are divided by commas
        string previousFileHashes;
    }
    // Mapping of integers to forms (i.e., each for has an unique ID)
    // Each form has an unique ID which can be hashed and used as identified to retrieve the form

    mapping(string => Form)  public  forms;
    mapping(uint256 => Participant) public  partipants;



    // Constructor (called upon contract creation of the contract)
    constructor() {
      administrator = msg.sender;
      addParticipant(1391, "Scheid", "UZH");
      addParticipant(1393, "Killer", "UZH");
      addParticipant(1392, "Rafati", "UZH");
    }

    // basic auth
    function isAdministrator(address _address) view public returns(bool) {
        return _address == administrator;
    }
    modifier onlyAdministrator {
        require(msg.sender == administrator, "This function is only callable by an admin!");
        _;
    }

    // events

    event FormFrozen(string indexed _formID);

    // functions

    function addParticipant(uint _userID, string memory _name, string memory _company)  public onlyAdministrator {
        Participant memory participant =  Participant(_name, _company);
         partipants[_userID]  =  participant;
    }

    function createForm(string memory _id, string memory _name, uint256 _createdByUser, string memory _fileName, string memory _fileHash, string memory _additionalData)  public  onlyAdministrator {
        require(forms[_id].createdAt==0,"Form already exist.");

        Form memory newForm = Form({
            name: _name,
            createdByUser: partipants[_createdByUser],
            lastModifiedBy: partipants[_createdByUser],
            createdAt: block.timestamp,
            lastModifiedAt: block.timestamp,
            frozen: false,
            fileName:  _fileName,
            fileHash: _fileHash,
            additionalData: _additionalData,
            changeCount: 0,
            previousFileNames: "NULL",
            previousFileHashes: "NULL"
        });

        formsList.push(_id);
        forms[_id] = newForm;
        amountForms++;
    }

    function getUpdateCount(string memory _id) public view returns (uint256){
        return forms[_id].changeCount;
    }
    function getUpdate(string memory _id) public view returns (string memory) {
        return forms[_id].previousFileNames;
    }

    function updateForm (string memory _id,  uint256 _lastModifiedBy,  string memory _fileName, string  memory _fileHash, string memory _additionalData) public onlyAdministrator {
        require(forms[_id].createdAt!=0,"Form does not exist.");
        require(forms[_id].frozen == false, "Cannot update a frozen form");
        forms[_id].lastModifiedBy =  partipants[_lastModifiedBy];
        forms[_id].lastModifiedAt =  block.timestamp;
        forms[_id].changeCount++;
        forms[_id].previousFileNames = string(bytes.concat(bytes(forms[_id].previousFileNames),",", bytes(forms[_id].fileName)));
        forms[_id].previousFileHashes = string(bytes.concat(bytes(forms[_id].previousFileHashes),",", bytes(forms[_id].fileHash)));
        forms[_id].fileName =  _fileName;
        forms[_id].fileHash =  _fileHash;
        forms[_id].additionalData = _additionalData;

    }
    function freezeForm(string memory _id) public onlyAdministrator {
        require(forms[_id].frozen == false, "Form already frozen");
        forms[_id].frozen = true;
        emit FormFrozen(_id);
    }

}