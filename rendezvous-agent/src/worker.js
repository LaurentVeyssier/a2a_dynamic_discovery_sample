export class Registry {
    constructor(state) {
        this.state = state;
    }

    async fetch(request) {
        const url = new URL(request.url);

        if (request.method === "POST" && url.pathname === "/register") {
            return this.register(request);
        }

        if (request.method === "POST" && url.pathname === "/heartbeat") {
            return this.heartbeat(request);
        }

        if (request.method === "GET" && url.pathname === "/agents") {
            return this.listAgents();
        }

        if (request.method === "DELETE" && url.pathname === "/unregister") {
            return this.unregister(request);
        }

        if (request.method === "GET" && url.pathname === "/") {
            return json({
                service: "rendezvous-agent",
                status: "ok"
            });
        }

        return new Response("Not Found", { status: 404 });
    }

    async register(request) {
        const agent = await request.json();
        agent.last_seen = Date.now();
        await this.state.storage.put(agent.agent_id, agent);
        return new Response(JSON.stringify({ status: "registered" }), {
            status: 200,
            headers: { "Content-Type": "application/json" }
        });
    }

    async heartbeat(request) {
        const { agent_id } = await request.json();
        const agent = await this.state.storage.get(agent_id);
        if (!agent) return new Response(JSON.stringify({ error: "unknown agent" }), { status: 404, headers: { "Content-Type": "application/json" } });
        agent.last_seen = Date.now();
        await this.state.storage.put(agent_id, agent);
        return new Response(JSON.stringify({ status: "alive" }), { status: 200, headers: { "Content-Type": "application/json" } });
    }

    async unregister(request) {
        const { agent_id } = await request.json();
        await this.state.storage.delete(agent_id);
        return new Response(JSON.stringify({ status: "removed" }), { status: 200, headers: { "Content-Type": "application/json" } });
    }

    async listAgents() {
        const now = Date.now();
        const TTL = 60_000;

        const all = await this.state.storage.list();
        const agents = [];
        for (const [key, agent] of all) { // Correct iteration for Map
            if (now - agent.last_seen < TTL) {
                agents.push(agent);
            }
        }

        return json(agents);
    }
}

function json(data, status = 200) {
    return new Response(JSON.stringify(data, null, 2), {
        status,
        headers: { "Content-Type": "application/json" }
    });
}

export default {
    fetch(request, env) {
        const id = env.REGISTRY.idFromName("global");
        return env.REGISTRY.get(id).fetch(request);
    }
};
