# CloudCrack

[![LinkedIn](https://img.shields.io/badge/Connect%20on-LinkedIn-blue.svg)](https://www.linkedin.com/in/thomasholdom/)

             _______  ___      _______  __   __  ______   _______  ______    _______  _______  ___   _ 
            |       ||   |    |       ||  | |  ||      | |       ||    _ |  |   _   ||       ||   | | |
            |       ||   |    |   _   ||  | |  ||  _    ||       ||   | ||  |  |_|  ||       ||   |_| |
            |       ||   |    |  | |  ||  |_|  || | |   ||       ||   |_||_ |       ||       ||      _|
            |      _||   |___ |  |_|  ||       || |_|   ||      _||    __  ||       ||      _||     |_ 
            |     |_ |       ||       ||       ||       ||     |_ |   |  | ||   _   ||     |_ |    _  |
            |_______||_______||_______||_______||______| |_______||___|  |_||__| |__||_______||___| |_|


## About the Author

CloudCrack is developed and maintained by [Thomas Holdom](https://www.linkedin.com/in/thomasholdom/), a passionate Computer Science student at the University of Auckland with experience in penetration testing, cloud security and software development.

## Features

CloudCrack is a powerful CLI program that leverages AWS EC2 services to de-hash passwords at an effectively infinite scale, right from the command line. Key features include:

- **Scalable Password De-hashing**: Utilize the power of AWS EC2 services to perform password de-hashing on a massive scale, enabling quick retrieval of passwords on an near infinite scale.
- **Cost-Effective**: CloudCrack allows you to utilize AWS EC2 services without any upfront costs. However, please note that you are responsible for all AWS usage fees incurred.
- **AWS Account Requirement**: To use CloudCrack, you need an AWS account. Please ensure that you have an AWS account and have your vCPU limit lifted to at least 4 vCPUs for P type instances (See setup guide below).
- **Easy Setup**: CloudCrack provides step-by-step instructions to guide you through the setup process, including creating an AWS IAM user and entering the credentials into CloudCrack.
- **Zero Overhead**: The AWS infrastructure that supports CloudCrack runs entirely within the AWS Free-Tier. The only costs you pay for are directly related to the de-hashing of passwords.

## Setup

Follow the steps below to set up and run CloudCrack:

1. **Clone the repository:**

   ```shell
   git clone https://github.com/your-username/CloudCrack.git
   ```

2. **Install the required dependencies:**

   ```shell
   pip install -r requirements.txt
   ```

3. 

4. **Navigate to the IAM page of AWS and create a new IAM user with the following permissions:**  
Navigation: IAM > Users > Create User > Attach Policies Directly 
   - EC2FullAccess
   - S3FullAccess
   - SQSFullAccess
   - IAMFullAccess
   - ServiceQuotesReadOnlyAccess   


5. **Fetch the Access Key and Secret Key for the IAM User you just created:**  
Navigation: IAM > Users > Your_User > Security Credentials > Create Access Key > Other > Create Key  
Keep this window open, you will need these credentials when you start CloudCrack
6. **Navigate to your install location and launch CloudCrack and enter your AWS IAM user credentials when prompted:**

   ```shell
   python3 cloudcrack.py
   ```

## Future Development

The future development of CloudCrack will focus on the following areas:

- **Additional Cloud Providers**: Expanding support for other cloud providers, such as Azure and Google Cloud Platform, to offer users a wider range of options.
- **Enhanced Hashing Algorithms**: Adding support for more password hashing algorithms commonly used in various applications.
- **Improved User Experience**: Incorporating user feedback to enhance the usability, performance, and efficiency of CloudCrack.

We welcome contributions and suggestions from the community to make CloudCrack even better.

## Legal Disclaimer

CloudCrack is an educational tool intended to be used for legitimate purposes only. The developers of CloudCrack are not responsible for any illegal or unauthorized use of this software.