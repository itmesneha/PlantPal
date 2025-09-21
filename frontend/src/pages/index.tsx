import { useState } from 'react';
import { AuthForm } from '../components/AuthForm';
import { Dashboard } from '../components/Dashboard';
import { PlantScanner } from '../components/PlantScanner';
import { PlantHealthReport } from '../components/PlantHealthReport';
import { Button } from '../components/ui/button';
import { ArrowLeft } from 'lucide-react';

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

export default function App() {
  const [currentState, setCurrentState] = useState<AppState>('auth');
  const [user, setUser] = useState<User | null>(null);
  const [scanResult, setScanResult] = useState<PlantScanResult | null>(null);
  const [plantStreak, setPlantStreak] = useState(14); // Mock streak

  const handleAuthSuccess = (userData: User) => {
    setUser(userData);
    setCurrentState('dashboard');
  };

  const handleScanComplete = (result: PlantScanResult) => {
    setScanResult(result);
    setCurrentState('results');
  };

  const handleAddToGarden = () => {
    // In real app, this would save to database
    console.log('Adding plant to garden:', scanResult);
    setCurrentState('dashboard');
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
    <div className="min-h-screen bg-background">
      {currentState !== 'dashboard' && (
        <div className="p-4">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </div>
      )}

      {currentState === 'dashboard' && (
        <Dashboard
          user={user}
          onScanPlant={() => setCurrentState('scanner')}
        />
      )}

      {currentState === 'scanner' && (
        <div className="p-4">
          <PlantScanner onScanComplete={handleScanComplete} />
        </div>
      )}

      {currentState === 'results' && scanResult && (
        <div className="p-4">
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