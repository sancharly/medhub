# Architecture Patterns

## Pattern Comparison

| Pattern              | Best For                    | Team Size | Trade-offs                                |
|----------------------|-----------------------------|-----------|-------------------------------------------|
| **Monolith**         | Simple domain, small team   | 1-10      | Simple deploy; hard to scale parts        |
| **Modular Monolith** | Growing complexity          | 5-20      | Module boundaries; still single deploy    |
| **Microservices**    | Complex domain, large org   | 20+       | Independent scale; operational complexity |
| **Serverless**       | Variable load, event-driven | Any       | Auto-scale; cold starts, vendor lock      |
| **Event-Driven**     | Async processing            | 10+       | Loose coupling; debugging complexity      |

## Monolith

```plantuml
@startuml
skinparam linetype ortho

package "Application" #lightblue {
    rectangle "Users" as Users
    rectangle "Orders" as Orders
    rectangle "Products" as Products
}

database "Database" as DB #lightgray

Users --> DB
Orders --> DB
Products --> DB

@enduml
```

**When to Use**:

- Starting a new project
- Small team (< 10 developers)
- Simple domain
- Rapid iteration needed

**Pros**: Simple deployment, easy debugging, no network latency
**Cons**: Hard to scale independently, technology locked, deployment risk

## Microservices

```plantuml
@startuml
skinparam linetype ortho

rectangle "Users\nService" as UserSvc #lightblue
rectangle "Orders\nService" as OrderSvc #lightblue
rectangle "Products\nService" as ProductSvc #lightblue

database "User DB" as UserDB #lightgray
database "Order DB" as OrderDB #lightgray
database "Product DB" as ProductDB #lightgray

UserSvc --> UserDB
OrderSvc --> OrderDB
ProductSvc --> ProductDB

@enduml
```

**When to Use**:

- Large team (20+ developers)
- Complex domain with clear boundaries
- Different scaling requirements per service
- Polyglot technology needs

**Pros**: Independent scaling, team autonomy, fault isolation
**Cons**: Distributed system complexity, eventual consistency, operational overhead

## Event-Driven

```plantuml
@startuml
skinparam linetype ortho

rectangle "Producer" as Producer #lightblue
queue "Message Bus\n(Kafka)" as Bus #lightgray
rectangle "Consumer A" as ConsumerA #lightblue
rectangle "Consumer B" as ConsumerB #lightblue

Producer --> Bus
Bus --> ConsumerA
Bus --> ConsumerB

@enduml
```

**When to Use**:

- Async processing required
- Loose coupling between services
- Event sourcing needs
- High throughput messaging

**Pros**: Decoupled services, scalable, audit trail
**Cons**: Eventual consistency, debugging complexity, message ordering

## CQRS (Command Query Responsibility Segregation)

```plantuml
@startuml
skinparam linetype ortho

rectangle "Commands" as Commands #lightblue
rectangle "Write Model" as WriteModel #lightblue
rectangle "Events" as Events #lightgray
rectangle "Read Model" as ReadModel #lightblue
rectangle "Queries" as Queries #lightblue

Commands --> WriteModel
WriteModel --> Events
Events --> ReadModel
ReadModel --> Queries

@enduml
```

**When to Use**:

- Read/write ratio heavily skewed
- Complex read queries
- Event sourcing architecture
- Different optimization needs

## Quick Reference

| Requirement      | Recommended Pattern |
|------------------|---------------------|
| Simple CRUD app  | Monolith            |
| Growing startup  | Modular Monolith    |
| Enterprise scale | Microservices       |
| Variable load    | Serverless          |
| Async processing | Event-Driven        |
| Read-heavy       | CQRS                |
