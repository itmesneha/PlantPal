import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { storefrontService, CoinBalance } from '../services/storefrontService';
import { X, Sparkles } from 'lucide-react';

interface StoreProduct {
  id: string;
  name: string;
  price: string;
}

interface Store {
  id: string;
  name: string;
  location: string;
  website: string;
  products: StoreProduct[];
}

const STORES: Store[] = [
  {
    id: 'store-1',
    name: 'Botanic & Bloom',
    location: 'Orchard Road, Singapore',
    website: 'https://example.com/botanic-bloom',
    products: [
      { id: 'p1', name: 'Monstera Deliciosa', price: 'S$39.90' },
      { id: 'p2', name: 'Snake Plant', price: 'S$24.90' },
    ],
  },
  {
    id: 'store-2',
    name: 'Urban Jungle SG',
    location: 'Tiong Bahru, Singapore',
    website: 'https://example.com/urban-jungle-sg',
    products: [
      { id: 'p1', name: 'ZZ Plant', price: 'S$32.00' },
      { id: 'p2', name: 'Fiddle Leaf Fig', price: 'S$58.00' },
    ],
  },
  {
    id: 'store-3',
    name: 'Plant House Co. SG',
    location: 'Katong, Singapore',
    website: 'https://example.com/plant-house-sg',
    products: [
      { id: 'p1', name: 'Pothos', price: 'S$18.90' },
      { id: 'p2', name: 'Spider Plant', price: 'S$15.90' },
    ],
  },
  {
    id: 'store-4',
    name: 'Gardeners Hub SG',
    location: 'Jurong, Singapore',
    website: 'https://example.com/gardeners-hub-sg',
    products: [
      { id: 'p1', name: 'Succulent Mix', price: 'S$12.90' },
      { id: 'p2', name: 'Terracotta Pots (Set of 3)', price: 'S$19.90' },
    ],
  },
  {
    id: 'store-5',
    name: 'Roots & Shoots SG',
    location: 'Bukit Timah, Singapore',
    website: 'https://example.com/roots-shoots-sg',
    products: [
      { id: 'p1', name: 'Peace Lily', price: 'S$28.00' },
      { id: 'p2', name: 'Aloe Vera', price: 'S$14.50' },
    ],
  },
];

const COUPON_TIERS = [
  { label: '5% Off', discount: 5, cost: 50 },
  { label: '10% Off', discount: 10, cost: 100 },
  { label: '20% Off', discount: 20, cost: 150 },
];

interface StorefrontProps {
  onBalanceChange?: (balance: CoinBalance | null) => void;
}

type PurchasedCoupon = {
  storeName: string;
  discount: number;
  code: string;
};

