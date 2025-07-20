# Cloud Cost Guardian

A CLI automation tool that helps you monitor, analyze, and optimize your AWS cloud costs.

## Overview

Cloud Cost Guardian is a command-line tool that provides real-time insights into your AWS spending, detects cost anomalies, and suggests optimization opportunities. It helps you stay on top of your cloud expenses and avoid unexpected bills.

## Features

- **Real-time Cost Monitoring**: Track spending across all AWS services
- **Anomaly Detection**: Get alerts for unusual spending patterns
- **Resource Optimization**: Receive recommendations for cost-saving opportunities
- **Automated Actions**: Schedule and automate cost-saving measures
- **Budget Management**: Set up and track budgets for different projects
- **Tagging Compliance**: Enforce consistent tagging for better cost allocation
- **Cost-Aware Development**: Get recommendations for cost-efficient architectures

## Prerequisites

- Python 3.6 or higher
- AWS CLI installed and configured with appropriate permissions
- AWS Cost Explorer enabled in your account

## Required AWS Permissions

The tool requires the following AWS permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ce:GetCostAndUsage",
                "ce:GetCostForecast",
                "ec2:DescribeInstances",
                "ec2:DescribeVolumes",
                "rds:DescribeDBInstances",
                "s3:ListBuckets",
                "s3:GetBucketLifecycleConfiguration"
            ],
            "Resource": "*"
        }
    ]
}
```

For the cleanup functionality, additional permissions are required:

```json
{
    "Effect": "Allow",
    "Action": [
        "ec2:TerminateInstances",
        "ec2:DeleteVolume"
    ],
    "Resource": "*"
}
```

A complete IAM policy is provided in the `iam-policy.json` file.

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-cost-guardian.git
cd cloud-cost-guardian

# Run the installation script
./install.sh
```

The installation script will:
1. Check for required dependencies
2. Create a Python virtual environment
3. Install required packages
4. Create a symbolic link to make the tool available in your PATH

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-cost-guardian.git
cd cloud-cost-guardian

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x cost_guardian.py

# Create a symbolic link (optional)
ln -sf $(pwd)/cost-guardian ~/.local/bin/cost-guardian
```

## Usage

### Basic Commands

```bash
# Get an overview of your current AWS spending
cost-guardian overview

# Check for cost anomalies
cost-guardian anomalies

# Get optimization recommendations
cost-guardian optimize

# Run automated cleanup of unused resources (dry run mode)
cost-guardian cleanup

# Run actual cleanup (use with caution)
cost-guardian cleanup --dry-run=False
```

### Using with Different AWS Profiles and Regions

```bash
# Use a specific AWS profile
cost-guardian overview --profile my-profile

# Use a specific AWS region
cost-guardian optimize --region us-west-2

# Combine profile and region
cost-guardian anomalies --profile my-profile --region eu-west-1
```

### Demo Mode

If you want to see how the tool works without connecting to AWS:

```bash
./demo.py overview
./demo.py optimize
```

## Configuration

You can customize the tool's behavior by editing the `config.json` file:

```json
{
    "budget_alerts": {
        "enabled": true,
        "threshold_percentage": 80,
        "notification_email": "your-email@example.com"
    },
    "optimization": {
        "idle_resource_threshold_days": 7,
        "auto_cleanup": false
    },
    "reporting": {
        "daily_summary": false,
        "weekly_summary": true
    }
}
```

## Troubleshooting

### Common Issues

1. **"No cost data available"**
   - Make sure Cost Explorer is enabled in your AWS account
   - It may take up to 24 hours for Cost Explorer data to become available after enabling it
   - Check that your IAM user/role has the necessary permissions

2. **"AWS credentials not found"**
   - Run `aws configure` to set up your credentials
   - Check that your credentials are valid by running `aws sts get-caller-identity`

3. **"AccessDeniedException"**
   - Your IAM user/role doesn't have the required permissions
   - Add the permissions listed in the "Required AWS Permissions" section

4. **"ModuleNotFoundError"**
   - Make sure you've activated the virtual environment: `source venv/bin/activate`
   - Or use the provided wrapper script: `./cost-guardian`

## Development Status

This project was developed as part of the AWS Q Developer Challenge

## License

MIT
