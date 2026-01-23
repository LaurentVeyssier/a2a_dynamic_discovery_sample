# Rendezvous-agent

## How to deploy

prerequisites:
- wrangler (cloudflare CLI tool) is installed (`npm install -g wrangler`) + cloudflare workers (free) account is created 

steps:
- use the code and project structure from rendezvous-agent folder
    

```
rendezvous-agent/
├── wrangler.toml
└── src/
    └── worker.js
```
- login to cloudflare: `wrangler login`
- deploy from inside the rendezvous-agent folder: `wrangler deploy`
- check the deployed function at https://cloudflare.com/workers

-> live rendezvous agent deployed and reachable using its endpoint (defined in .env file)

## cloudflare workers definition

The rendezvous agent stores registered agents in a SQLite-backed Durable Object; records persist indefinitely, but agents are treated as “dead” when their last_seen exceeds the TTL.

A stateless request handler that can talk to stateful storage.
A Cloudflare Worker is:
- A small JavaScript program
- Executed inside Cloudflare’s infrastructure
- Triggered per HTTP request
- Has no permanent memory by itself

The Worker does not run continuously. It only runs when a request arrives.

`env.REGISTRY.get(id).fetch(request)` forwards the request to the Durable Object instance called Registry (stateful, persistent, consistent, serverless). The free-tier is backed by SQLite.

the registry is NOT stored in the Worker.
It is stored inside the Durable Object’s SQLite database.

`await this.state.storage.put(agent_id, agent)` writes a row into Cloudflare-managed SQLite storage.

This storage is not cleared automatically. It usesLogical TTL (soft expiration). The code enforces logical expiration using `last_seen`.
- Dead agents are filtered out
- But their records still exist in storage

```
if (now - agent.last_seen < TTL) {
  agents.push(agent);
}
```

## Role & capabilities

Responsability: Discovery, liveness tracking

Capabilities:
| Method   | Path          | Purpose                  |
| -------- | ------------- | ------------------------ |
| `POST`   | `/register`   | Register / refresh agent |
| `POST`   | `/heartbeat`  | Keep agent alive         |
| `GET`    | `/agents`     | List live agents         |
| `DELETE` | `/unregister` | Graceful leave           |

We used Durable Objects. Durable Objects are:

- Small, stateful actors
- Strongly consistent
- Addressable by ID
- Still serverless

Once agents are registered, they can be discovered by other agents or services. We expect:

```
Cloudflare Worker
   └── Durable Object (Registry)
      ├── agent-a
      ├── agent-b
      └── agent-c
```

## Testing

curl.exe \<worker endpoint>/agents

returns the list of registered agents (or [] if none)