# Sprout Budget App

Sprout is a personal finance dashboard for tracking transactions, budgets, and savings goals. Users authenticate with Supabase, connect bank accounts via Plaid Link, and all financial data is stored in Postgres with Row Level Security enforced per user. The Next.js frontend only handles auth/session; all data access flows through a FastAPI backend that verifies Supabase JWTs and queries Postgres.

## Features

🔐 **Authentication**: Secure user authentication using Supabase  
🏦 **Bank Integration**: Connect and sync bank accounts via Plaid  
🤖 **AI-Assisted Categorization**: Intelligent transaction categorization using AI agents with rule-based fallbacks  
💳 **Transaction Management**: Automatic transaction syncing via Plaid transactions sync with AI categorization  
📊 **Dashboard**: Comprehensive financial overview with income, expenses, and net worth  
💰 **Budgets**: Create and track monthly budgets by category  
🎯 **Goals**: Set savings goals and track progress over time  
📱 **Accounts Management**: Manage both Plaid-connected and manual accounts  
🔍 **Transaction Filtering**: Filter transactions by category, date range, and amount  
📅 **Month Navigation**: View transactions organized by month with easy navigation  
✏️ **Manual Transactions**: Add and edit transactions manually  
📈 **Spending Breakdown**: Visual breakdown of spending by category  
🔄 **Sync on Demand**: Manual "Sync" button to sync bank transactions when needed  
📱 **Responsive Design**: Modern UI with Tailwind CSS

## Tech Stack

**Frontend:**

- Next.js (App Router)
- React
- TypeScript
- Tailwind CSS
- Radix UI
- Lucide React Icons
- Recharts

**Backend:**

- FastAPI
- Python 3.12
- SQLAlchemy
- PostgreSQL
- Plaid API
- LangChain (agent orchestration)
- OpenAI API (transaction classification)

**Authentication & Database:**

- Supabase Auth + Postgres
- Frontend uses publishable key for auth only
- All database access goes through FastAPI (RLS enforced)

**Testing:**

- Vitest
- React Testing Library
- Pytest

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.12+
- PostgreSQL database (or Supabase)
- Plaid account (for bank integration)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Budget\ App
   ```

2. **Backend Setup**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Frontend Setup**

   ```bash
   cd sprout
   npm install
   ```

4. **Environment Variables**

   Create `.env` files in both `backend/` and `sprout/`:

   **Backend `.env`:**

   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/budgetapp
   PLAID_CLIENT_ID=your_plaid_client_id
   PLAID_SECRET=your_plaid_secret  # Environment-specific (sandbox/dev/prod)
   PLAID_ENV=production  # Options: sandbox, development, production
   SUPABASE_URL=your_supabase_url
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o-mini  # Model used for AI categorization agents
   DEBUG=true  # Set to false in production
   ```

   **Frontend `.env.local`:**

   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. **Database Setup**

   The database schema is managed through SQL migration scripts in `backend/migrations/`. Apply migrations as needed, or use Supabase's migration tools if using Supabase Postgres.

6. **Start Development Servers**

   **Backend:**

   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   **Frontend:**

   ```bash
   cd sprout
   npm run dev
   ```

7. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
Budget App/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Auth, config
│   │   ├── db/           # Database models and session
│   │   └── agent/        # AI categorization agents
│   ├── tests/            # Backend tests
│   └── requirements.txt
├── sprout/               # Next.js frontend
│   ├── app/              # Next.js app directory
│   │   ├── accounts/     # Accounts page
│   │   ├── budgets/      # Budgets page
│   │   ├── dashboard/    # Dashboard page
│   │   ├── goals/       # Goals page
│   │   ├── transactions/ # Transactions page
│   │   └── components/   # React components
│   ├── lib/              # Utilities and API client
│   └── package.json
└── README.md
```

## Key Features Explained

### Bank Integration (Plaid)

- Connect multiple bank accounts securely via Plaid Link
- Sync transactions on demand with manual "Sync" button
- Support for checking, savings, credit cards, and investment accounts
- Incremental sync using Plaid's cursor-based pagination

### AI-Assisted Transaction Categorization

- **Ingestion Agent**: Normalizes merchant names from transaction descriptions
- **Classification Agent**: Automatically categorizes transactions using OpenAI (GPT-4o-mini)
- **Subscription Detection**: Identifies recurring subscriptions automatically
- **Tag Generation**: Adds relevant tags to transactions for better organization
- **Batch Processing**: Process hundreds of uncategorized transactions with one click
- **Smart Rules**: Uses rule-based categorization for common patterns before AI processing. This reduces latency, cost, and misclassification for common transaction patterns.
- **Caching**: Intelligent caching to reduce API costs and improve performance

### Transaction Management

- Transaction syncing via Plaid transactions sync API
- Automatic categorization of transactions via AI agents
- Manual transaction creation and editing
- Filter by category, date, amount, and search terms
- Month-based navigation for easy browsing
- Transaction stats (total, income, expenses) calculated server-side
- One-click auto-categorization for all uncategorized transactions

### Budgets

- Create monthly budgets by category
- Track spending against budget limits
- Month/year navigation for historical budgets
- Visual indicators for budget status

### Goals

- Set savings goals with target amounts and dates
- Track progress with automatic updates
- Link transactions to goals
- Goal badges on transactions

### Dashboard

- Financial overview at a glance
- Income, expenses, savings, and net worth
- Spending breakdown by category
- Recent transactions
- Asset tracking

## API Endpoints

- `GET /api/dashboard` - Dashboard data
- `GET /api/transactions` - List transactions with filters
- `GET /api/transactions/stats` - Transaction statistics
- `POST /api/transactions` - Create transaction
- `GET /api/budgets` - List budgets
- `POST /api/budgets` - Create budget
- `GET /api/goals` - List goals
- `POST /api/goals` - Create goal
- `GET /api/accounts` - List accounts
- `POST /api/plaid/link` - Get Plaid Link token
- `POST /api/plaid/exchange` - Exchange Plaid public token
- `POST /api/plaid/sync` - Sync Plaid transactions
- `POST /api/agents/process-transaction/{transaction_id}` - Process single transaction with AI agents
- `POST /api/agents/process-uncategorized` - Batch process all uncategorized transactions

## Security

- **Row Level Security (RLS)**: Enabled on all user tables in Postgres
- **JWT Verification**: FastAPI verifies Supabase JWT tokens and resolves `auth_user_id` → `users.id`
- **Server-Side Auth**: All database queries enforce `user_id = current_app_user_id()` via RLS policies
- **No Direct DB Access**: Frontend never queries Postgres directly; all data access flows through FastAPI backend
- **Publishable Key Only**: Frontend uses Supabase publishable key for auth sessions only, not for data access

## Testing

**Backend:**

```bash
cd backend
pytest
```

**Frontend:**

```bash
cd sprout
npm test
```

## License

This project is private and proprietary.

## Contact

For questions or contributions, please open an issue or contact via GitHub profile.
