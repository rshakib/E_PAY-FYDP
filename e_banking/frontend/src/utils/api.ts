// API client to communicate with Python backend
import { getUserSession } from './session';

const configuredApiBaseUrl = import.meta.env.VITE_BACKEND_URL;
const API_BASE_URL = configuredApiBaseUrl
  ? configuredApiBaseUrl.replace(/\/$/, '')
  : import.meta.env.DEV
  ? 'http://localhost:5001'
  : '';

function getAuthHeaders(): Record<string, string> {
  const session = getUserSession();
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (session?.token) {
    headers['Authorization'] = `Bearer ${session.token}`;
  }
  return headers;
}

export interface TransferResponse {
  status: 'success' | 'error' | 'futile';
  message: string;
  new_t?: string;
  new_balance?: number;
}

export async function processTransfer(
  username: string,
  receiver: string,
  amount: number
): Promise<TransferResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/transfer`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        username,
        receiver,
        amount,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        status: data.status || 'error',
        message: data.message || 'Unknown error occurred',
      };
    }

    return {
      status: data.status,
      message: data.message,
      new_t: data.new_t,
      new_balance: data.new_balance,
    };
  } catch (error) {
    console.error('Transfer API error:', error);
    return {
      status: 'error',
      message: 'Failed to connect to backend server',
    };
  }
}

export async function getUser(username: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/user/${username}`, {
      headers: getAuthHeaders(),
    });
    return await response.json();
  } catch (error) {
    console.error('Get user error:', error);
    return null;
  }
}

export async function getTransactionHistory(username: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/transactions/${username}`, {
      headers: getAuthHeaders(),
    });
    return await response.json();
  } catch (error) {
    console.error('Get transactions error:', error);
    return { transactions: [] };
  }
}

export async function getNotifications(username: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/notifications/${username}`, {
      headers: getAuthHeaders(),
    });
    return await response.json();
  } catch (error) {
    console.error('Get notifications error:', error);
    return { notifications: [] };
  }
}

export async function registerAccount(data: { username: string; password: string; nid?: string; activationCode?: string; bp?: string }) {
  try {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    const result = await response.json();
    if (!response.ok) {
      return { status: 'error', message: result.message || 'Registration failed' };
    }
    
    return { status: 'success', message: result.message };
  } catch (error) {
    console.error('Registration API error:', error);
    return { status: 'error', message: 'Failed to connect to backend server' };
  }
}

export async function loginUser(username: string, password: string): Promise<{
  status: string;
  message: string;
  token?: string;
  user?: {
    id: string;
    username: string;
    t: string;
    balance: number;
    accountId: string;
    daily_limit: number;
    today_spent: number;
  };
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await response.json();
    if (!response.ok) {
      return { status: 'error', message: data.message || 'Login failed' };
    }
    return { status: 'success', message: 'Login successful', token: data.token, user: data.user };
  } catch (error) {
    console.error('Login API error:', error);
    const msg = import.meta.env.DEV
      ? 'Cannot connect to backend server. Make sure it is running on port 5001.'
      : 'Cannot connect to backend server. Please verify your internet connection or check backend status.';
    return { status: 'error', message: msg };
  }
}

export async function checkReceiver(username: string): Promise<{ found: boolean; username?: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/check-receiver/${encodeURIComponent(username)}`, {
      headers: getAuthHeaders(),
    });
    if (response.ok) {
      const data = await response.json();
      return { found: true, username: data.username };
    }
    return { found: false };
  } catch (error) {
    console.error('Check receiver error:', error);
    return { found: false };
  }
}
