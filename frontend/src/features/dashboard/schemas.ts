export type DashboardSummary = {
  income_total: string;
  expense_total: string;
  balance: string;
};

export type CategorySpending = {
  category_id: string;
  category_name: string;
  total: string;
};

export type BalancePoint = {
  date: string;
  balance: string;
};

export type Dashboard = {
  start_date: string;
  end_date: string;
  summary: DashboardSummary;
  by_category: CategorySpending[];
  balance_evolution: BalancePoint[];
};
