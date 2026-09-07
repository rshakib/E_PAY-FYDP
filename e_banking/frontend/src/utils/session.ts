// Session storage for non-sensitive user session data.
export interface UserSession {
  id: string;
  username: string;
  token: string;
  t: string; // Last successful timestamp
  balance: number;
  accountId: string; // Supabase account ID
  daily_limit: number;
  today_spent: number;
}

const SESSION_KEY = 'user_session';

export function saveUserSession(session: UserSession): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getUserSession(): UserSession | null {
  const sessionData = localStorage.getItem(SESSION_KEY);
  return sessionData ? JSON.parse(sessionData) : null;
}

export function clearUserSession(): void {
  localStorage.removeItem(SESSION_KEY);
}

export function updateUserTimestamp(newT: string): void {
  const session = getUserSession();
  if (session) {
    session.t = newT;
    saveUserSession(session);
  }
}

export function updateUserBalance(newBalance: number): void {
  const session = getUserSession();
  if (session) {
    session.balance = newBalance;
    saveUserSession(session);
  }
}

export function updateTodaySpent(amount: number): void {
  const session = getUserSession();
  if (session) {
    session.today_spent += amount;
    saveUserSession(session);
  }
}