export function Storefront({ onBalanceChange }: StorefrontProps) {
  const [balance, setBalance] = useState<CoinBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const [purchasedCoupon, setPurchasedCoupon] = useState<PurchasedCoupon | null>(null);

  const refresh = async () => {
    try {
      setLoading(true);
      setError('');
      setMessage('');
      const b = await storefrontService.getBalance();
      setBalance(b);
      onBalanceChange?.(b);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load balance');
      onBalanceChange?.(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  const handlePurchase = async (store: Store, discount: number, cost: number) => {
    try {
      setMessage('');
      const res = await storefrontService.purchaseCoupon({
        store_id: store.id,
        store_name: store.name,
        discount_percent: discount,
        cost_coins: cost,
      });
      if (res.success) {
        const coupon = res.coupon;
        if (coupon) {
          setPurchasedCoupon({
            storeName: store.name,
            discount,
            code: coupon.code,
          });
          setMessage(`✅ Coupon purchased: ${coupon.code} (${discount}% off at ${store.name})`);
        } else {
          setMessage(`✅ Coupon purchased! Enjoy ${discount}% off at ${store.name}.`);
        }
        await refresh();
      } else {
        setMessage(`❌ ${res.message}`);
      }
    } catch (e) {
      setMessage(`❌ ${(e as Error).message}`);
    }
  };

  return (
    <>
      {purchasedCoupon && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
          onClick={() => setPurchasedCoupon(null)}
        >
          <div
            className="relative w-full max-w-md overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-500 via-green-500 to-lime-400 p-8 text-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setPurchasedCoupon(null)}
              className="absolute right-4 top-4 rounded-full bg-white/20 p-2 transition hover:bg-white/30"
              aria-label="Close coupon popup"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.35em] text-white/80">
              <Sparkles className="h-4 w-4" />
              Special Reward
            </div>
            <h3 className="mt-4 text-3xl font-semibold leading-tight">Exclusive Coupon Unlocked</h3>
            <p className="mt-2 text-sm text-white/90">
              Enjoy {purchasedCoupon.discount}% off at{' '}
              <span className="font-semibold">{purchasedCoupon.storeName}</span>.
            </p>
            <div className="mt-6 rounded-2xl border border-white/30 bg-white/10 p-6 text-center shadow-inner">
              <div className="text-xs uppercase tracking-[0.5em] text-white/60">Discount Code</div>
              <div className="mt-4 font-mono text-3xl font-bold tracking-[0.4em]">
                {purchasedCoupon.code}
              </div>
              <p className="mt-4 text-sm text-white/80">
                This is a one-time code, save it.
              </p>
            </div>
            <div className="mt-6 flex justify-center">
              <button
                type="button"
                onClick={() => setPurchasedCoupon(null)}
                className="rounded-full bg-white px-6 py-2 text-sm font-semibold text-emerald-600 shadow-lg transition hover:bg-white/90"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">🪴🏪</span>
              Storefront
            </CardTitle>
            <CardDescription>Spend your coins to get discount coupons from partner stores</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div>Loading...</div>
            ) : error ? (
              <div className="text-red-600">{error}</div>
            ) : balance ? (
              <div className="flex flex-wrap gap-6">
                <div className="p-4 rounded-lg border bg-white">
                  <div className="text-sm text-gray-600">Coins Earned</div>
                  <div className="text-2xl font-bold text-green-700">{balance.coins_earned}</div>
                </div>
                <div className="p-4 rounded-lg border bg-white">
                  <div className="text-sm text-gray-600">Coins Spent</div>
                  <div className="text-2xl font-bold text-red-600">{balance.coins_spent}</div>
                </div>
                <div className="p-4 rounded-lg border bg-white">
                  <div className="text-sm text-gray-600">Coins Remaining</div>
                  <div className="text-2xl font-bold text-yellow-600">{balance.coins_remaining}</div>
                </div>
              </div>
            ) : null}
            {message && (
              <div className="mt-4 text-sm">{message}</div>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {STORES.map((store) => (
            <Card key={store.id} className="overflow-hidden">
              <CardHeader className="border-b bg-gradient-to-r from-green-50 to-emerald-50">
                <CardTitle className="flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <span className="text-xl">🌿</span>
                    {store.name}
                  </span>
                  <a href={store.website} target="_blank" rel="noreferrer" className="text-sm text-blue-600 underline">Visit site</a>
                </CardTitle>
                <CardDescription>{store.location}</CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div>
                  <div className="mb-2 flex items-center gap-2 text-sm text-gray-600"><span>🧺</span> Popular Products</div>
                  <ul className="grid gap-2">
                    {store.products.map((p) => (
                      <li key={p.id} className="flex items-center justify-between rounded border bg-white p-2">
                        <span>{p.name}</span>
                        <span className="font-medium text-gray-700">{p.price}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <div className="mb-2 flex items-center gap-2 text-sm text-gray-600"><span>🎟️</span> Buy Discount Coupon</div>
                  <div className="flex flex-wrap gap-2">
                    {COUPON_TIERS.map((tier) => (
                      <Button key={tier.discount}
                        onClick={() => handlePurchase(store, tier.discount, tier.cost)}
                        disabled={!!balance && balance.coins_remaining < tier.cost}
                        className="border"
                        variant="outline"
                      >
                        {tier.label} · {tier.cost} coins
                      </Button>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </>
  );
}

export default Storefront;

