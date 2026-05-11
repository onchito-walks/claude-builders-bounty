# CLAUDE.md — Next.js 15 + SQLite SaaS

> Opinionated project context for AI coding assistants.
> Paste into any greenfield Next.js 15 App Router + SQLite project. No edits needed.

---

## Stack & Versions

- **Next.js** 15.x (App Router, not Pages Router)
- **React** 19.x
- **TypeScript** 5.x (strict mode)
- **SQLite** via better-sqlite3 (local dev) or Turso (prod)
- **ORM:** Drizzle ORM — not Prisma, not Knex
- **Auth:** NextAuth.js v5 (Auth.js)
- **Styling:** Tailwind CSS 4.x + shadcn/ui components
- **Package manager:** pnpm (not npm, not yarn)
- **Node:** 22.x LTS

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Auth route group (login, register)
│   ├── (dashboard)/       # Protected route group
│   ├── api/               # API routes (REST, not tRPC)
│   ├── layout.tsx         # Root layout (providers only)
│   └── page.tsx           # Landing page
├── components/
│   ├── ui/                # shadcn/ui primitives (auto-generated)
│   └── features/          # Feature-specific components
├── lib/
│   ├── db.ts              # Database connection singleton
│   ├── auth.ts            # NextAuth config
│   └── utils.ts           # cn(), formatDate(), etc.
├── db/
│   ├── schema.ts          # Drizzle schema definitions
│   ├── migrations/        # SQL migration files
│   └── seed.ts            # Dev seed script
└── types/
    └── index.ts           # Shared types (no `any`)
```

## Dev Commands

```bash
pnpm dev          # Start dev server (port 3000)
pnpm build        # Production build
pnpm db:push      # Push schema changes to SQLite (no migration files)
pnpm db:migrate   # Run pending migrations
pnpm db:seed      # Seed dev data
pnpm db:studio    # Drizzle Studio (GUI for SQLite)
pnpm lint         # ESLint
pnpm typecheck    # TypeScript check without emit
```

## SQL / Migration Conventions

- **Schema is source of truth** — define tables in `db/schema.ts`, never raw SQL
- Use `pnpm db:push` during active development (no migration files)
- Generate migration files only before PRs: `pnpm db:generate`
- **Never** edit migration files after they're committed
- All timestamps: `integer('created_at', { mode: 'timestamp' })` — Unix epoch ms
- UUIDs: `text('id').primaryKey().$defaultFn(() => crypto.randomUUID())`
- Soft delete: `integer('deleted_at', { mode: 'timestamp' })` — null means active
- **No** `SELECT *` — always specify columns in queries

## Component Patterns

- **Server Components by default** — only add `'use client'` when you need hooks or browser APIs
- Server Actions for mutations — not API routes for form submissions
- Colocate queries with their Server Component: `const users = await db.select()...` at the top of the component file
- **No** `useEffect` for data fetching — use Server Components instead
- Error boundaries at route segment level: `error.tsx` files
- Loading states at route segment level: `loading.tsx` files
- shadcn/ui for all UI primitives — no custom Button/Input/Card components

### Naming

- Components: PascalCase (`UserCard.tsx`)
- Server actions: camelCase with `action` suffix (`createUserAction`)
- API routes: kebab-case (`/api/user-settings`)
- DB tables: snake_case (`user_settings`)
- Files: kebab-case (`user-card.tsx`), except components which may be PascalCase

## What We Don't Do (and Why)

- **No Prisma** — too slow for SQLite, schema-first doesn't fit our workflow. Drizzle is lighter and generates better SQL.
- **No tRPC** — adds complexity without benefit for a SaaS with a public API. REST is simpler and more portable.
- **No Zustand/Redux** — Server Components eliminate most client state. Use `useState` for local UI state, URL params for shared state.
- **No Axios** — `fetch` is built into Next.js. No reason for an extra dependency.
- **No `any`** — if TypeScript can't infer it, define the type explicitly.
- **No barrel files** (`index.ts` that just re-exports) — they break tree-shaking. Import directly from the source file.
- **No CSS Modules** — Tailwind handles styling. If you need dynamic styles, use `clsx`/`cn()`.
- **No server-side `localStorage`** — always guard with `typeof window !== 'undefined'`.
- **No `getServerSideProps`** — that's Pages Router. Use `fetch` in Server Components instead.

## Database Connection

```typescript
// lib/db.ts — singleton pattern
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from '@/db/schema';

const sqlite = new Database('dev.db');
export const db = drizzle(sqlite, { schema });
```

- **Dev:** local `dev.db` file via better-sqlite3
- **Prod:** Turso (`@libsql/client`) — same Drizzle schema, different driver
- Connection is a **singleton** — never create multiple instances

## Auth Patterns

- NextAuth v5 with the App Router adapter
- Session in HTTP-only cookies — no localStorage tokens
- Protected routes: wrap in `auth()` server-side, `SessionProvider` client-side
- Never expose user IDs in client code — use opaque tokens or server-side resolution

## Common Pitfalls

- **`async` in Server Components** — you CAN await directly in the component. No need for `useEffect`.
- **Drizzle relations** — always define `relations()` in schema.ts, not inline
- **SQLite limitations** — no `ALTER TABLE DROP COLUMN` (use new table + rename). No `RETURNING` (use `.returning()` in Drizzle which simulates it).
- **Turso sync** — local dev DB doesn't auto-sync with prod. Use `turso db shell` for prod queries.

## PR Checklist

Before submitting a PR, verify:

- [ ] `pnpm typecheck` passes
- [ ] `pnpm lint` passes
- [ ] No `any` types introduced
- [ ] No new dependencies without justification
- [ ] Server Components used unless client is required
- [ ] Schema changes include migration file (or are `db:push`-only for WIP)
