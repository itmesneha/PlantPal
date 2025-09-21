import { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Leaf } from 'lucide-react';

interface AuthFormProps {
  onAuthSuccess: (user: { id: string; name: string; email: string }) => void;
}

export function AuthForm({ onAuthSuccess }: AuthFormProps) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>, isLogin: boolean) => {
    e.preventDefault();
    setLoading(true);
    
    // Mock authentication - in real app this would call your auth service
    setTimeout(() => {
      const mockUser = {
        id: '1',
        name: 'Plant Lover',
        email: 'user@example.com'
      };
      onAuthSuccess(mockUser);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-emerald-100 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-green-500 rounded-full flex items-center justify-center mb-4">
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <CardTitle>PlantCare Pro</CardTitle>
          <CardDescription>
            Identify plants, track health, and earn achievements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="login" className="space-y-4">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>
            
            <TabsContent value="login">
              <form onSubmit={(e) => handleSubmit(e, true)} className="space-y-4">
                <div>
                  <Input type="email" placeholder="Email" required />
                </div>
                <div>
                  <Input type="password" placeholder="Password" required />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
            </TabsContent>
            
            <TabsContent value="register">
              <form onSubmit={(e) => handleSubmit(e, false)} className="space-y-4">
                <div>
                  <Input type="text" placeholder="Full Name" required />
                </div>
                <div>
                  <Input type="email" placeholder="Email" required />
                </div>
                <div>
                  <Input type="password" placeholder="Password" required />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? 'Creating account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}