#!/usr/bin/env python3
"""
Cloud Cost Guardian - A CLI tool to monitor and optimize AWS cloud costs.
"""

import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich import box
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

console = Console()

class CloudCostGuardian:
    """Main class for the Cloud Cost Guardian tool."""
    
    def __init__(self, region=None, profile=None):
        """Initialize the Cloud Cost Guardian with AWS clients."""
        try:
            # Use specified profile if provided
            session_kwargs = {}
            if profile:
                session_kwargs['profile_name'] = profile
            if region:
                session_kwargs['region_name'] = region
                
            session = boto3.Session(**session_kwargs)
            
            # Get the region from the session if not specified
            if not region:
                region = session.region_name
                
            self.ce_client = session.client('ce')
            self.ec2_client = session.client('ec2')
            self.rds_client = session.client('rds')
            self.s3_client = session.client('s3')
            
            # Set up date ranges for queries
            self.today = datetime.datetime.now()
            self.first_day_month = self.today.replace(day=1).strftime('%Y-%m-%d')
            self.today_str = self.today.strftime('%Y-%m-%d')
            
            # Calculate the end of the month for forecasts
            next_month = self.today.replace(day=28) + datetime.timedelta(days=4)
            self.end_of_month = next_month.replace(day=1) - datetime.timedelta(days=1)
            self.end_of_month_str = self.end_of_month.strftime('%Y-%m-%d')
            
            # Load configuration
            self.config = self._load_config()
            
        except NoCredentialsError:
            console.print("[bold red]Error: AWS credentials not found.[/bold red]")
            console.print("Please run 'aws configure' to set up your credentials.")
            sys.exit(1)
        except PartialCredentialsError:
            console.print("[bold red]Error: Incomplete AWS credentials.[/bold red]")
            console.print("Please run 'aws configure' to set up your credentials properly.")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red]Error initializing AWS clients: {str(e)}[/bold red]")
            sys.exit(1)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json file."""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                # Return default config
                return {
                    "budget_alerts": {
                        "enabled": True,
                        "threshold_percentage": 80,
                        "notification_email": ""
                    },
                    "optimization": {
                        "idle_resource_threshold_days": 7,
                        "auto_cleanup": False
                    },
                    "reporting": {
                        "daily_summary": False,
                        "weekly_summary": True
                    }
                }
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load config file: {str(e)}[/yellow]")
            console.print("[yellow]Using default configuration.[/yellow]")
            return {}
    
    def get_month_to_date_cost(self) -> Dict[str, Any]:
        """Get the month-to-date cost for all services."""
        try:
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': self.first_day_month,
                    'End': self.today_str
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'AccessDeniedException':
                console.print("[bold red]Error: You don't have permission to access AWS Cost Explorer.[/bold red]")
                console.print("Make sure your IAM user or role has the 'ce:GetCostAndUsage' permission.")
            else:
                console.print(f"[bold red]AWS Error ({error_code}): {error_message}[/bold red]")
            
            return {}
    
    def get_cost_forecast(self) -> Dict[str, Any]:
        """Get cost forecast for the current month."""
        try:
            response = self.ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': self.today_str,
                    'End': self.end_of_month_str
                },
                Metric='UNBLENDED_COST',
                Granularity='MONTHLY'
            )
            return response
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'AccessDeniedException':
                console.print("[bold red]Error: You don't have permission to access AWS Cost Explorer forecasts.[/bold red]")
                console.print("Make sure your IAM user or role has the 'ce:GetCostForecast' permission.")
            else:
                console.print(f"[bold red]AWS Error ({error_code}): {error_message}[/bold red]")
            
            return {}
    
    def get_idle_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identify potentially idle or underutilized resources."""
        idle_resources = {
            'ec2_instances': [],
            'ebs_volumes': [],
            'rds_instances': []
        }
        
        with Progress() as progress:
            ec2_task = progress.add_task("[cyan]Checking EC2 instances...", total=1)
            ebs_task = progress.add_task("[cyan]Checking EBS volumes...", total=1)
            rds_task = progress.add_task("[cyan]Checking RDS instances...", total=1)
            
            # Find stopped EC2 instances
            try:
                ec2_response = self.ec2_client.describe_instances(
                    Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}]
                )
                
                for reservation in ec2_response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        # Get instance name from tags
                        instance_name = "Unnamed"
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                                break
                        
                        # Calculate how long the instance has been stopped
                        stopped_since = "Unknown"
                        if 'StateTransitionReason' in instance:
                            reason = instance['StateTransitionReason']
                            if reason.startswith('User initiated'):
                                # Extract date from the reason string if possible
                                try:
                                    date_str = reason.split('(')[1].split(')')[0]
                                    stopped_since = date_str
                                except:
                                    pass
                        
                        idle_resources['ec2_instances'].append({
                            'id': instance['InstanceId'],
                            'name': instance_name,
                            'type': instance['InstanceType'],
                            'state': 'stopped',
                            'stopped_since': stopped_since
                        })
                
                progress.update(ec2_task, completed=1)
            except ClientError as e:
                console.print(f"[bold red]Error getting EC2 instances: {e}[/bold red]")
                progress.update(ec2_task, completed=1)
            
            # Find unattached EBS volumes
            try:
                ebs_response = self.ec2_client.describe_volumes(
                    Filters=[{'Name': 'status', 'Values': ['available']}]
                )
                
                for volume in ebs_response.get('Volumes', []):
                    # Get volume name from tags
                    volume_name = "Unnamed"
                    for tag in volume.get('Tags', []):
                        if tag['Key'] == 'Name':
                            volume_name = tag['Value']
                            break
                    
                    idle_resources['ebs_volumes'].append({
                        'id': volume['VolumeId'],
                        'name': volume_name,
                        'size': volume['Size'],
                        'type': volume['VolumeType'],
                        'created': volume['CreateTime'].strftime('%Y-%m-%d')
                    })
                
                progress.update(ebs_task, completed=1)
            except ClientError as e:
                console.print(f"[bold red]Error getting EBS volumes: {e}[/bold red]")
                progress.update(ebs_task, completed=1)
            
            # Find idle RDS instances
            try:
                rds_response = self.rds_client.describe_db_instances()
                
                for instance in rds_response.get('DBInstances', []):
                    # Check if the instance is available but has low connections
                    if instance['DBInstanceStatus'] == 'available':
                        idle_resources['rds_instances'].append({
                            'id': instance['DBInstanceIdentifier'],
                            'type': instance['DBInstanceClass'],
                            'engine': instance['Engine'],
                            'state': instance['DBInstanceStatus']
                        })
                
                progress.update(rds_task, completed=1)
            except ClientError as e:
                console.print(f"[bold red]Error getting RDS instances: {e}[/bold red]")
                progress.update(rds_task, completed=1)
        
        return idle_resources
    
    def display_cost_overview(self):
        """Display an overview of the current month's costs."""
        with console.status("[bold green]Fetching cost data from AWS..."):
            cost_data = self.get_month_to_date_cost()
            forecast_data = self.get_cost_forecast()
        
        if not cost_data or 'ResultsByTime' not in cost_data or not cost_data['ResultsByTime']:
            console.print("[bold red]No cost data available.[/bold red]")
            console.print("This could be due to insufficient permissions or because Cost Explorer is not enabled.")
            console.print("To enable Cost Explorer, visit: https://console.aws.amazon.com/cost-management/home")
            return
        
        # Extract the total cost
        total_cost = 0
        for group in cost_data['ResultsByTime'][0]['Groups']:
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            total_cost += amount
        
        # Get the forecast
        forecast_amount = 0
        if forecast_data and 'Total' in forecast_data:
            forecast_amount = float(forecast_data['Total']['Amount'])
        
        # Calculate the projected total
        projected_total = total_cost + forecast_amount
        
        # Create a table for the cost overview
        table = Table(title="AWS Cost Overview", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Amount (USD)", style="green")
        
        table.add_row("Month-to-Date Spend", f"${total_cost:.2f}")
        table.add_row("Forecasted Additional Spend", f"${forecast_amount:.2f}")
        table.add_row("Projected Monthly Total", f"${projected_total:.2f}")
        
        console.print(table)
        
        # Create a table for service breakdown
        service_table = Table(title="Cost Breakdown by Service", box=box.ROUNDED)
        service_table.add_column("Service", style="cyan")
        service_table.add_column("Cost (USD)", style="green")
        service_table.add_column("Percentage", style="yellow")
        
        # Sort services by cost
        services = sorted(
            cost_data['ResultsByTime'][0]['Groups'],
            key=lambda x: float(x['Metrics']['UnblendedCost']['Amount']),
            reverse=True
        )
        
        # Display top 10 services
        for group in services[:10]:
            service_name = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            percentage = (amount / total_cost) * 100 if total_cost > 0 else 0
            service_table.add_row(service_name, f"${amount:.2f}", f"{percentage:.1f}%")
        
        console.print(service_table)
    
    def display_optimization_recommendations(self):
        """Display cost optimization recommendations."""
        with console.status("[bold green]Analyzing resources for optimization opportunities..."):
            idle_resources = self.get_idle_resources()
        
        console.print(Panel("[bold]Cost Optimization Recommendations[/bold]", style="blue"))
        
        # EC2 Recommendations
        if idle_resources['ec2_instances']:
            ec2_table = Table(title="Stopped EC2 Instances", box=box.ROUNDED)
            ec2_table.add_column("Instance ID", style="cyan")
            ec2_table.add_column("Name", style="blue")
            ec2_table.add_column("Type", style="green")
            ec2_table.add_column("State", style="yellow")
            ec2_table.add_column("Stopped Since", style="magenta")
            
            for instance in idle_resources['ec2_instances']:
                ec2_table.add_row(
                    instance['id'],
                    instance['name'],
                    instance['type'],
                    instance['state'],
                    instance['stopped_since']
                )
            
            console.print(ec2_table)
            
            # Calculate potential savings (rough estimate)
            savings = 0
            for instance in idle_resources['ec2_instances']:
                # Very rough estimate based on instance type
                instance_type = instance['type']
                hourly_rate = 0.05  # Default estimate
                
                if instance_type.startswith('t2.'):
                    hourly_rate = 0.02
                elif instance_type.startswith('t3.'):
                    hourly_rate = 0.03
                elif instance_type.startswith('m5.'):
                    hourly_rate = 0.1
                elif instance_type.startswith('c5.'):
                    hourly_rate = 0.12
                
                savings += hourly_rate * 24 * 30  # Monthly cost
            
            console.print(f"[bold green]Potential monthly savings:[/bold green] ${savings:.2f}")
            console.print("[bold green]Recommendation:[/bold green] Consider terminating these instances if they are no longer needed.")
            console.print("Command to terminate an instance: [cyan]aws ec2 terminate-instances --instance-ids <instance-id>[/cyan]")
        else:
            console.print("[green]No stopped EC2 instances found.[/green]")
        
        # EBS Recommendations
        if idle_resources['ebs_volumes']:
            ebs_table = Table(title="Unattached EBS Volumes", box=box.ROUNDED)
            ebs_table.add_column("Volume ID", style="cyan")
            ebs_table.add_column("Name", style="blue")
            ebs_table.add_column("Size (GB)", style="green")
            ebs_table.add_column("Type", style="yellow")
            ebs_table.add_column("Created", style="magenta")
            
            for volume in idle_resources['ebs_volumes']:
                ebs_table.add_row(
                    volume['id'],
                    volume['name'],
                    str(volume['size']),
                    volume['type'],
                    volume['created']
                )
            
            console.print(ebs_table)
            
            # Calculate potential savings
            savings = 0
            for volume in idle_resources['ebs_volumes']:
                # Rough estimate based on volume type and size
                volume_type = volume['type']
                size = volume['size']
                
                if volume_type == 'gp2':
                    savings += size * 0.10  # $0.10 per GB-month
                elif volume_type == 'gp3':
                    savings += size * 0.08  # $0.08 per GB-month
                elif volume_type == 'io1':
                    savings += size * 0.125  # $0.125 per GB-month
                else:
                    savings += size * 0.05  # Default estimate
            
            console.print(f"[bold green]Potential monthly savings:[/bold green] ${savings:.2f}")
            console.print("[bold green]Recommendation:[/bold green] Delete these unattached volumes to save on storage costs.")
            console.print("Command to delete a volume: [cyan]aws ec2 delete-volume --volume-id <volume-id>[/cyan]")
        else:
            console.print("[green]No unattached EBS volumes found.[/green]")
        
        # RDS Recommendations
        if idle_resources['rds_instances']:
            rds_table = Table(title="RDS Instances to Review", box=box.ROUNDED)
            rds_table.add_column("Instance ID", style="cyan")
            rds_table.add_column("Type", style="green")
            rds_table.add_column("Engine", style="yellow")
            rds_table.add_column("State", style="magenta")
            
            for instance in idle_resources['rds_instances']:
                rds_table.add_row(
                    instance['id'],
                    instance['type'],
                    instance['engine'],
                    instance['state']
                )
            
            console.print(rds_table)
            console.print("[bold green]Recommendation:[/bold green] Review these RDS instances for utilization and consider downsizing if they are underutilized.")
        else:
            console.print("[green]No RDS instances found for review.[/green]")
        
        # General recommendations
        console.print("\n[bold]General Cost Optimization Tips:[/bold]")
        console.print("• Consider using Reserved Instances for steady-state workloads")
        console.print("• Implement auto-scaling for variable workloads")
        console.print("• Use Spot Instances for fault-tolerant, flexible workloads")
        console.print("• Implement lifecycle policies for S3 to move data to cheaper storage tiers")
        console.print("• Enable S3 Intelligent Tiering for objects with unknown access patterns")

    def check_cost_anomalies(self):
        """Check for cost anomalies in your AWS account."""
        try:
            # Get cost data for the last 30 days
            end_date = self.today
            start_date = end_date - datetime.timedelta(days=30)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            
            if not response or 'ResultsByTime' not in response:
                console.print("[bold red]No cost data available for anomaly detection.[/bold red]")
                return
            
            # Process the data to find anomalies
            service_costs = {}
            
            for day_data in response['ResultsByTime']:
                date = day_data['TimePeriod']['Start']
                
                for group in day_data['Groups']:
                    service = group['Keys'][0]
                    amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    
                    if service not in service_costs:
                        service_costs[service] = []
                    
                    service_costs[service].append((date, amount))
            
            # Find services with significant cost increases
            anomalies = []
            
            for service, costs in service_costs.items():
                if len(costs) < 2:
                    continue
                
                # Calculate the average cost for the first 20 days
                baseline_costs = costs[:-10] if len(costs) > 10 else costs[:-1]
                if not baseline_costs:
                    continue
                
                baseline_avg = sum(cost for _, cost in baseline_costs) / len(baseline_costs)
                
                # Check the most recent days for anomalies
                recent_costs = costs[-10:] if len(costs) > 10 else costs[-1:]
                
                for date, cost in recent_costs:
                    if baseline_avg > 0 and cost > baseline_avg * 1.5:  # 50% increase
                        percent_increase = ((cost - baseline_avg) / baseline_avg) * 100
                        anomalies.append({
                            'service': service,
                            'date': date,
                            'cost': cost,
                            'baseline': baseline_avg,
                            'increase': percent_increase
                        })
            
            # Display anomalies
            if anomalies:
                anomaly_table = Table(title="Cost Anomalies Detected", box=box.ROUNDED)
                anomaly_table.add_column("Service", style="cyan")
                anomaly_table.add_column("Date", style="green")
                anomaly_table.add_column("Cost (USD)", style="yellow")
                anomaly_table.add_column("Baseline (USD)", style="blue")
                anomaly_table.add_column("Increase", style="red")
                
                for anomaly in sorted(anomalies, key=lambda x: x['increase'], reverse=True):
                    anomaly_table.add_row(
                        anomaly['service'],
                        anomaly['date'],
                        f"${anomaly['cost']:.2f}",
                        f"${anomaly['baseline']:.2f}",
                        f"{anomaly['increase']:.1f}%"
                    )
                
                console.print(anomaly_table)
                console.print("[bold yellow]Recommendation:[/bold yellow] Investigate these services for unexpected usage or potential optimization opportunities.")
            else:
                console.print("[green]No significant cost anomalies detected in the last 30 days.[/green]")
                
        except ClientError as e:
            console.print(f"[bold red]Error checking for cost anomalies: {e}[/bold red]")

    def cleanup_resources(self, dry_run=True):
        """Run automated cleanup of unused resources."""
        with console.status("[bold green]Identifying resources for cleanup..."):
            idle_resources = self.get_idle_resources()
        
        if dry_run:
            console.print(Panel("[bold yellow]DRY RUN MODE[/bold yellow] - No resources will be modified", style="yellow"))
        
        # Process EC2 instances
        if idle_resources['ec2_instances']:
            console.print("\n[bold]Stopped EC2 Instances:[/bold]")
            
            for instance in idle_resources['ec2_instances']:
                console.print(f"  • {instance['id']} ({instance['name']}) - {instance['type']} - Stopped since: {instance['stopped_since']}")
            
            if not dry_run:
                console.print("\n[bold yellow]Do you want to terminate these instances? (y/n)[/bold yellow]")
                choice = input().lower()
                
                if choice == 'y':
                    instance_ids = [instance['id'] for instance in idle_resources['ec2_instances']]
                    try:
                        response = self.ec2_client.terminate_instances(InstanceIds=instance_ids)
                        console.print("[bold green]Instances terminated successfully.[/bold green]")
                    except ClientError as e:
                        console.print(f"[bold red]Error terminating instances: {e}[/bold red]")
        else:
            console.print("[green]No stopped EC2 instances found for cleanup.[/green]")
        
        # Process EBS volumes
        if idle_resources['ebs_volumes']:
            console.print("\n[bold]Unattached EBS Volumes:[/bold]")
            
            for volume in idle_resources['ebs_volumes']:
                console.print(f"  • {volume['id']} ({volume['name']}) - {volume['size']} GB - Created: {volume['created']}")
            
            if not dry_run:
                console.print("\n[bold yellow]Do you want to delete these volumes? (y/n)[/bold yellow]")
                choice = input().lower()
                
                if choice == 'y':
                    for volume in idle_resources['ebs_volumes']:
                        try:
                            self.ec2_client.delete_volume(VolumeId=volume['id'])
                            console.print(f"[green]Deleted volume {volume['id']}[/green]")
                        except ClientError as e:
                            console.print(f"[bold red]Error deleting volume {volume['id']}: {e}[/bold red]")
        else:
            console.print("[green]No unattached EBS volumes found for cleanup.[/green]")


@click.group()
def cli():
    """Cloud Cost Guardian - Monitor and optimize your AWS cloud costs."""
    pass


@cli.command()
@click.option('--region', '-r', help='AWS region to use')
@click.option('--profile', '-p', help='AWS profile to use')
def overview(region, profile):
    """Display an overview of your current AWS spending."""
    guardian = CloudCostGuardian(region=region, profile=profile)
    guardian.display_cost_overview()


@cli.command()
@click.option('--region', '-r', help='AWS region to use')
@click.option('--profile', '-p', help='AWS profile to use')
def optimize(region, profile):
    """Get recommendations for cost optimization."""
    guardian = CloudCostGuardian(region=region, profile=profile)
    guardian.display_optimization_recommendations()


@cli.command()
@click.option('--region', '-r', help='AWS region to use')
@click.option('--profile', '-p', help='AWS profile to use')
def anomalies(region, profile):
    """Check for cost anomalies in your AWS account."""
    guardian = CloudCostGuardian(region=region, profile=profile)
    guardian.check_cost_anomalies()


@cli.command()
@click.option('--dry-run', is_flag=True, default=True, help='Run in dry-run mode without making changes')
@click.option('--region', '-r', help='AWS region to use')
@click.option('--profile', '-p', help='AWS profile to use')
def cleanup(dry_run, region, profile):
    """Run automated cleanup of unused resources."""
    guardian = CloudCostGuardian(region=region, profile=profile)
    guardian.cleanup_resources(dry_run=dry_run)


if __name__ == "__main__":
    cli()
