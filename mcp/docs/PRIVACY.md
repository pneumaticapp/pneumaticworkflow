# Pneumatic connector for Claude: privacy notice

This notice explains how the Pneumatic connector for Claude handles data when you use the hosted connector at `https://mcp.pneumatic.app`. It supplements the [Pneumatic privacy policy](https://www.pneumatic.app/legal/privacy/), which covers your Pneumatic account and the data stored in it.

The connector is operated by Pneumatic Software Inc. If you self-host Pneumatic, your connector runs on your own server and your organization is responsible for it.

## What the connector does

The connector is a bridge between Claude and your Pneumatic account. When you ask Claude to do something in Pneumatic, Claude calls a connector tool, the connector calls the Pneumatic API with your API key and returns the result to Claude. The connector has no database of its own and does not store your Pneumatic data.

## Data the connector processes

| Data                                                                                                                 | Why                                                 | Where it is kept                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Your Pneumatic API key                                                                                               | To act in Pneumatic on your behalf                  | Only encrypted (AES-256-GCM) inside the OAuth tokens held by Claude, the short-lived authorization code and your one-time upload links; the connector does not store it |
| Tool requests and results: tasks, workflows, templates, comments, users, groups, datasets, reports, files you choose | To carry out your request                           | Passed through in memory while the request runs; not stored by the connector                                                                                            |
| Files you upload through a one-time upload link                                                                      | To attach them in Pneumatic                         | Passed straight to Pneumatic file storage; the link and its upload status are kept in memory for up to 25 hours                                                         |
| Identifiers of used OAuth codes and tokens and their expiry times                                                    | To block reuse of stolen or replayed tokens         | A ledger on the connector server; contains no API keys or Pneumatic data; entries are removed after they expire                                                         |
| A one-way hash of your API key, request counters, and the IP address of failed sign-in attempts                      | Rate limiting and caching the key check             | In memory: counters and the key check for up to 5 minutes, failed sign-in IPs for 1 minute, the key hash of an upload link with its record (up to 25 hours)             |
| Technical request logs: request ID, route, HTTP status, duration, tool name and outcome                              | Operating, securing and troubleshooting the service | Connector server logs                                                                                                                                                   |

The connector's logs never contain API keys, tokens, upload links, request bodies, tool arguments or tool results. The reverse proxy in front of the connector records standard access log entries (time, IP address, request path and status), as for the rest of Pneumatic.

The connector does not use your data for advertising, analytics, profiling or training AI models, and does not sell it.

## Sharing with third parties

- **Anthropic.** Tool results are returned to Claude as part of your conversation. From then on Anthropic processes them under the terms of your Claude plan and [Anthropic's privacy policy](https://www.anthropic.com/legal/privacy). Pneumatic does not control that processing.
- **Pneumatic.** The connector sends your requests and API key only to the Pneumatic API and the Pneumatic file storage.
- **Public URLs you ask for.** When you ask Claude to attach a file from a public HTTPS link, the connector downloads that file without your API key or any credentials and stores it in Pneumatic.

No other third party receives data from the connector.

## Retention

- OAuth access tokens expire after 1 hour, refresh tokens after 90 days without use.
- Upload links expire after 1 hour; their records are removed 24 hours after that.
- Token reuse records are removed from the ledger after the tokens expire.
- Logs are kept only as long as needed to operate and secure the service, then deleted, as described in the Pneumatic privacy policy.
- Data you create or change through Claude (tasks, comments, files and so on) is stored in your Pneumatic account and kept under the Pneumatic privacy policy, the same as data entered in the web app.

## Your control

- Disconnect the connector in Claude at any time.
- Delete the API key in Pneumatic (**Integrations → Your API Keys**) to revoke access for every connected session within 5 minutes.
- The connector can only do what the API key owner can do in Pneumatic.
- Your rights to access, correct and delete your personal data are described in the [Pneumatic privacy policy](https://www.pneumatic.app/legal/privacy/).

## Security

Connections use HTTPS. Sign-in uses OAuth 2.1 with PKCE, and tokens are encrypted and bound to the connector. The API key is re-checked with Pneumatic at least every 5 minutes. More technical details: [README, Security model](../README.md#security-model).

## Contact

Pneumatic Software Inc., 8350 N Central Expy, Suite 1900, Dallas, Texas 75206, USA
Email: [support@pneumatic.app](mailto:support@pneumatic.app)

We will update this notice when the connector's data handling changes.
