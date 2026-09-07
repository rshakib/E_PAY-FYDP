// Supabase database service for user operations
import { SUPABASE_URL, SUPABASE_ANON_KEY } from './supabase';

const API_URL = SUPABASE_URL;

interface UserProfile {
  id: string;
  registration_number: string;
  hmac_key_k1: string;
  password_key_k2: string;
  fingerprint_bp: string;
  timestamp_t: string;
  balance: number;
  daily_limit: number;
  today_spent: number;
}

interface UserAccount {
  id: string;
  profile_id: string;
  account_number: string;
  balance: number;
  is_active: boolean;
}

/**
 * Fetch user profile from Supabase
 */
export async function fetchUserProfile(username: string): Promise<UserProfile | null> {
  try {
    const response = await fetch(
      `${API_URL}/rest/v1/profiles?registration_number=eq.${username}&select=*`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );

    const data = await response.json();
    return data.length > 0 ? data[0] : null;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return null;
  }
}

/**
 * Fetch user's primary account
 */
export async function fetchUserAccount(profileId: string): Promise<UserAccount | null> {
  try {
    const response = await fetch(
      `${API_URL}/rest/v1/accounts?profile_id=eq.${profileId}&is_active=eq.true&limit=1`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );

    const data = await response.json();
    return data.length > 0 ? data[0] : null;
  } catch (error) {
    console.error('Error fetching user account:', error);
    return null;
  }
}

/**
 * Fetch transaction history
 */
export async function fetchTransactionHistory(accountId: string, limit: number = 20) {
  try {
    const response = await fetch(
      `${API_URL}/rest/v1/transactions?sender_account_id=eq.${accountId}&order=created_at.desc&limit=${limit}`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching transaction history:', error);
    return [];
  }
}

/**
 * Search for receiver by username
 */
export async function searchReceiver(username: string): Promise<UserProfile | null> {
  try {
    const response = await fetch(
      `${API_URL}/rest/v1/profiles?registration_number=eq.${username}&select=id,registration_number`,
      {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
        },
      }
    );

    const data = await response.json();
    return data.length > 0 ? data[0] : null;
  } catch (error) {
    console.error('Error searching receiver:', error);
    return null;
  }
}
