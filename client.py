import alive_progress as alive
class ClientController:

    def __init__(self, job_handler):
        self.job_handler = job_handler

    def wait_for_user_input(self):
        self.print_welcome()
        while True:
            user_input = input("\nCloudCrack > ")
            user_input.strip()
            input_as_list = user_input.split(" ")

            if input_as_list[0] == "help":
                self.print_help()
            elif input_as_list[0] == "exit":
                self.job_handler.cancel_all_jobs()
                break
            elif input_as_list[0] == "show":
                if input_as_list[1] == "all":
                    self.show_current_jobs()
                else:
                    try:
                        job_id = int(input_as_list[1])
                        self.show_current_job(job_id)
                    except:
                        print("Invalid Job ID")
            elif input_as_list[0] == "create":
                _hash, hash_type, attack_mode, required_info = self.print_create()
                job = self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
                self.job_handler.send_job(job)
            elif input_as_list[0] == "cancel":
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

    
    def show_current_jobs(self):
        print("Current Jobs:\ns")
        for job in self.job_handler.job_log.values():
            print("\n---------------------------------")
            print("Job ID: " + str(job.job_id))
            print("Hash: " + job._hash)
            print("Status: " + job.status)
            print("Progress: " + str((job.progress[0] / job.progress[1])) + "%")
            print("---------------------------------")

    def show_current_job(self, job_id):
        try:
            job = self.job_handler.job_log[job_id]
            with alive.alive_bar(total=job.progress[1], stats="{rate}, ETA: {eta}") as bar:
                while True:
                    
        except:
            raise Exception("Invalid Job ID")

            
       
    def show_create_screen(self):
        user_input = ""
        _hash = ""
        hash_type = ""
        attack_mode = ""
        mask = ""
        dictionary = ""
        
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
                if mask != None:
                    required_info = mask
                elif dictionary != None:
                    required_info = dictionary
                else:
                    raise Exception("No mask or dictionary provided")
                self.job_handler.create_job(_hash, hash_type, attack_mode, required_info)
            if input_as_list == "clear":
                _hash = ""
                hash_type = ""
                attack_mode = ""
                mask = ""
                dictionary = ""
        return
        

        

    
controller = ClientController(None)
controller.wait_for_user_input()
    
        



        