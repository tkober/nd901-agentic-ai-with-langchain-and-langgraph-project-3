## MCP Servers

All tooling in this project is exposed via MCP servers, which are implemented using the `langchain_mcp` library. Each server provides a set of tools and resources that can be accessed by the agent to perform various tasks related to user management, knowledgebase querying, and experience management.

In order to run this project, you need to start these MCP servers so that the agent can communicate with them.

Before running the MCP Servers, make sure the virtual environment is activated and all dependencies are installed (see [Prerequisites](../../README.md#prerequisites)). Each MCP server can be run independently, and they will listen for incoming requests on their respective ports.
You can activate the virtual environment with the following command:

```bash
source .venv/bin/activate
```

### UDA Hub MCP Server

This server provides tools to interact with the UDA Hub database, which contains information about users, accounts, and knowledge entries.
Run this server with the following command:

```bash
python -m starter.mcp_servers.udahub_mcp
```

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `create_udahub_user` | tool | Create a new user in the UdaHub database. | `account_id: str`, `external_user_id: str`, `user_name: str` | `udahub`, `user`, `create`, `validation` | no | no | no |
| `get_udahub_user` | tool | Retrieve user details from the UdaHub database by using the internal UDA Hub user ID. | `user_id: str` | `udahub`, `user`, `details` | yes | no | yes |
| `find_udahub_user` | tool | Find a user in the UdaHub database by using the account ID of a customer and the external user ID. | `account_id: str`, `external_user_id: str` | `udahub`, `user`, `details`, `validation` | yes | no | yes |
| `get_udahub_account` | tool | Retrieve account details from the UdaHub database. | `account_id: str` | `udahub`, `account`, `details` | yes | no | yes |

### UDA Hub Knowledgebase MCP Server

This server provides tools to manage and query the knowledgebase, which contains information about customers, their issues, and relevant experiences.
Run this server with the following command:

```bash
python -m starter.mcp_servers.knowledgebase_mcp
```

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `knowledgebase_config` | resource (`data://config`) | Configuration for the knowledgebase. | - | `monitoring`, `config` | - | - | - |
| `sync_cultpass_experiences` | tool | Synchronize the Cultpass experiences into the knowledgebase. | - | `cultpass`, `sync`, `experiences` | no | no | yes |
| `sync_udahub_knowledgebase` | tool | Synchronize the UdaHub knowledge entries into the knowledgebase. | - | `udahub`, `sync` | no | no | yes |
| `query_udahub_knowledgebase` | tool | Query the UdaHub knowledgebase for learnings related to a given customer. | `account_id: str`, `query_text: str`, `n_results: int (0..10)` | `cultpass`, `query`, `knowledge`, `faq` | yes | no | yes |
| `query_cultpass_experiences` | tool | Query the experiences which Cultpass offers. | `query_text: str`, `n_results: int (0..10)` | `cultpass`, `query`, `knowledge`, `experiences`, `browsing` | yes | no | yes |

### Cultpass MCP Server

This server provides tools to interact with the Cultpass database, which contains information about users, their subscriptions, reservations, and available experiences.
Run this server with the following command:

```bash
python -m starter.mcp_servers.cultpass_mcp
```

| Name | Type | Description | Arguments | Tags | ReadOnly | Destructive | Idempotent |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `get_cultpass_user` | tool | Retrieve user details from the Cultpass database. | `user_id: str` | `cultpass`, `user`, `details`, `subscription`, `validation` | yes | no | yes |
| `cancel_cultpass_subscription` | tool | Cancel a user's subscription in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `cancel` | no | yes | no |
| `reactivate_cultpass_subscription` | tool | Reactivate a user's cancelled subscription in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `reactivate` | no | no | no |
| `upgrade_cultpass_subscription` | tool | Upgrade a user's subscription to premium in the Cultpass database. | `user_id: str` | `cultpass`, `subscription`, `upgrade` | no | no | no |
| `get_cultpass_reservations` | tool | Retrieve reservations for a user from the Cultpass database. | `user_id: str` | `cultpass`, `reservation`, `details` | yes | no | yes |
| `cancel_cultpass_reservation` | tool | Cancel a reservation for a user in the Cultpass database. | `user_id: str`, `reservation_id: str` | `cultpass`, `reservation`, `cancel` | no | yes | no |
| `make_cultpass_reservation` | tool | Make a reservation for a user in the Cultpass database. | `user_id: str`, `experience_id: str` | `cultpass`, `reservation`, `create` | no | no | no |
| `get_cultpass_experience` | tool | Retrieve experience details from the Cultpass database. | `experience_id: str` | `cultpass`, `experience`, `details`, `browsing` | yes | no | yes |