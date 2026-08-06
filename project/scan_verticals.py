import subprocess
import time

scans = [
    ["python", "-X", "utf8", "main.py", "scan", "--topic", "Amazon FBA seller pain points software", "--subreddits", "FulfillmentByAmazon", "AmazonSeller", "--limit", "30"],
    ["python", "-X", "utf8", "main.py", "scan", "--topic", "real estate investor agent pain points", "--subreddits", "realestateinvesting", "Realtors", "--limit", "30"],
    ["python", "-X", "utf8", "main.py", "scan", "--topic", "small business acquisition search fund issues", "--subreddits", "smallbusiness", "Entrepreneur", "--limit", "30"],
    ["python", "-X", "utf8", "main.py", "scan", "--topic", "freight broker logistics supply chain software", "--subreddits", "FreightBrokers", "logistics", "--limit", "30"],
    ["python", "-X", "utf8", "main.py", "scan", "--topic", "Etsy seller store software pain points", "--subreddits", "EtsySellers", "--limit", "30"],
]

for cmd in scans:
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd)
    time.sleep(2)
    print("Done.\n")
