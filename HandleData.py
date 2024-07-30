import asyncio
import json, time
import dateutil.parser
import os
from datetime import datetime
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import requests
import urllib3

f = open("Config.json", 'r+', encoding='utf-8')
config = json.load(f)


class HandleData:
    def __init__(self):
        self.cookies = {
            '_ga': 'GA1.2.1564887654.1644181048',
            'csrftoken': 'YewbsaeZsQTbbUrSWw68XUhTOsnm3l9ez2sfXytUIrYcly33qgMHbc6Mr2iwM2r0',
            'op_browser_state': 'e1b5449746b83db4d810aa2100c5afc8c449baf9f03dc03cd65519ff',
            'sessionid': 'kacgu0pq36y7tq89vu16uw825rh3ub49',
        }

        self.headers = {
            'authority': 'qs.fromarte.ch',
            'accept': 'application/json',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7,lb;q=0.6,id;q=0.5',
            'origin': 'https://qs.fromarte.ch',
            'referer': 'https://qs.fromarte.ch/qs',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
        }
        self.data = {
            'refresh_token': config["config"]["fromarte"]["refresh_token"],
            'client_id': 'pc',
            'grant_type': 'refresh_token',
            'redirect_uri': 'https://qs.fromarte.ch/login',
        }

        self.authToken = "0"
        self.lastChecked = '2022-12-14T15:46:19.944445'  # some artificial data in the future
        self.getAnswerQuery = config["config"]["queries"]["getAnswerQuery"]
        self.getHistAnswerQuery = config["config"]["queries"]["getHistAnswerQuery"]
        self.getAllWorkingItemsQuery = config["config"]["queries"]["getAllWorkingItemsQuery"]
        self.getAllWorkingItemsAfterQuery = config["config"]["queries"]["getAllWorkingItemsAfterQuery"]
        self.searchFilterAllWorkingItems = config["config"]["searchFilterAllWorkingItems"]
        self.nameNewestBackupFile = ""
        self.searchFilterMilkRelated = config["config"]["search_words"]

    def refreshToken(self):
        """
        Sends a request to the GQL endpoint of fromarte to refresh the authorization- and refresh-token.
        """
        got_new_token = False
        tries = 0
        # If the request gets denied or it is delayed, try it again (max 5 times).
        while got_new_token == False and tries < 5:
            try:
                response = requests.post('https://qs.fromarte.ch/openid/token', headers=self.headers,
                                         cookies=self.cookies,
                                         data=self.data)
                got_new_token = True
            except requests.exceptions.ConnectionError:
                print("Connection refused: Failed to fetch refresh token.")
            except urllib3.exceptions.ConnectTimeoutError:
                print("Connection timed out: Failed to fetch refresh token.")
            except Exception:
                print("Unexpected error occured: Failed to fetch refresh token.")
            finally:
                tries += 1
                if not got_new_token:
                    if tries < 5:
                        print("\nRetrying...")
                        time.sleep(config["config"]["retry_interval"])
                    else:
                        print("System will exit as five unsuccessful attempts were made. Please add it manually and restart the system.")
                        exit

        response_data = response.json()
        # Allocate the two token.
        self.authToken = response_data["access_token"]
        self.data['refresh_token'] = response_data["refresh_token"]
        config["config"]["fromarte"]["refresh_token"] = response_data["refresh_token"]
        with open("Config.json", "w") as jsonFile:
            json.dump(config, jsonFile, indent=4)

    def getAllWorkingItems(self, query, date_time=None):
        """
        Returns a JSON with all the open forms and corresponding information (i.e. UserID of creator, creation date)
        :return: Returns the received JSON.
        """
        transport = AIOHTTPTransport(url="https://qs.fromarte.ch/graphql/",
                                     headers={"authorization": "Bearer " + self.authToken})
        client = Client(transport=transport)
        query = gql(query)
        # Set the time to the time that it was last checked
        params = {"dateTime": self.lastChecked}
        # If the dateTime is needed (when checking for new forms), execute with the params.
        if date_time:
            response = client.execute(query, variable_values=params)
        else:
            response = client.execute(query)
        return response

    def saveAsJson(self, response_json, name_of_json):
        """
        Saves a response as a JSON to the directory.
        :param response_json: JSON which should be saved
        :param name_of_json: The name the JSON should get.
        """
        with open(name_of_json + '.json', 'w', encoding='utf-8') as f:
            json.dump(response_json, f, ensure_ascii=False, indent=4)

    def getDocument(self, document_id, query, date_time=None):
        """
        Through a provided query and document ID this function fetches the associated JSON and returns the received
        file. The extraction only works if there are not more than one k, v pair wih the same key. Else the latter
        will be taken.
        :param document_id: Id of the document
        :param query: GraphQL query
        :param date_time: Relevant when fetching historical answers. Default is false (=not relevant).
        :return: Received JSON file
        """
        transport = AIOHTTPTransport(url="https://qs.fromarte.ch/graphql/",
                                     headers={"authorization": "Bearer " + self.authToken})
        client = Client(transport=transport)
        # Provide a GraphQL query with the docID
        query = gql(query)
        params = {"id": document_id}
        # DateTime may be relevant when fetching historical answers
        if date_time:
            params['dateTime'] = datetime.now().isoformat()
        got_connection = False
        tries = 0
        response = None
        while got_connection == False and tries < 5:
            try:
                response = client.execute(query, variable_values=params)
                got_connection = True
            except requests.exceptions.ConnectionError:
                print("Connection refused, failed to fetch forms.")
            except asyncio.exceptions.TimeoutError:
                print("Timeout error occurred, failed to fetch forms.")
            except Exception as e:
                print("An unexpected error occurred, failed to fetch forms.", type(e))
            finally:
                tries += 1
                if not got_connection:
                    if tries < 5:
                        print("Retrying...")
                        time.sleep(config["config"]["retry_interval"])
                    else:
                        print("Failed to establish a connection and to fetch forms. Exiting after 5 tries.")
        return response

    def getRelevantInfoAllWorkingItems(self, json_data):
        """
        This function is designed to extract relevant information from the JSON with all the open forms.
        :param json_data: Passing the JSON into the function.
        :return: Return a dict with the extracted fields.
        """
        final = {}
        # Check if it is dict or a list
        if type(json_data) == dict:
            for k, v in json_data.items():
                if type(v) == dict or type(v) == list:
                    # If the value is still a dict or a list, call itself again (recursion).
                    final = final | self.getRelevantInfoAllWorkingItems(v)
                # append the key value pair, if they are of relevance.
                if k in self.searchFilterAllWorkingItems:
                    final[k] = v

        elif type(json_data) == list:
            for element in json_data:
                final = final | self.getRelevantInfoAllWorkingItems(element)
        # set the lastUpdated variable = 0 and lastModifiedBy to an empty string
        final["lastUpdated"] = 0
        final["lastModifiedBy"] = ""
        return final

    def updateFiles(self):
        """
        This is the core function of the script. It fetches the "historical answers" of unfinished forms.
        If something was deleted or altered it will be indicated with a "~", a "+" indicate that an new answer was
        given. The Functions then updates the new or altered answers on the JSON and saves the new file locally in the
        Backup folder.
        :return: The IDs of the Files that were altered/updated. The ID of the forms, that were frozen. And
        the local Names of the file names (ID-Unix timestamp) for consistent naming.

        """
        ids_of_updated_files = []
        ids_to_freeze = []
        local_names = []
        with open(self.nameNewestBackupFile, encoding='utf-8') as f:
            data = json.load(f)
            # used to see if a new file needs to be saved to BackUpFile
            total_changes = 0
            # loop through all stored documents
            for node in data.items():
                changes_to_current_file = 0
                newest_history_date = data[node[0]]["lastUpdated"]
                if not node[1]["lastUpdated"]:
                    # Initiate a random date in the past.
                    newest_history_date = "2000-07-19T19:27:19.121610"
                # check if the document is already frozen after first fetching
                if node[1]['status'] != 'RUNNING':
                    ids_to_freeze.append(node[0])
                    continue
                # Fetch al docs again
                returnedJson = self.getDocument(node[0], self.getHistAnswerQuery, date_time=True)
                # chek if it got frozen in the meantime
                new_answers = []
                if returnedJson:
                    if returnedJson['allDocuments']["edges"][0]["node"]["case"]["status"] != 'RUNNING':
                        ids_to_freeze.append(node[0])
                        print(node[0], "Will be frozen")
                        continue
                    # check if something was changed with "~" and if the answer is relevant
                    for historical_answer in returnedJson["documentAsOf"]["historicalAnswers"]['edges']:
                        question = historical_answer["node"]["question"]["slug"]
                        hist_date = historical_answer["node"]["historyDate"]
                        if historical_answer["node"]["historyType"] == "~" and question in self.searchFilterMilkRelated \
                                and newest_history_date != hist_date[:(hist_date.index("+"))]:
                            # something was altered or deleted and is new
                            new_answers.append(question)
                            if dateutil.parser.parse(newest_history_date) < dateutil.parser.parse(
                                    hist_date[:(hist_date.index("+"))]):
                                newest_history_date = hist_date[:(hist_date.index("+"))]
                            # save the Username
                            modifiedByWho = historical_answer["node"]["historyUserId"]
                        elif question in self.searchFilterMilkRelated and question not in node[1]['answer']:
                            # check if a new relevant answer was given
                            new_answers.append(question)
                            if dateutil.parser.parse(newest_history_date) < dateutil.parser.parse(
                                    hist_date[:(hist_date.index("+"))]):
                                newest_history_date = hist_date[:(hist_date.index("+"))]
                            modifiedByWho = historical_answer["node"]["historyUserId"]
                        # "Kultur" related variables need to be handled differently, 833-10-kultur-lotnummer and
                        # 833-10-kultur variables need to be appended manually
                        if historical_answer["node"]["question"]["label"] == "Kulturen" and node[1]["lastUpdated"] != \
                                historical_answer["node"]["historyDate"]:
                            new_answers.extend(["833-10-kultur", "833-10-kultur-lotnummer"])
                            modifiedByWho = historical_answer["node"]["historyUserId"]
                if new_answers:
                    # check if the new answers are really new maybe the historical answer is the same.
                    # This makes sure no unnecessary transaction will me triggered.
                    new_fetched_answers = {key: val for key, val in self.getRelevantInfoFromJsonAnswers(
                        self.getDocument(node[0], self.getAnswerQuery), new_answers).items() if val != "tbt"}
                    for question, newVal in new_fetched_answers.items():
                        try:
                            if node[1]["answer"][question] or node[1]["answer"][question] is None:
                                if node[1]["answer"][question] != newVal:
                                    # the new value was really new
                                    data[node[0]]["answer"][question] = newVal
                                    total_changes += 1
                                    changes_to_current_file += 1
                                    if node[0] not in ids_of_updated_files:
                                        ids_of_updated_files.append(node[0])
                        except:
                            # Catch if question does not exist
                            data[node[0]]["answer"][question] = newVal
                            total_changes += 1
                            changes_to_current_file += 1
                            if node[0] not in ids_of_updated_files:
                                ids_of_updated_files.append(node[0])

                    # check if a given value was deleted
                    for quest in new_answers:
                        if quest not in new_fetched_answers and quest in data[node[0]]["answer"].keys():
                            data[node[0]]["answer"].update({quest: None})
                            total_changes += 1
                            changes_to_current_file += 1
                            if node[0] not in ids_of_updated_files:
                                ids_of_updated_files.append(node[0])

                    # create new BackupFile if changes to current file were made
                    if changes_to_current_file != 0:
                        # update the lastUpdated time
                        data[node[0]]["lastUpdated"] = newest_history_date
                        data[node[0]]["lastModifiedBy"] = modifiedByWho
                        os.chdir("BackupFiles")
                        to_save = {}
                        to_save[node[0]] = data[node[0]]
                        local_name = node[0] + r"-" + str(int(time.time()))
                        local_names.append(local_name)
                        self.saveAsJson(to_save, local_name)
                        os.chdir("..")

        # update the new BackupJSON with the new time
        if total_changes != 0:
            # Update nameNewestBackupFile variable
            print(total_changes, " were made")
            new_name = "BackUp" + str(int(time.time())) + ".json"
            self.nameNewestBackupFile = new_name
            with open(new_name, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        return ids_of_updated_files, ids_to_freeze, local_names

    def compareDates(self, curr_date, hist_date):
        """
        Checks if the hist_date is newer than the curr_date.
        :param curr_date: The latest date, of type datetime.
        :param hist_date: The date of the history answer, of type datetime.
        :return:
        """
        if dateutil.parser.parse(curr_date) < dateutil.parser.parse(hist_date):
            return True

    def mostRecentFileByID(self, id):
        """
        Gets the most recent file by ID.
        :param id: A ID of a file.
        :return: Return the newest file.
        """
        return max(
            [int(x[x.index("-") + 1:x.index(".json") + 1]) for x in os.listdir("BackupFiles") if x.startswith(id)])

    def checkForNewFiles(self):
        """
        Fetches all the working items again and checks if they are new, if yes it appends to the current BackUp file
        :return: Returns the new forms.
        """
        new_items = self.getAllWorkingItems(query=self.getAllWorkingItemsAfterQuery, date_time=self.lastChecked)
        # Update the last checked time to the current UCT time, as the server runs on UCT time.
        self.lastChecked = datetime.now().utcnow().isoformat()
        new_forms, local_names = self.helperFunctionForExtractionAndSaving(new_items)
        new_forms_keys = list(new_forms.keys())
        for new_form in new_forms_keys:
            date_str = new_forms[new_form]['createdAt']
            if "+" in date_str:
                date_str = date_str.split("+")[0]
            date = datetime.fromisoformat(date_str)
            last_checked = datetime.fromisoformat(self.lastChecked)
            if date < last_checked:
                del new_forms[new_form]
        if new_forms:
            self.writeOnCurrentBackUpFile(new_forms)
            print("new item", new_forms)
            return new_forms, local_names
        else:
            return None, None

    def helperFunctionForExtractionAndSaving(self, all_work_items_json):
        """
        Helps extracting and organizing relevant info from all the forms from the digitalQM. Fetches the corresponding
        answer JSON from each form.
        :param all_work_items_json: The AllWorkingItems json with all the items in the DigitalQM.
        :return: Returns the BackUp file with all nodes and all its relevant variables, plus the local names
        for consistent naming.
        """
        final = {}
        local_names = []
        curr_string_time = str(int(time.time()))
        # Loop trough the file with all the forms.
        for node in all_work_items_json["allCases"]["edges"]:
            nested = {}
            # Feed each node into getRelevantInfoAllWorkingItems, to extract the relevant information.
            relevant_data = self.getRelevantInfoAllWorkingItems(node)
            id_of_current_node = node["node"]["document"]["id"]
            os.chdir("Answers")
            # Save the new fetched answer file from the forms inside the Answers directory.
            st = time.time()
            self.saveAsJson(self.getDocument(id_of_current_node, self.getAnswerQuery),
                            "Answer_" + id_of_current_node + curr_string_time)
            # Call getRelevantInfoFromJsonAnswers to extract all the relevant variables from the new
            relevant_data["answer"] = {key: val for key, val in self.getRelevantInfoFromJsonAnswers(
                "Answer_" + id_of_current_node + curr_string_time + ".json").items() if val != "tbt"}
            nested[relevant_data["id"]] = relevant_data
            final.update(nested)
            os.chdir("..")
            os.chdir("BackupFiles")
            # Save the new organized JSON with the extracted variables also to the BackupFiles folder.
            if nested:
                name_of_file = relevant_data["id"] + r"-" + str(int(time.time()))
                local_names.append(name_of_file)
                self.saveAsJson(nested, name_of_file)
            os.chdir("..")
        return final, local_names

    def freezeForm(self, ids):
        """
        Freezes completed forms. Frozen forms are extracted from the BackUp file and moved into a FrozenIDs.json.
        :param ids: Takes a list with IDs a parameter.
        :return Returns nothing, but if we have an empty list the function does not need to run, or empty files
        may be created.
        """
        # May be called with an empty list.
        if not ids:
            return
        with open(self.nameNewestBackupFile, "r+", encoding='utf-8') as f:
            data = json.load(f)
            # check if the file where all the frozen files are saved already exists.
            if os.path.exists(r"FrozenIDs.json"):
                frozen = open("FrozenIDs.json", "r+", encoding='utf-8')
                already_frozen = json.load(frozen)
            else:
                frozen = open("FrozenIDs.json", "w", encoding='utf-8')
                already_frozen = {}
            # Iterate through the ids of the files which need to be frozen.
            for id in ids:
                # create the same data structure as in the BackUp file, and add to the alreadyFrozen file.
                popped = data.pop(id)
                already_frozen[popped["id"]] = popped
                already_frozen[popped["id"]]["status"] = "COMPLETED"
            # Overwrite the old file with the new appended JSON file
            frozen.seek(0)
            json.dump(already_frozen, frozen, indent=2)
            frozen.truncate()
            frozen.close()
            print("new frozenIDs file: ", already_frozen)
            # Save the BackUp file with the RUNNING files, as all COMPLETED ones were frozen.
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    def writeOnCurrentBackUpFile(self, file_to_append):
        """
        Writes a JSON onto the currents BackUp JSON.
        """
        with open(self.nameNewestBackupFile, "r+", encoding='utf-8') as f:
            curr_data = json.loads(f.read())
            # Appends to the current file and overwrites the outdated data
            curr_data.update(file_to_append)
            f.seek(0)
            json.dump(curr_data, f, indent=2)
            f.truncate()

    def getRelevantInfoFromJsonAnswers(self, json_name, search_words=None):
        """
        Extracts certain variables from a JSON containing the answers to a filled out from.
        :param json_name: Name of the (JSON) file that needs to be searched.
        :param search_words: The variables that are relevant and need to be extracted.
        :return:
        """
        # take the predefined searchwords, if the variable is not defined.
        if search_words is None:
            search_words = self.searchFilterMilkRelated
        final = {}

        # check all answer nodes for relevant variables
        if type(json_name) == dict:
            for k, v in json_name.items():
                if type(v) == dict or type(v) == list:
                    final = final | self.getRelevantInfoFromJsonAnswers(v, search_words)
                if v in search_words:
                    final[v] = "tbt"
                if "tbt" in final.values():
                    if "Value" in k:
                        final.update({ke: v for ke, val in final.items() if type(v) in [str, float, int]})
        elif type(json_name) == list:
            for element in json_name:
                final = final | self.getRelevantInfoFromJsonAnswers(element, search_words)

        return final
