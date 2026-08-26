**# Subscription Auditor**

Finds recurring charges (subscriptions) in bank/card statement exports,

flags silent price increases, estimates what you'd save by cancelling them,

and answers plain-language questions about the results through an

LLM agent grounded in the actual detection output (not free-floating chat).

\`\`\`

Upload CSV -> detect subscriptions -> "Ask the Auditor" about what was found

\`\`\`

**## Why this is harder than \`groupby("merchant")\`**

Real bank exports are messy: merchant names vary transaction to transaction

(\`NETFLIX.COM\` vs \`NETFLIX LOS GATOS CA\` vs \`NFLX\*STREAMING\`), billing dates

drift, prices change, and not everything that repeats is a subscription (a

weekly coffee habit looks similar at a glance but has irregular timing and

amounts). This project handles all of that explicitly - see

\`backend/app/core/\` for the actual logic.

**## Architecture**

\`\`\`

backend/

  app/

    core/          detection engine - ingestion, merchant normalization,

                    recurrence detection, pricing analysis, evaluation

                    (pure logic, no framework or LLM dependency)

    agent/          Azure OpenAI tool-calling agent - answers questions

                    using tools that read the real detection output;

                    it cannot invent numbers, only report what the

                    detector actually found

    api/            FastAPI routes, request/response schemas, and an

                    in-memory per-audit result store

    cli.py           optional terminal-only entry point (no API needed)

    main.py           FastAPI app

  scripts/

    generate\_synthetic\_data.py   synthetic dataset + ground-truth generator

  tests/              pytest suite (37 tests) covering core logic, the

                       agent's tools, and the API endpoints

  data/, sample\_output/   pre-generated sample data and report

frontend/

  src/

    App.jsx                main layout

    components/

      UploadPanel.jsx        CSV upload / drag-drop

      StatementTotal.jsx     summary figures

      LedgerList.jsx           detected-subscription list (statement-line UI)

      AuditMark.jsx             hand-drawn circle marking a price increase

      ChatPanel.jsx              "Ask the Auditor" chat, calls the backend agent

    api/client.js               typed fetch wrapper around the backend API

\`\`\`

The core detection engine has zero dependency on the agent or the API - it's

the same tested logic whether you run it via the CLI, the API, or import it

directly in a notebook.

**## Setup**

**### 1. Backend**

\`\`\`bash

cd backend

python3 -m venv .venv

source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env

\# edit .env and fill in your Azure OpenAI credentials (see below) -

\# the app runs fine without them, just with chat disabled

python scripts/generate\_synthetic\_data.py   # creates data/sample\_transactions.csv

python -m pytest tests/ -v                  # 37 tests should pass

uvicorn app.main\:app --reload --port 8000

\`\`\`

Visit \`[http://localhost:8000/docs](http://localhost:8000/docs)\` for interactive API docs.

**#### Azure OpenAI configuration (optional - enables the chat agent)**

\`\`\`dotenv

AZURE\_OPENAI\_ENDPOINT="[https://your-resource-name.openai.azure.com/](https://your-resource-name.openai.azure.com/)"

AZURE\_OPENAI\_API\_KEY="your-key"

AZURE\_OPENAI\_DEPLOYMENT="your-deployment-name"   # the deployment name YOU

                                                   # chose in Azure, not a

                                                   # model name like "gpt-4o"

AZURE\_OPENAI\_API\_VERSION="2024-12-01-preview"

\`\`\`

Without these set, everything except the chat panel works normally -

\`/api/health\` reports \`agent\_configured: false\`, and the frontend disables

the chat input with an explanation instead of erroring.

**### 2. Frontend**

\`\`\`bash

cd frontend

npm install

cp .env.example .env   # defaults to [http://localhost:8000](http://localhost:8000), adjust if needed

npm run dev

\`\`\`

Visit \`[http://localhost:5173](http://localhost:5173)\`. Click "try it with sample data" to see a

full audit immediately, or drop in a real bank CSV export.

**## Running the tests**

\`\`\`bash

cd backend

pytest tests/ -v

\`\`\`

37 tests: merchant normalization, interval/amount detection logic (including

that irregular "habit" spending is correctly excluded), price-change

detection, savings math, the evaluation harness, CSV ingestion across bank

formats, the agent's tool functions, and the API endpoints (the chat

endpoint's tests mock the agent call, so they don't require real Azure

credentials to run).

**## Using it without the frontend**

\`\`\`bash

cd backend

python -m app.cli data/sample\_transactions.csv --evaluate data/ground\_truth.csv

\`\`\`

**## Supported bank CSV formats**

Auto-detected by column headers: Chase, Bank of America, Discover, and a

plain \`date,description,amount\` generic format. Amex's headers happen to be

identical to Bank of America's but use the opposite sign convention for

charges, so that one can't be auto-detected safely - pass it explicitly via

the CLI's \`--bank amex\` flag, or use the generic format for it through the

API.

**## Deployment**

This is two independently deployable services:

**\*\*Backend\*\*** - any Python host that runs an ASGI app (Render, Railway,

Fly.io, an EC2/VM with \`uvicorn\`/\`gunicorn\`, etc.). Set the Azure OpenAI

environment variables in the host's dashboard rather than shipping a \`.env\`

file. Set \`FRONTEND\_ORIGIN\` to your deployed frontend's URL so CORS allows

it.

**\*\*Frontend\*\*** - any static host (Vercel, Netlify, Cloudflare Pages,

S3+CloudFront). Run \`npm run build\`, deploy the \`dist/\` folder, and set

\`VITE\_API\_URL\` (as a build-time environment variable on the host) to your

deployed backend's URL.

**## Design notes / known limitations**

\- Detection requires at least 3 occurrences of a merchant before it's

  classified as recurring, which avoids false positives on short histories

  but means brand-new subscriptions won't show up immediately.

\- The agent's in-memory audit store (\`backend/app/api/store.py\`) is

  process-local and clears on restart - fine for a demo/single-user

  deployment; a real multi-user product would swap this for a database,

  which is the one seam designed for that change.

\- Bank format auto-detection matches on column headers only; where two

  supported banks share identical headers but different sign conventions

  (Bank of America vs. Amex), the format must be specified explicitly -

  a deliberate fail-safe rather than a silent guess.