// src/App.tsx
import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthForm } from './components/AuthForm';
import { Dashboard } from './components/Dashboard';
import { PlantScanner } from './components/PlantScanner';
import { PlantHealthReport } from './components/PlantHealthReport';
import { Button } from './components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { signOut, getCurrentUser } from 'aws-amplify/auth';
import { userService, User } from './services/userService';
import { Callback } from './components/Callback';
import { ToastProvider, useToast } from './context/ToastContext';

interface PlantScanResult {
  species: string;
  confidence: number;
  isHealthy: boolean;
  disease?: string;
  healthScore: number;
  careRecommendations: string[];
}

type AppState = 'loading' | 'auth' | 'dashboard' | 'scanner' | 'results';

function AppWrapper() {
  return (
    <Router>
      <ToastProvider>
        <Routes>
          <Route path="/callback" element={<Callback />} />
          <Route path="/*" element={<App />} />
        </Routes>
      </ToastProvider>
    </Router>
  );
}

function App() {
  const { showSuccess } = useToast();
  const [currentState, setCurrentState] = useState<AppState>('loading');
  const [user, setUser] = useState<User | null>(null);
  const [scanResult, setScanResult] = useState<PlantScanResult | null>(null);
  const [originalImageFile, setOriginalImageFile] = useState<File | null>(null); // Store original image
  const [plantStreak] = useState(14); // Mock streak
  const [rescanPlantId, setRescanPlantId] = useState<string | null>(null); // Track plant being rescanned

  // Check if user is already authenticated on app load
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const currentUser = await getCurrentUser();
      if (currentUser) {
        console.log('✅ User is authenticated with Cognito:', currentUser);
        // User is authenticated, try to sync with backend
        try {
          const backendUser = await userService.syncUserAfterAuth();
          setUser(backendUser);
          setCurrentState('dashboard');
        } catch (backendError) {
          console.error('Backend sync failed!, but user is authenticated:', backendError);
          // Fall back to showing auth form - user needs to sign in again
          setCurrentState('auth');
        }
      } else {
        console.log('❌ No authenticated user found');
        setCurrentState('auth');
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      setCurrentState('auth');
    }
  };

  const handleAuthSuccess = async (userData: { id: string; name: string; email: string; }) => {
    try {
      // Sync user with backend after authentication
      const backendUser = await userService.syncUserAfterAuth();
      setUser(backendUser);
      setCurrentState('dashboard');
    } catch (error) {
      console.error('Failed to sync user with backend:', error);
      // Still proceed to dashboard with Cognito user data
      const fallbackUser: User = {
        id: userData.id,
        cognito_user_id: userData.id,
        email: userData.email,
        name: userData.name,
        created_at: new Date().toISOString()
      };
      setUser(fallbackUser);
      setCurrentState('dashboard');
    }
  };

  const handleScanComplete = (scanResult: PlantScanResult, originalFile: File) => {
    // Store the scan result and original image file
    setScanResult(scanResult);
    setOriginalImageFile(originalFile);
    setCurrentState('results');
  };

  const handleScanPlant = (plantId?: string) => {
    // Set the plant ID if rescanning an existing plant
    setRescanPlantId(plantId || null);
    setCurrentState('scanner');
  };

  const handleAddToGarden = (plantId: string, plantName: string) => {
    if (rescanPlantId) {
      // This was a rescan - data has already been updated in the backend
      console.log(`🔄 Plant "${plantName}" (ID: ${rescanPlantId}) rescanned successfully!`);
      showSuccess(`Successfully updated "${plantName}" health data!`, 4000);
    } else {
      // This was a new plant scan - plant was added to garden
      console.log(`🌱 Plant "${plantName}" (ID: ${plantId}) added to garden!`);
      showSuccess(`Successfully added "${plantName}" to your garden!`, 4000);
    }
    
    // Navigate back to dashboard after a short delay
    setTimeout(() => {
      setCurrentState('dashboard');
      
      // Clear the scan results and rescan state
      setScanResult(null);
      setOriginalImageFile(null);
      setRescanPlantId(null);
    }, 1500); // Give user time to see the success message
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
      // Clear rescan state when going back from scanner
      setRescanPlantId(null);
    } else if (currentState === 'results') {
      setCurrentState('scanner');
    }
  };

  // Loading state
  if (currentState === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-emerald-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-green-600">Loading PlantPal...</p>
        </div>
      </div>
    );
  }

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
            onScanPlant={handleScanPlant}
            onSignOut={handleSignOut}
          />
        </div>
      )}

      {currentState === 'scanner' && (
        <div className="p-4 plant-grow">
          <PlantScanner 
            onScanComplete={handleScanComplete}
            plantId={rescanPlantId || undefined}
          />
        </div>
      )}

      {currentState === 'results' && scanResult && (
        <div className="p-4 plant-grow">
          <PlantHealthReport
            result={scanResult}
            streak={plantStreak}
            onAddToGarden={handleAddToGarden}
            originalImage={originalImageFile || undefined}
            isRescan={!!rescanPlantId}
            rescanPlantId={rescanPlantId || undefined}
          />
        </div>
      )}
    </div>
  );
}

export default AppWrapper;
