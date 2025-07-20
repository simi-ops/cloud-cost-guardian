# Cloud Cost Guardian Documentation

## Overview

Cloud Cost Guardian is a CLI tool designed to help AWS users monitor, analyze, and optimize their cloud costs. It provides real-time insights into spending patterns, identifies cost-saving opportunities, and offers recommendations for resource optimization.

## Features

### 1. Cost Monitoring

The tool connects to AWS Cost Explorer API to provide:
- Current month-to-date spending
- Forecasted spending for the remainder of the month
- Breakdown of costs by service
- Historical spending trends

```bash
cost-guardian overview
```

This command displays:
- A summary table with month-to-date spend, forecasted additional spend, and projected monthly total
- A breakdown of costs by service, showing the top 10 services by cost
- Percentage of total cost for each service

### 2. Resource Optimization

Cloud Cost Guardian identifies resources that could be optimized:

```bash
cost-guardian optimize
```

This command analyzes:
- Stopped EC2 instances that could be terminated
- Unattached EBS volumes that could be deleted
- Underutilized RDS instances that could be downsized
- Idle Elastic IPs that are incurring charges

For each category, the tool provides:
- Details about the resources (IDs, types, states, etc.)
- Estimated potential monthly savings
- Recommendations for optimization
- AWS CLI commands to implement the recommendations

### 3. Anomaly Detection

The tool analyzes spending patterns to detect unusual changes:

```bash
cost-guardian anomalies
```

This command:
- Analyzes cost data for the last 30 days
- Establishes baseline spending for each service
- Identifies services with significant cost increases (>50% above baseline)
- Displays the date, cost, baseline, and percentage increase for each anomaly
- Provides recommendations for investigation

### 4. Resource Cleanup

Cloud Cost Guardian offers automated cleanup options:

```bash
cost-guardian cleanup
```

By default, this runs in dry-run mode, showing what would be cleaned up without making changes. To actually perform the cleanup:

```bash
cost-guardian cleanup --dry-run=False
```

The cleanup process:
1. Identifies resources that could be cleaned up (stopped EC2 instances, unattached EBS volumes)
2. Displays details about these resources
3. In non-dry-run mode, prompts for confirmation before taking action
4. Executes the cleanup actions (terminating instances, deleting volumes)
5. Reports on the success or failure of each action

## Installation

### Prerequisites

- Python 3.6 or higher
- AWS CLI configured with appropriate permissions
- Required Python packages (see requirements.txt)

### Setup

1. Clone the repository
2. Run `./install.sh` to set up the command-line tool

The installation script:
1. Checks for required dependencies (Python, AWS CLI)
2. Creates a Python virtual environment
3. Installs required packages
4. Creates a symbolic link to make the tool available in your PATH

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

### AWS Permissions

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

### Advanced Usage

#### Using with Different AWS Profiles and Regions

```bash
# Use a specific AWS profile
cost-guardian overview --profile my-profile

# Use a specific AWS region
cost-guardian optimize --region us-west-2

# Combine profile and region
cost-guardian anomalies --profile my-profile --region eu-west-1
```

#### Demo Mode

If you want to see how the tool works without connecting to AWS:

```bash
./demo.py overview
./demo.py optimize
```

### Configuration

The tool can be configured using the `config.json` file:

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

#### Configuration Options

- **budget_alerts**: Settings for budget alerts
  - **enabled**: Whether to enable budget alerts
  - **threshold_percentage**: Percentage of budget at which to send alerts
  - **notification_email**: Email address to send alerts to

- **optimization**: Settings for resource optimization
  - **idle_resource_threshold_days**: Number of days a resource must be idle before recommending cleanup
  - **auto_cleanup**: Whether to automatically clean up resources without prompting

- **reporting**: Settings for cost reporting
  - **daily_summary**: Whether to generate daily cost summaries
  - **weekly_summary**: Whether to generate weekly cost summaries

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

### Debugging

For more detailed output, you can run the tool with Python's debug mode:

```bash
python -m pdb cost_guardian.py overview
```

## Development

### Project Structure

- **cost_guardian.py**: Main script with the core functionality
- **demo.py**: Demo version that uses simulated data
- **cost-guardian**: Wrapper script for easy execution
- **config.json**: Configuration file
- **requirements.txt**: Python dependencies
- **install.sh**: Installation script
- **iam-policy.json**: IAM policy for required permissions
- **generate_screenshots.sh**: Script to generate screenshots for documentation

### Adding New Features

To add a new feature:

1. Create a new method in the `CloudCostGuardian` class
2. Add a new command to the Click CLI interface
3. Update the documentation to reflect the new feature

### Running Tests

To run tests:

```bash
# Activate the virtual environment
source venv/bin/activate

# Run tests
python -m unittest discover tests
```

## Development Roadmap

1. **Current Version (1.0)**
   - Basic cost monitoring
   - Resource optimization recommendations
   - Anomaly detection
   - Resource cleanup

2. **Version 1.1**
   - Email reporting
   - Scheduled execution
   - More detailed cost analysis

3. **Version 2.0**
   - Integration with Slack/Teams for notifications
   - Custom dashboards
   - Multi-account support
   - Cost allocation by tags/projects

## License

MIT
