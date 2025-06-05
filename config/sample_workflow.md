{
  "name": "My workflow",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "/calendly",
        "options": {}
      },
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [
        -660,
        -280
      ],
      "id": "3d9147f9-6cfe-456c-8210-db2ec51263fb",
      "name": "Webhook",
      "webhookId": "83cfd9e8-f3a6-43b9-88af-30eb05c748ba"
    },
    {
      "parameters": {
        "resource": "mail",
        "toEmail": "={{$json[\"email\"]}}",
        "dynamicTemplate": true,
        "additionalFields": {}
      },
      "type": "n8n-nodes-base.sendGrid",
      "typeVersion": 1,
      "position": [
        -260,
        -280
      ],
      "id": "df69f4e8-2949-4b10-8b3e-844e5ab348b7",
      "name": "SendGrid"
    }
  ],
  "pinData": {},
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "SendGrid",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": false,
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "0c70166b-702c-4a1c-ac7a-718adddcce1b",
  "meta": {
    "instanceId": "29579e9e4601a6e9a8edc3d0abdc197bc5757a27dbefc26efb0fe5232c6e1ac6"
  },
  "id": "fHNbe2PBcUMGpZXJ",
  "tags": []
}