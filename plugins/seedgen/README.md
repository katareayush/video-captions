# seedgen

A lightweight, local Claude Code plugin that **analyzes any repo and generates a runnable, schema-aware test-data seed script** — then wires it up so seeding just works in your environment.

Stack-agnostic by design: web2 backends, web3 contracts, Python services, or anything with a data model. It reads your actual schema (SQL migrations, Prisma, Django, Mongoose, Solidity, etc.), respects constraints and foreign keys, and produces referentially consistent data in *your* project's language.

## What it does

- **Analyzes** the repo — detects the stack and locates every data definition (migrations, ORM schemas, models, contracts, API types).
- **Generates** an idiomatic, idempotent seed script that satisfies enums, NOT NULL, unique, and FK constraints.
- **Wires it up** — reuses your existing DB config/`.env`, adds the run command and any needed dependency.
- **Filters / locales** — tell it `indian`, `us`, `japanese`, a count, or a scope, and the generated data (names, phones, addresses, currency) matches.

## Install

```
/plugin marketplace add katareayush/video-captions
/plugin install seedgen@katareayush
```

## Usage

Inside any repo:

```
/seed
/seed indian 50 users
/seed web3 only
/seed us, orders and payments
```

The command reads your schema, writes the seed script to a conventional path, and prints an exact **How to run** block.

## Layout

```
seedgen/
├── .claude-plugin/plugin.json
├── commands/seed.md          # the /seed command
├── references/locales.md     # locale/filter profiles
└── README.md
```

## License

MIT
