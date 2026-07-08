# Clone repo
- Log in to your Databricks Free Edition workspace
- Clone this repo: https://github.com/togobingi/databricks-demos/tree/main/databricks-apps/mcp-ai-dev-kit 
- Navigate to the “databricks-apps/mcp-ai-dev-kit” folder
  - Run all cells in this file: add_skills_from_ai_dev_kit (this installs all the Databricks skills in your workspace)
- Now create a new Databricks App
- Select "Create a custom app"
  - Give your app this name: mcp-ai-dev-kit
  - Click on “Create app”
- Once created, select “Deploy” then navigate to the folder in the cloned repo: “mcp-ai-dev-kit”

# How Users Connect
- Skills (automatic — no setup)
- After the app is deployed, skills are immediately available to all Genie Code users. Genie Code loads them contextually when relevant. Users can also invoke them with @skill-name
.

# Install MCP Tools
- Open Genie Code Settings (gear icon)
- Under MCP Servers, click Add Server
- Select mcp-ai-dev-kit from the Databricks App list
- Choose which tools to enable (max 15 per server)
  - execute_sql
  - execute_code
  - manage_pipeline
  - manage_serving_endpoint
  - manage_app
  - get_current_user
- Close and save
- Ask Genie Code how many skills & MCP tools it has access to.

# Start vibe coding
- Under the databricks-apps folder, open Lab1_prompt.md
- Copy and paste that prompt into Genie Code and follow the instructions to start vibe coding your app
