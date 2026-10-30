# Architecture

## Data flow

```mermaid
flowchart TB
    subgraph TENANT["Tenant (per customer)"]
        CFG["config: state, city, mode, plan"]
        SKU["skus"]
    end
    subgraph CLOUD["Your cloud"]
        BILL["billing (Stripe)"]
        ADM["admin console"]
        TEN["tenant registry"]
    end
    subgraph RUN["Runtime (their container or yours)"]
        CORE["fbm_core: lock/rate/selectors/session"]
        PUB["bot + groups + crosslist"]
        INTEL["comps -> targets -> reprice"]
        ORD["watcher -> suppliers -> tracking"]
        AI["inbox_poller -> inbox_ai"]
    end
    FB["Facebook Marketplace"]
    MAIL["Email (alias routing)"]
    VEND["Suppliers / vendors"]

    CFG --> CORE --> PUB --> FB
    FB --> INTEL --> PUB
    FB --> ORD --> VEND
    VEND --> MAIL --> ORD --> FB
    FB --> AI --> FB
    TEN --> CLOUD --> BILL
    RUN -->|metrics| ADM
```

## Trust boundaries

- **Their data stays local** unless they enable cloud sync. The cloud only stores tenant/plan/billing + aggregate metrics.
- **Supplier keys** live in their `.env`. Ours never touch them.
- **Billing** is the only PII: email + Stripe customer id.

## Failure domains

| Domain | Blast radius | Mitigation |
|---|---|---|
| Profile lock | one tenant | per-tenant profile dirs |
| Rate limit | one account | per-account limiter state |
| Vendor outage | one SKU | backup supplier |
| FB suspension | one account | multi-account routing |
| Billing failure | dashboard only | listings keep running |