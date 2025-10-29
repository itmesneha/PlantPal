import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface CoinBalance {
  coins_earned: number;
  coins_spent: number;
  coins_remaining: number;
}

export interface Coupon {
  id: string;
  store_id: string;
  store_name: string;
  discount_percent: number;
  cost_coins: number;
  code: string;
  redeemed: boolean;
  expires_at?: string | null;
  created_at: string;
}

export interface PurchaseCouponRequest {
  store_id: string;
  store_name: string;
  discount_percent: number; // 10, 20, 35
  cost_coins: number; // 50, 100, 200
}

class StorefrontService {
  private getAuthToken = async (): Promise<string> => {
    const session = await fetchAuthSession();
    const idToken = session.tokens?.idToken;
    if (!idToken) throw new Error('No ID token available');
    return idToken.toString();
  };

  getBalance = async (): Promise<CoinBalance> => {
    const token = await this.getAuthToken();
    const res = await fetch(`${API_BASE_URL}/api/v1/storefront/balance`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch coin balance');
    return res.json();
  };

  getCoupons = async (): Promise<Coupon[]> => {
    const token = await this.getAuthToken();
    const res = await fetch(`${API_BASE_URL}/api/v1/storefront/coupons`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to fetch coupons');
    return res.json();
  };

  purchaseCoupon = async (payload: PurchaseCouponRequest): Promise<{ success: boolean; message: string; coupon?: Coupon }> => {
    const token = await this.getAuthToken();
    const res = await fetch(`${API_BASE_URL}/api/v1/storefront/purchase`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || 'Failed to purchase coupon');
    }
    return res.json();
  };
}

export const storefrontService = new StorefrontService();
export default storefrontService;


