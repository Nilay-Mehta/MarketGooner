python main.py scan --topic "AI agent pricing usage costs" --subreddits FreightBrokers Truckers --limit 100
python main.py scan --topic "Amazon PPC ACOS fees" --subreddits FulfillmentByAmazon AmazonSeller --limit 100
python main.py scan --topic "MLS commission split brokerage fees" --subreddits realtors RealEstate --limit 100
python main.py scan --topic "POS fees delivery commission" --subreddits restaurateur bartenders --limit 100
python main.py extract
python main.py cluster --recluster
python main.py rank
