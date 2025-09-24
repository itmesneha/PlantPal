// src/App.tsx
import { useState } from 'react';
import { AuthForm } from './components/AuthForm';
import { Dashboard } from './components/Dashboard';
import { PlantScanner } from './components/PlantScanner';
import { PlantHealthReport } from './components/PlantHealthReport';
import { Button } from './components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { signOut } from 'aws-amplify/auth';

interface User {
  id: string;
  name: string;
  email: string;
}

interface PlantScanResult {
  species: string;
  confidence: number;
  isHealthy: boolean;
  disease?: string;
  healthScore: number;
  careRecommendations: string[];
}

type AppState = 'auth' | 'dashboard' | 'scanner' | 'results';

function App() {
  const [currentState, setCurrentState] = useState<AppState>('auth');
  const [user, setUser] = useState<User | null>(null);
  const [scanResult, setScanResult] = useState<PlantScanResult | null>(null);
  const [plantStreak] = useState(14); // Mock streak

  const handleAuthSuccess = (userData: User) => {
    setUser(userData);
    setCurrentState('dashboard');
  };

  const handleScanComplete = (scanResult: PlantScanResult) => {
    // Add to garden functionality would go here
    // For now, just set the scan result to show the result
    setScanResult(scanResult);
  };

  const handleAddToGarden = () => {
    // In real app, this would save to backend
    setCurrentState('dashboard');
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      setUser(null);
      setCurrentState('auth');
      setScanResult(null);
    } catch (error) {
      // Handle sign out error silently or show user-friendly message
      setUser(null);
      setCurrentState('auth');
    }
  };

  const handleBack = () => {
    if (currentState === 'scanner') {
      setCurrentState('dashboard');
    } else if (currentState === 'results') {
      setCurrentState('scanner');
    }
  };

  if (!user) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50">
      {currentState !== 'dashboard' && (
        <div className="p-4 bg-white/80 backdrop-blur-sm border-b border-green-100">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="mb-4 hover:bg-green-50 text-green-700"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>
      )}

      {currentState === 'dashboard' && (
        <div className="plant-grow">
          <Dashboard
            user={user}
            onScanPlant={() => setCurrentState('scanner')}
            onSignOut={handleSignOut}
          />
        </div>
      )}

      {currentState === 'scanner' && (
        <div className="p-4 plant-grow">
          <PlantScanner onScanComplete={handleScanComplete} />
        </div>
      )}

      {currentState === 'results' && scanResult && (
        <div className="p-4 plant-grow">
          <PlantHealthReport
            result={scanResult}
            streak={plantStreak}
            onAddToGarden={handleAddToGarden}
          />
        </div>
      )}
    </div>
  );
}

export default App;
