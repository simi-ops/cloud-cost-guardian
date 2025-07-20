#!/usr/bin/env python3
"""
Cloud Cost Guardian Demo - Simulates the functionality without requiring AWS credentials.
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
from rich import box

console = Console()

class CloudCostGuardianDemo:
    """Demo class for the Cloud Cost Guardian tool."""
    
    def __init__(self):
        """Initialize the Cloud Cost Guardian Demo."""
        self.today = datetime.datetime.now()
        self.first_day_month = self.today.replace(day=1).strftime('%Y-%m-%d')
        self.today_str = self.today.strftime('%Y-%m-%d')
        
        # Mock data
        self.mock_cost_data = {
            'ResultsByTime': [
                {
                    'TimePeriod': {
                        'Start': self.first_day_month,
                        'End': self.today_str
                    },
                    'Groups': [
                        {
                            'Keys': ['Amazon Elastic Compute Cloud - Compute'],
                            'Metrics': {'UnblendedCost': {'Amount': '156.78', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon Relational Database Service'],
                            'Metrics': {'UnblendedCost': {'Amount': '89.32', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon Simple Storage Service'],
                            'Metrics': {'UnblendedCost': {'Amount': '45.67', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['AWS Lambda'],
                            'Metrics': {'UnblendedCost': {'Amount': '23.45', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon CloudFront'],
                            'Metrics': {'UnblendedCost': {'Amount': '18.90', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['AWS Data Transfer'],
                            'Metrics': {'UnblendedCost': {'Amount': '12.34', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon DynamoDB'],
                            'Metrics': {'UnblendedCost': {'Amount': '9.87', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon ElastiCache'],
                            'Metrics': {'UnblendedCost': {'Amount': '7.65', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['Amazon Route 53'],
                            'Metrics': {'UnblendedCost': {'Amount': '4.32', 'Unit': 'USD'}}
                        },
                        {
                            'Keys': ['AWS Key Management Service'],
                            'Metrics': {'UnblendedCost': {'Amount': '2.10', 'Unit': 'USD'}}
                        }
                    ]
                }
            ]
        }
        
        self.mock_forecast_data = {
            'Total': {
                'Amount': '145.67',
                'Unit': 'USD'
            }
        }
        
        self.mock_idle_resources = {
            'ec2_instances': [
                {
                    'id': 'i-0abc123def456789',
                    'type': 't3.medium',
                    'state': 'stopped',
                    'stopped_since': '2023-07-10'
                },
                {
                    'id': 'i-0123456789abcdef',
                    'type': 'm5.large',
                    'state': 'stopped',
                    'stopped_since': '2023-07-05'
                }
            ],
            'ebs_volumes': [
                {
                    'id': 'vol-0abc123def456789',
                    'size': 100,
                    'type': 'gp2',
                    'created': '2023-06-15'
                },
                {
                    'id': 'vol-0123456789abcdef',
                    'size': 50,
                    'type': 'gp3',
                    'created': '2023-06-20'
                },
                {
                    'id': 'vol-9876543210fedcba',
                    'size': 200,
                    'type': 'io1',
                    'created': '2023-05-10'
                }
            ],
            'rds_instances': [
                {
                    'id': 'db-instance-1',
                    'type': 'db.t3.medium',
                    'state': 'available',
                    'last_connection': '2023-07-01'
                }
            ]
        }
    
    def get_month_to_date_cost(self) -> Dict[str, Any]:
        """Get mock month-to-date cost data."""
        return self.mock_cost_data
    
    def get_cost_forecast(self) -> Dict[str, Any]:
        """Get mock cost forecast data."""
        return self.mock_forecast_data
    
    def get_idle_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get mock idle resources data."""
        return self.mock_idle_resources
    
    def display_cost_overview(self):
        """Display an overview of the current month's costs using mock data."""
        with console.status("[bold green]Fetching cost data..."):
            cost_data = self.get_month_to_date_cost()
            forecast_data = self.get_cost_forecast()
        
        # Extract the total cost
        total_cost = 0
        for group in cost_data['ResultsByTime'][0]['Groups']:
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            total_cost += amount
        
        # Get the forecast
        forecast_amount = float(forecast_data['Total']['Amount'])
        
        # Calculate the projected total
        projected_total = total_cost + forecast_amount
        
        # Create a table for the cost overview
        table = Table(title="AWS Cost Overview (DEMO DATA)", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Amount (USD)", style="green")
        
        table.add_row("Month-to-Date Spend", f"${total_cost:.2f}")
        table.add_row("Forecasted Additional Spend", f"${forecast_amount:.2f}")
        table.add_row("Projected Monthly Total", f"${projected_total:.2f}")
        
        console.print(table)
        
        # Create a table for service breakdown
        service_table = Table(title="Cost Breakdown by Service (DEMO DATA)", box=box.ROUNDED)
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
        """Display cost optimization recommendations using mock data."""
        with console.status("[bold green]Analyzing resources for optimization opportunities..."):
            idle_resources = self.get_idle_resources()
        
        console.print(Panel("[bold]Cost Optimization Recommendations (DEMO DATA)[/bold]", style="blue"))
        
        # EC2 Recommendations
        if idle_resources['ec2_instances']:
            ec2_table = Table(title="Stopped EC2 Instances", box=box.ROUNDED)
            ec2_table.add_column("Instance ID", style="cyan")
            ec2_table.add_column("Type", style="green")
            ec2_table.add_column("State", style="yellow")
            ec2_table.add_column("Stopped Since", style="magenta")
            
            for instance in idle_resources['ec2_instances']:
                ec2_table.add_row(
                    instance['id'],
                    instance['type'],
                    instance['state'],
                    instance['stopped_since']
                )
            
            console.print(ec2_table)
            
            # Calculate potential savings
            savings = 0
            for instance in idle_resources['ec2_instances']:
                if instance['type'] == 't3.medium':
                    savings += 0.0416 * 24 * 30  # $0.0416 per hour
                elif instance['type'] == 'm5.large':
                    savings += 0.096 * 24 * 30   # $0.096 per hour
            
            console.print(f"[bold green]Potential monthly savings:[/bold green] ${savings:.2f}")
            console.print("[bold green]Recommendation:[/bold green] Consider terminating these instances if they are no longer needed.")
        else:
            console.print("[green]No stopped EC2 instances found.[/green]")
        
        # EBS Recommendations
        if idle_resources['ebs_volumes']:
            ebs_table = Table(title="Unattached EBS Volumes", box=box.ROUNDED)
            ebs_table.add_column("Volume ID", style="cyan")
            ebs_table.add_column("Size (GB)", style="green")
            ebs_table.add_column("Type", style="yellow")
            ebs_table.add_column("Created", style="magenta")
            
            for volume in idle_resources['ebs_volumes']:
                ebs_table.add_row(
                    volume['id'],
                    str(volume['size']),
                    volume['type'],
                    volume['created']
                )
            
            console.print(ebs_table)
            
            # Calculate potential savings
            savings = 0
            for volume in idle_resources['ebs_volumes']:
                if volume['type'] == 'gp2':
                    savings += volume['size'] * 0.10  # $0.10 per GB-month
                elif volume['type'] == 'gp3':
                    savings += volume['size'] * 0.08  # $0.08 per GB-month
                elif volume['type'] == 'io1':
                    savings += volume['size'] * 0.125  # $0.125 per GB-month
            
            console.print(f"[bold green]Potential monthly savings:[/bold green] ${savings:.2f}")
            console.print("[bold green]Recommendation:[/bold green] Delete these unattached volumes to save on storage costs.")
        else:
            console.print("[green]No unattached EBS volumes found.[/green]")
        
        # General recommendations
        console.print("\n[bold]General Cost Optimization Tips:[/bold]")
        console.print("• Consider using Reserved Instances for steady-state workloads")
        console.print("• Implement auto-scaling for variable workloads")
        console.print("• Use Spot Instances for fault-tolerant, flexible workloads")
        console.print("• Implement lifecycle policies for S3 to move data to cheaper storage tiers")
        console.print("• Enable S3 Intelligent Tiering for objects with unknown access patterns")


@click.group()
def cli():
    """Cloud Cost Guardian Demo - Simulates the functionality without requiring AWS credentials."""
    pass


@cli.command()
def overview():
    """Display an overview of your current AWS spending (demo data)."""
    guardian = CloudCostGuardianDemo()
    guardian.display_cost_overview()


@cli.command()
def optimize():
    """Get recommendations for cost optimization (demo data)."""
    guardian = CloudCostGuardianDemo()
    guardian.display_optimization_recommendations()


@cli.command()
def anomalies():
    """Check for cost anomalies in your AWS account (demo feature)."""
    console.print("[yellow]This feature is under development for the full version.[/yellow]")
    console.print("The anomaly detection will analyze your spending patterns and alert you to unusual changes.")


@cli.command()
def cleanup():
    """Run automated cleanup of unused resources (demo feature)."""
    console.print("[yellow]This feature is under development for the full version.[/yellow]")
    console.print("The automated cleanup will help you remove unused resources safely.")


if __name__ == "__main__":
    console.print(Panel("[bold red]DEMO MODE[/bold red] - Using simulated data", style="yellow"))
    cli()
