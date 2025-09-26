// src/components/Callback.tsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export const Callback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    async function handleCognitoRedirect() {
      try {
        // Here you can use Cognito signUp/signIn functions if needed
        // Or use current authenticated session via modular API
        console.log('✅ Callback triggered');
        navigate('/'); // redirect to main app
      } catch (error) {
        console.error('Callback handling failed:', error);
        navigate('/auth'); // fallback to login
      } 
    }

    handleCognitoRedirect();
  }, [navigate]);

  return <div>Logging in...</div>;
};
