from job_handler import STATUS
class ClientController:

    def __init__(self, job_handler):
        self.job_handler = job_handler


    def run(self):
        self.print_welcome()
        while True:
            self.job_handler.check_for_response()
            user_input = input("\nCloudCrack > ")
            user_input.strip()
            input_as_list = user_input.split(" ")

            if input_as_list[0] == "help":
                self.print_help()
            elif input_as_list[0] in ["exit", "close", "quit"]:
                self.job_handler.cancel_all_jobs()
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
                job_id = int(input("Job ID: "))
                try: 
                    self.job_handler.cancel_job(job_id)
                except:
                    print("Invalid Job ID")
        

    def print_welcome(self):
        print("ASCII Art Goes Here")
        print("Welcome to Cloud Crack")
        print("Type 'help' for a list of commands")

    def print_help(self):
        print("\nhelp - print this message")
        print("exit - exit the program")
        print("list - list all jobs")
        print("create - create a new job")
        print("cancel - cancel a job")

    
    def show_current_jobs(self):
        print("Current Jobs:")
        for job in self.job_handler.job_log.values():
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            if job.job_status == STATUS.RUNNING:
                print("Progress: " + str((job.progress[0] / job.progress[1])) + "%")
            elif job.job_status == STATUS.COMPLETED:
                print("Result: " + job.required_info)
            print("---------------------------------")

    def show_current_job(self, job_id):
        try:
            job = self.job_handler.job_log[job_id]
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job.hash)
            print("Status: " + job.job_status.name)
            print("Progress: " + str((job.progress[0] / job.progress[1])) + "%")
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

            if input_as_list[0].lower() == "options" or input_as_list[0].lower() == "help":
                print("Options:")
                print("Hash: " + _hash)
                print("Hash Type: " + hash_type)
                print("Attack Mode: " + attack_mode)
                print("Mask: " + mask)
                print("Dictionary: " + dictionary)
                print("Output File (Optional): " + output_file)
                print("Hash File Location (Optional): " + hash_file_location)

            if input_as_list[0].lower() == "set":
                if input_as_list[1].lower() == "hash":
                    _hash = input_as_list[2].strip()
                elif input_as_list[1].lower() == "hash_type":
                    hash_type = input_as_list[2].strip()
                elif input_as_list[1].lower() == "attack_mode":
                    attack_mode = input_as_list[2].strip()
                elif input_as_list[1].lower() == "mask":
                    mask = input_as_list[2].strip()
                elif input_as_list[1].lower() == "dictionary":
                    dictionary = input_as_list[2].strip()

            if input_as_list[0].lower() in ["run", "start", "create"]:
                if dictionary == "" and attack_mode == "0":
                    print("You must provide a dictionary for attack mode 0")
                    continue
                if mask == "" and attack_mode == "3":
                    print("You must provide a mask for attack mode 3")
                    continue
                if hash == "" and hash_file_location == "":
                    print("You must provide a hash OR hash file location")
                    continue
                if hash_type == "":
                    print("You must provide a hash type")
                    continue
                if attack_mode == "":
                    print("You must provide an attack mode")
                    continue
                
                if dictionary != "":
                    required_info = dictionary
                elif mask != "":
                    required_info = mask
                
                if hash_file_location != "":
                    try:
                        with open(hash_file_location, "r") as file:
                            pass
                    except:
                        print("Failed to open hash file. Please check the file location and try again")
                        continue

                    with open(hash_file_location, "r") as file:
                        hashes = file.readlines()
                    for _hash in hashes:
                        _hash = _hash.strip(" ")
                        _hash = _hash.strip("\n")
                        try: 
                            jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                            self.job_handler.send_job(jb)
                        except:
                            print("Failed to create job") # DEBUG
                            continue
                else:
                    jb = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                    self.job_handler.send_job(jb)

                

            if input_as_list == "clear":
                _hash = ""
                hash_type = ""
                attack_mode = ""
                mask = ""
                dictionary = ""
                output_file = ""
                hash_file_location = ""

        return
    
        



        