
Using the databricks-apps-python skill, scaffold a Databricks App called
"market-ops-assistant". It should use Gradio to build a chat app (gr.Blocks with
gr.ChatInterface) that authenticates as the app's service principal via
the Databricks SDK.

Add tool-calling capabilities. The LLM should be able to call these tools
via OpenAI function calling:


1. calculate_risk_metrics:
   - Takes: ticker (or "PORTFOLIO"), period_days, confidence_level
   - Returns: VaR, Sharpe ratio, max drawdown, volatility
   - Include methodology description in output

2. search_compliance_docs:
   - Takes: query string, optional regulation filter
     (KYC, AML, MiFID_II, SOX, GDPR)
   - Simulates RAG search over compliance knowledge base
   - Returns relevant regulatory excerpts

Implement a tool-calling loop (up to 5 iterations): LLM decides which
tool to call, we execute it, feed result back, LLM generates final answer.

Add user login:
- Define a get_current_user(request: gr.Request) function that extracts
  the user's identity from the "x-forwarded-access-token" header by
  calling the SCIM /Me endpoint ({cfg.host}/api/2.0/preview/scim/v2/Me)
- Display the logged-in user's name/email in a Markdown banner on page load
- Gate the run_agent function: reject unauthenticated users

System prompt should enforce:
- Never give personal investment advice
- Always cite data sources and date ranges
- Round financials to 2 decimal places
- Use ISO currency codes (USD, EUR, GBP)
- Include "⚠️ INTERNAL USE ONLY — not investment advice" disclaimer

CRITICAL implementation notes (avoid known bugs):
- cfg.host ALREADY includes the scheme (e.g. "https://example.cloud.databricks.com").
  So the OpenAI base_url must be f"{cfg.host}/serving-endpoints" — NOT
  f"https://{cfg.host}/serving-endpoints" (double scheme causes DNS failure).
- cfg.authenticate() returns a dict. Use headers.get("Authorization", "")
  not headers["Authorization"] for safer access.
- Import requests as http_requests (to avoid shadowing).
- The get_current_user function MUST be defined before run_agent and
  load_user_info reference it — define it right after _get_openai_token().

Files to create:
- app.py (all logic in one file)
- app.yaml with command [python, app.py] and env vars:
    DATABRICKS_WAREHOUSE_ID valueFrom: sql-warehouse
    SERVING_ENDPOINT_NAME valueFrom: serving-endpoint
- requirements.txt: databricks-sdk, databricks-sql-connector, openai

After deploy, remind me to attach the sql-warehouse and serving-endpoint
resources in the Apps UI.
