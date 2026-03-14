# Product Overview

A2A Dynamic Discovery Sample - A multi-agent system demonstrating autonomous agent discovery, coordination, and collaboration using the Agent-to-Agent (A2A) protocol.

## Core Concept

This project showcases how autonomous agents can **dynamically discover, connect, and coordinate** with each other to solve complex user requests without hardcoded dependencies. Agents find peers based on capabilities rather than pre-configured endpoints.

## Key Features

1. **Dynamic Discovery**: Agents discover each other via a central rendezvous registry (Cloudflare Worker)
2. **Capability-Based Routing**: Agents search for peers by capabilities, not by hardcoded URLs
3. **Agent Handshakes**: Agents verify peer status and exchange capability cards before collaboration
4. **Autonomous Delegation**: Agents delegate sub-tasks to specialized peers and relay results
5. **Real-Time Visualization**: Frontend dashboard shows live agent interactions (discovery, handshake, call, response)

## Architecture Components

### Agents
- **Personal Assistant**: User-facing agent with access to personal data (passport info)
- **Travel Agent**: Orchestrates travel bookings, coordinates between user and airline
- **Airline Agent**: Handles flight-specific operations, requires passport for booking

### Infrastructure
- **Rendezvous Agent**: Cloudflare Worker serving as central registry for agent discovery
- **Frontend Dashboard**: Real-time visualization of agent interactions with chat interface

## User Flow Example

1. User requests: "Book a trip to Paris on 2026-02-01"
2. Personal Assistant searches registry for "travel" capability
3. Travel Agent is discovered and receives delegation
4. Travel Agent searches for "airline" capability
5. Airline Agent is found but requires passport number
6. Travel Agent calls back to Personal Assistant for passport
7. Personal Assistant provides passport data
8. Airline Agent confirms booking
9. Success message propagates back: Airline → Travel → PA → User

## Event Types

The dashboard visualizes four event types:
- 🔵 **DISCOVERY**: Agent searching the registry for capabilities
- 🟡 **HANDSHAKE**: Verification of peer status and capability exchange
- 🟢 **CALL**: Task delegation between agents
- ⚪ **RESPONSE**: Result of task delegation

## Deployment Modes

### Development (Version 1)
- Each agent runs on separate port (9000, 9001, 9002)
- Higher memory footprint (~600MB+)
- More flexible for independent scaling

### Production (Version 2 - Current)
- All agents run on single port (9000) via ADK
- Lower memory footprint (350-450MB)
- Fits in 512MB RAM constraint
- Agent cards at: `http://host:9000/a2a/<agent_name>/.well-known/agent-card.json`

## Key Constraints

- Agents register with rendezvous on startup
- Heartbeat mechanism maintains "active" status
- No hardcoded peer URLs - all discovery is dynamic
- Agent cards follow A2A protocol standard
