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
        print("\nCreate Job:")
        _hash = input("Hash: ")
        hash_type = input("Hash Type: ")
        attack_mode = input("Attack Mode: ")
        required_info = input("Required Info: ")
        return _hash, hash_type, attack_mode, required_info
    
controller = ClientController(None)
controller.wait_for_user_input()
    
        



        