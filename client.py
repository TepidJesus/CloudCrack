from job_handler import JobHandler, STATUS
from errors import MaskFormatError, ConfigError, CredentialsFileNotFoundError
from controller import AwsController
import json
import signal

## Problems:
## TODO: Finish settings menu and add a way to change settings and save them to the config fil
## TODO: Potentially add a seperate control queue for each Ec2 hashing instance

class ClientController:

    def __init__(self):
        try:
            self.config = self.get_config()
        except FileNotFoundError:
            print("Error: The config file does not exist. Did you delete it? Go get a new one from the repository, it's kind of important.")
            exit()
        except ConfigError as e:
            print(e)
            exit()

        if not self.config["offline_mode"]:
            try:
                self.aws_controller = AwsController(self.config, "client")
            except 
            self.job_handler = JobHandler(self.aws_controller, "client", self.config["debug_mode"])
        
    def run(self):
        self.print_welcome()
        signal.signal(signal.SIGINT, self.handle_interrupt)
        while True:
            user_input = input("\nCloudCrack > ")
            if not self.config["offline_mode"]:
                self.job_handler.check_for_response()
            user_input.strip()
            input_as_list = user_input.split(" ")

            if input_as_list[0] == "help":
                self.print_help()
            elif input_as_list[0] in ["exit", "close", "quit"]:
                if not self.config["offline_mode"]:
                    self.job_handler.cancel_all_jobs()
                    self.aws_controller.cleanup()
                break
            elif input_as_list[0] == "show":
                if len(input_as_list) < 2:
                    print("Use 'show all' to show all jobs or 'show <job_id>' to show a specific job")
                    continue 
                if input_as_list[1] == "all":
                    self.show_current_jobs()
                else:
                    try:
                        job_id = int(input_as_list[1])
                        self.show_current_job(job_id)
                    except:
                        print("Invalid Job ID")
            elif input_as_list[0] == "create":
                self.create_screen()
            elif input_as_list[0] == "cancel":
                if (len(input_as_list) == 2):
                    if input_as_list[1] == "all":
                        self.job_handler.cancel_all_jobs()
                    try:
                        job_id = int(input_as_list[1])
                        self.job_handler.cancel_job(job_id)
                    except:
                        print("Invalid Job ID")
                else:
                    job_id = int(input("Job ID: "))
                    try: 
                        self.job_handler.cancel_job(job_id)
                    except:
                        print("Invalid Job ID")
            elif input_as_list[0] ==  "settings":
                self.options_screen()
            else:
                print("Unknown Command -- Type 'help' for a list of commands")

    def handle_interrupt(self, signal, frame):
        print("\nExiting...")
        try:
            self.aws_controller.cleanup()
        except:
            pass
        exit(0)

    def print_welcome(self):
        print(""" 
             _______  ___      _______  __   __  ______   _______  ______    _______  _______  ___   _ 
            |       ||   |    |       ||  | |  ||      | |       ||    _ |  |   _   ||       ||   | | |
            |       ||   |    |   _   ||  | |  ||  _    ||       ||   | ||  |  |_|  ||       ||   |_| |
            |       ||   |    |  | |  ||  |_|  || | |   ||       ||   |_||_ |       ||       ||      _|
            |      _||   |___ |  |_|  ||       || |_|   ||      _||    __  ||       ||      _||     |_ 
            |     |_ |       ||       ||       ||       ||     |_ |   |  | ||   _   ||     |_ |    _  |
            |_______||_______||_______||_______||______| |_______||___|  |_||__| |__||_______||___| |_|

            """)
        print("Welcome to CloudCrack v1.3")
        print("Type 'help' for a list of commands")

    def print_help(self):
        print("\nhelp - print this message")
        print("exit - exit CloudCrack")
        print("show <all> / <job_id>) - list all jobs or show a specific job")
        print("create - create a new job")
        print("cancel <job_id> - cancel a job")

    
    def show_current_jobs(self):
        print("Current Jobs:")
        for job_id in self.job_handler.job_log.keys():
            job = self.job_handler.get_job(job_id)
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            if job.job_status == STATUS.RUNNING:
                print("Progress: " + str(round(job.progress[0] / job.progress[1], 4) * 100) + "%")
            elif job.job_status == STATUS.COMPLETED:
                print("Result: " + job.required_info)
            print("---------------------------------")

    def show_current_job(self, job_id):
        try:
            job = self.job_handler.get_job(job_id)
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            if job.job_status == STATUS.RUNNING:
                print("Progress: " + str(round(job.progress[0] / job.progress[1], 2) * 100) + "%")
            elif job.job_status == STATUS.COMPLETED:
                print("Result: " + job.required_info)
            print("---------------------------------")
        except:
            raise Exception("Invalid Job ID")

    def create_screen(self):
        user_input = ""
        _hash = ""
        hash_type = ""
        attack_mode = ""
        mask = ""
        dictionary = ""
        output_file = ""
        hash_file_location = ""
        
        while user_input != "back" and user_input != "exit":
            user_input = input("\nCloudCrack > Create > ")
            input_as_list = user_input.split(" ")

            if input_as_list[0].lower() == "options":
                print("Options:")
                print("Hash: " + _hash)
                print("Hash Type: " + hash_type)
                print("Attack Mode: " + str(attack_mode))
                print("Mask: " + mask)
                print("Dictionary: " + dictionary)
                print("Output (Optional - Location of desired text file for output): " + output_file)
                print("Hashes (Optional - Location of bulk hash file): " + hash_file_location)
            elif input_as_list[0].lower() == "help":
                print("\nhelp - print this message")
                print("exit - return to the main menu")
                print("set <option> <value> - set an option to a value")
                print("run - run the job")
                print("options - list the current options and their values")
                print("clear - clear all options")

            if input_as_list[0].lower() == "set":
                if input_as_list[1].lower() == "hash":
                    _hash = input_as_list[2].strip()
                elif input_as_list[1].lower() == "type":
                    hash_type = input_as_list[2].strip()
                elif input_as_list[1].lower() == "mode":
                    if (input_as_list[2].lower() not in ["0", "3", "dictionary", "mask"]):
                        print("Invalid attack mode")
                        continue
                    else:
                        if input_as_list[2].lower() == "dictionary":
                            attack_mode = 0
                        elif input_as_list[2].lower() == "mask":
                            attack_mode = 3
                        else:
                            attack_mode = int(input_as_list[2].strip())
                elif input_as_list[1].lower() == "mask":
                    mask = input_as_list[2].strip()
                    if not self.is_valid_mask(mask):
                        mask = ""
                elif input_as_list[1].lower() == "dictionary":
                    dictionary = input_as_list[2].strip()
                elif input_as_list[1].lower() == "output":
                    output_file = input_as_list[2].strip()
                elif input_as_list[1].lower() == "hashes":
                    hash_file_location = input_as_list[2].strip()
                else:
                    print("Invalid option -- Type 'help' for a list of options")

            if input_as_list[0].lower() in ["run", "start", "create"]:
                if dictionary == "" and attack_mode == 0: 
                    print("You must provide a dictionary for attack mode 0") 
                    continue
                if mask == "" and attack_mode == 3:
                    print("You must provide a mask for attack mode 3")
                    continue
                if _hash == "" and hash_file_location == "":
                    print("You must provide a hash OR hash file location")
                    continue
                if hash_type == "":
                    print("You must provide a hash type")
                    continue
                if attack_mode == "":
                    print("You must provide an attack mode")
                    continue
                if attack_mode == 3 and not self.is_valid_mask(mask): ## TODO: Remove this if unnecessary
                    print("Invalid mask. See the HashCat wiki for help")
                    continue
                
                if dictionary != "":
                    try:
                        with open(dictionary, "r") as file:
                            required_info = dictionary
                            pass
                    except:
                        print("Failed to open dictionary file. Please check the file location and try again")
                        continue
                elif mask != "":
                    required_info = mask

                if output_file != "":
                    if self.config["debug_mode"] == True:
                        print("[DEBUG] Attempting to Locate Output File: " + output_file)
                    try:
                        with open(output_file, "w") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Located Output File")
                    except:
                        with open(output_file, "x") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Created Output File")
                
                if hash_file_location != "":
                    if self.config["debug_mode"] == True:
                        print("[DEBUG] Attempting to Get Hash file location: " + hash_file_location)
                    try:
                        with open(hash_file_location, "r") as file:
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Successfully Located Hash File")
                    except:
                        print("Failed to open hash file. Please check the file location and try again")
                        continue

                    with open(hash_file_location, "r") as file:
                        hashes = file.readlines()
                    for _hash in hashes:
                        _hash = _hash.strip(" ")
                        _hash = _hash.strip("\n")
                        try: 
                            jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info, output_file)
                            self.job_handler.send_job(jb)
                        except Exception as e:
                            print(f"Failed To Create Job For Hash: {_hash}")
                            if self.config["debug_mode"] == True:
                                print("[DEBUG] Failed To Create Job For Hash: " + _hash)
                                print(f"[DEBUG] Reason: {e}")
                            continue
                else:
                    jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info, output_file)
                    self.job_handler.send_job(jb)

            if input_as_list[0] == "clear":
                _hash = ""
                hash_type = ""
                attack_mode = ""
                mask = ""
                dictionary = ""
                output_file = ""
                hash_file_location = ""

        return ## Should probably return something
    
    def options_screen(self):
        user_input = ""
        
        while user_input != "back" and user_input != "exit":
            self.show_current_settings()
            user_input = input("\nCloudCrack > Settings > ")
            input_as_list = user_input.split(" ")
            if input_as_list[0] == "set":
                if input_as_list[1] in self.config:
                    if self.set_option(input_as_list[1], input_as_list[2]):
                        print(f"Successfully set {input_as_list[1]} to {input_as_list[2]}")
                    else:
                        print(f"Failed to set {input_as_list[1]} to {input_as_list[2]}")
                else:
                    print(f"Invalid option {input_as_list[1]}")


                    
    def set_option(self, option, value):
        if value == None or value == "":
            return False #NEWERRORNEEDED
        try:
            with open("config.json", "r") as file:
                config = json.load(file)
                config[option] = value
            with open("config.json", "w") as file:
                json.dump(config, file)
                self.config = config
            return True #NEWERRORNEEDED
        except:
            print("Failed to open config file")
            return False #NEWERRORNEEDED
        

    def show_current_settings(self): 
        print("\nCurrent Settings:")
        option_categories = []
        for option in self.config:
            option_categories.append(option)
            print(f"{option}: {self.config[option]}")

        return option_categories #NEWERRORNEEDED
    
    def is_valid_mask(self, mask): 
        valid_keyspaces = ["l", "u", "d", "h", "H", "s", "a", "b"]
        try:
            if mask == None or mask == "":
                raise MaskFormatError("Mask cannot be None or empty")
            
            if "?" not in mask:
                raise MaskFormatError("Mask must contain at least one ? character")
            
            if len(mask) <= 1:
                raise MaskFormatError("Mask must have at least two characters")
            
            for i in range(len(mask)):
                char = mask[i]
                if char == " ":
                    raise MaskFormatError("Mask cannot contain spaces")
                if char == "?":
                    if i < len(mask) - 1 and mask[i + 1] not in valid_keyspaces:
                        raise MaskFormatError("Invalid keyspace")
            return True #NEWERRORNEEDED
        except MaskFormatError as e:
            if self.config["debug_mode"] == True:
                print("[DEBUG] Mask Format Error: " + str(e))
            else:
                print("Invalid Mask: " + str(e))
            return False #NEWERRORNEEDED
         
    def get_config(self):
        with open("config.json", "r") as f:
            config = json.load(f)
        return config        

                
            
