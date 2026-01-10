export interface Account {
  id: number;
  user_id: number;
  name: string;
  account_type: string;
  provider: string;
  balance: string; // Decimal as string from backend
  is_active: boolean;
}

export const MOCK_ACCOUNTS: Account[] = [
  {
    id: 1,
    user_id: 1,
    name: "Chase Checking",
    account_type: "depository",
    provider: "plaid",
    balance: "5432.18",
    is_active: true,
  },
  {
    id: 2,
    user_id: 1,
    name: "Ally Savings",
    account_type: "depository",
    provider: "plaid",
    balance: "12500.00",
    is_active: true,
  },
  {
    id: 3,
    user_id: 1,
    name: "Chase Freedom Credit Card",
    account_type: "credit",
    provider: "plaid",
    balance: "-1234.56",
    is_active: true,
  },
  {
    id: 4,
    user_id: 1,
    name: "Fidelity Brokerage",
    account_type: "investment",
    provider: "plaid",
    balance: "45678.90",
    is_active: true,
  },
  {
    id: 5,
    user_id: 1,
    name: "Cash",
    account_type: "cash",
    provider: "manual",
    balance: "250.00",
    is_active: true,
  },
  {
    id: 6,
    user_id: 1,
    name: "Old Bank Account",
    account_type: "depository",
    provider: "plaid",
    balance: "0.00",
    is_active: false,
  },
];
