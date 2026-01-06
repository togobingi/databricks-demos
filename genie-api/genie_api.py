import requests
import json

# Configuration
DATABRICKS_HOST = "HOST-NAME"
DATABRICKS_TOKEN = "TOKEN" #use DB secrets:--> dbutils.secrets.get(scope = "your-secret-scope", key = "DATABRICKS_TOKEN")
WAREHOUSE_ID = "WAREHOUSE-ID"  # SQL Warehouse ID (find in SQL Warehouses page)


# API endpoint
url = f"{DATABRICKS_HOST}/api/2.0/genie/spaces"

# Headers
headers = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

# Your serialized space configuration
space_config = {
    "version": 1,
    "config": {
        "sample_questions": [
            {
                "id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
                "question": ["What were total sales last month?"]
            },
            {
                "id": "b2d46dca936942a081c7d8b5e2e62041",
                "question": ["Show top 10 customers by revenue"]
            },
            {
                "id": "3e4b87c9a1d24f41b2a6c9f5d873c201",
                "question": ["Compare sales by region for Q1 vs Q2"]
            }
        ]
    },
    "data_sources": {
        "tables": [

          {
                "identifier": "CATALOG.SCHEMA.TABLE"
            },
          
            {
                "identifier": "CATALOG.SCHEMA.TABLE",
                "description": ["Transactional order data including order date, amount, and customer information"],
                "column_configs": [
                  {
                        "column_name": "customer_id",
                        "get_example_values": True,
                        "build_value_dictionary": False
                    },
                    {
                        "column_name": "order_date",
                        "get_example_values": True
                    },
                    {
                        "column_name": "status",
                        "get_example_values": True,
                        "build_value_dictionary": True
                    }
                
                ]
            }
            ]
    },
    "instructions": {
        "text_instructions": [
            {
                "id": "01f0b37c378e1c91aabbccddeeff0011",
                "content": [
                    "When calculating revenue, sum the order_amount column. When asked about 'last month', use the previous calendar month (not the last 30 days). Round all monetary values to 2 decimal places."
                ]
            }
        ],
        "example_question_sqls": [
            {
                "id": "01f0821116d912dbaabbccddeeff0022",
                "question": ["Show top 10 customers by revenue"],
                "sql": [
                    "SELECT customer_name, SUM(order_amount) as total_revenue\n",
                    "FROM CATALOG.SCHEMA.TABLE o\n",
                    "JOIN CATALOG.SCHEMA.TABLE c ON o.customer_id = c.customer_id\n",
                    "GROUP BY customer_name\n",
                    "ORDER BY total_revenue DESC\n",
                    "LIMIT 10"
                ]
            },
            {
                "id": "01f099751a3a1df3aabbccddeeff0033",
                "question": ["What were total sales last month"],
                "sql": [
                    "SELECT SUM(order_amount) as total_sales\n",
                    "FROM CATALOG.SCHEMA.TABLE\n",
                    "WHERE order_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL 1 MONTH)\n",
                    "AND order_date < DATE_TRUNC('month', CURRENT_DATE)"
                ]
            }
        ],
       
        "sql_snippets": {
            "filters": [
                {
                    "id": "01f09972e66d1aabbccddeeff0055666",
                    "sql": ["orders.order_amount > 1000"],
                    "display_name": "high value orders",
                    "synonyms": ["large orders", "big purchases"]
                }
            ],
            "expressions": [
                {
                    "id": "01f09974563a1aabbccddeeff0066777",
                    "alias": "order_year",
                    "sql": ["YEAR(orders.order_date)"],
                    "display_name": "year"
                }
            ]
        }
    }
}

# Request payload
payload = {
    "display_name": 'My Genie Space',
    "description": 'Used to understand our customers and order behaviour',
    "serialized_space":  json.dumps(space_config),
    "warehouse_id": WAREHOUSE_ID
}

# API request
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result = response.json()
    print("Genie space created successfully!")
    print(f"Space ID: {result.get('id')}")
    print(f"Space Name: {result.get('display_name')}")
    print(f"\nFull response:")
    print(json.dumps(result, indent=2))
    
except requests.exceptions.HTTPError as e:
    print(f"✗ HTTP Error: {e}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")
