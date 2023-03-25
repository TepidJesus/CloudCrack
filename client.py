class ClientController:

    def __init__(self, job_handler):
        self.job_handler = job_handler

    def wait_for_user_input(self):
        self.print_welcome()
        while True:
            user_input = input("\nCloudCrack > ")
            if user_input == "help":
                self.print_help()
            elif user_input == "exit":
                self.job_handler.cancel_all_jobs()
                break
            elif user_input == "list":
                self.print_list(self.job_handler.job_log.values())
            elif user_input == "create":
                _hash, hash_type, attack_mode, required_info = self.print_create()
                job = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                self.job_handler.send_job(job)
            elif user_input == "cancel":
                job_id = int(input("Job ID: "))
                self.job_handler.cancel_job(job_id)
        

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

    def print_list(self, jobs):
        print("\nJobs:")
        for job in jobs:
            print(job)

    def print_create(self):
        user_input = ""
        while user_input != "back":
            user_input = input("\nCloudCrack > Create > ")
            if user_input == "options" or user_input == "help":
                print("\nOptions:")
                print("hash - the hash to crack")
                print("hash_type - the type of hash (md5, sha1, sha256, etc.)")
                print("attack_mode - the attack mode to use (brute_force, dictionary, etc.)")
                print("mask - The mask to use for a mask attack")
                print("dictionary - The file location of the dictionary you want to use")
                print("back - go back to the main menu")
                print("run - run the job")
            if user_input[0:5] == "hash ":
                _hash = user_input[5:].strip()
                print("Hash set to " + _hash)
            if user_input[0:10] == "hash_type ": 
                hash_type = user_input[10:].strip()
            if user_input[0:12] == "attack_mode ":
                attack_mode = user_input[12:].strip()
            if user_input[0:5] == "mask ":
                mask = user_input[5:].strip()
            if user_input[0:11] == "dictionary ": 
                dictionary = user_input[11:].strip()
            if user_input == "run":
                if mask != None:
                    required_info = mask
                elif dictionary != None:
                    required_info = dictionary
                else:
                    raise Exception("No mask or dictionary provided")
                self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
        

        

    
controller = ClientController(None)
controller.wait_for_user_input()
    
        



        