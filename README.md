# CloudCrack

[![LinkedIn](https://img.shields.io/badge/Connect%20on-LinkedIn-blue.svg)](https://www.linkedin.com/in/thomasholdom/)
[![Stars](https://img.shields.io/github/stars/username/repo.svg)](https://github.com/TepidJesus/CloudCrack/stargazers)

             _______  ___      _______  __   __  ______   _______  ______    _______  _______  ___   _ 
            |       ||   |    |       ||  | |  ||      | |       ||    _ |  |   _   ||       ||   | | |
            |       ||   |    |   _   ||  | |  ||  _    ||       ||   | ||  |  |_|  ||       ||   |_| |
            |       ||   |    |  | |  ||  |_|  || | |   ||       ||   |_||_ |       ||       ||      _|
            |      _||   |___ |  |_|  ||       || |_|   ||      _||    __  ||       ||      _||     |_ 
            |     |_ |       ||       ||       ||       ||     |_ |   |  | ||   _   ||     |_ |    _  |
            |_______||_______||_______||_______||______| |_______||___|  |_||__| |__||_______||___| |_| v0.1


## Features

CloudCrack is a powerful CLI program that leverages AWS EC2 services to de-hash passwords at an effectively infinite scale, right from the command line. Key features include:

- **Scalable Password De-hashing**: Utilize the power of AWS EC2 services to perform password de-hashing on a massive scale, enabling quick retrieval of acquired from engagements.
- **Cost-Effective**: CloudCrack allows you to utilize AWS EC2 services without any upfront costs. However, please note that you are responsible for all AWS usage fees incurred.
- **Zero Overhead**: The AWS infrastructure that supports CloudCrack runs entirely within the AWS Free-Tier. The only costs you pay for are directly related to the de-hashing of passwords.
- **AWS Account Requirement**: CloudCrack runs entirely within your own AWS account. Please ensure that you have an AWS account already setup.
- **Easy Setup**: CloudCrack provides step-by-step instructions to guide you through the setup process, including creating an AWS IAM user and applying for higher vCPU limits.
- **User Friendly Design**: CloudCrack has been built from the ground up to make large-scale password recovery easy and intuitive. Errors are handled gracefully and verbosely and in many cases handled before affecting you.

## Setup

Follow the steps below to set up and run CloudCrack:

1. **Clone the repository:**

   ```shell
   git clone https://github.com/TepidJesus/CloudCrack.git
   ```
      ```shell
   cd /CloudCrack/
   ```

2. **Install the required dependencies:**

   ```shell
   pip install -r requirements.txt
   ```

3. **Apply For P-Instance Quota increase using AWS Service Quota menu:**  
As CloudCrack runs entirely on your AWS account you need to apply for an increase in your P-Instance vCPU allowance. If you've never applied for an increase before a good place to start is 8 vCPU's, as this will likely be accepted. If you are a frequent AWS user and routinely have a high active vCPU count you can apply for much greater limits. CloudCrack will work with any limit greater than 4 vCPU's.
**[Apply Here](https://us-east-2.console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-417A185B)**


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

- **Better Hashcat Integration**: Expanding support for HashCat features such as more advanced mask options and niche attack modes.
- **Live Progress Updates**: Adding support for auto-refresh of job progress and other QoL UI improvements.
- **Improved User Experience**: Incorporating user feedback to enhance the usability, performance, and efficiency of CloudCrack. This will also include more verbose error handling and recovery methods.

We welcome contributions and suggestions from the community to make CloudCrack even better.

## About the Author

CloudCrack is developed and maintained by [Thomas Holdom](https://www.linkedin.com/in/thomasholdom/), a passionate Computer Science and Commerce student at the University of Auckland with experience in penetration testing, cloud security and software development.


## Legal Disclaimer

CloudCrack is an educational tool intended to be used for legitimate purposes only. The developers of CloudCrack are not responsible for any illegal or unauthorized use of this software.