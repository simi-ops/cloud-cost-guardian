#!/bin/bash

# Script to generate screenshots for documentation

# Create a directory for screenshots
mkdir -p screenshots

# Activate the virtual environment
source venv/bin/activate

# Generate overview screenshot
echo "Generating overview screenshot..."
python cost_guardian.py overview > screenshots/overview.txt

# Generate optimization screenshot
echo "Generating optimization screenshot..."
python cost_guardian.py optimize > screenshots/optimize.txt

# Generate anomalies screenshot
echo "Generating anomalies screenshot..."
python cost_guardian.py anomalies > screenshots/anomalies.txt

# Generate demo screenshots
echo "Generating demo screenshots..."
python demo.py overview > screenshots/demo_overview.txt
python demo.py optimize > screenshots/demo_optimize.txt

echo "Screenshots generated in the 'screenshots' directory."
echo "You can use these text files to create actual screenshots for your documentation."

# Deactivate the virtual environment
deactivate
