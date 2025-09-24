import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription } from './ui/alert';
import { Leaf } from 'lucide-react';
import { signUp, signIn, confirmSignUp, resetPassword, confirmResetPassword, type SignUpOutput, getCurrentUser } from 'aws-amplify/auth';

interface AuthFormProps {
  onAuthSuccess: (user: { id: string; name: string; email: string }) => void;
}

export function AuthForm({ onAuthSuccess }: AuthFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmationRequired, setConfirmationRequired] = useState(false);
  const [email, setEmail] = useState('');
  const [confirmationCode, setConfirmationCode] = useState('');
  const [resetPasswordMode, setResetPasswordMode] = useState(false);
  const [resetCodeSent, setResetCodeSent] = useState(false);
  const [newPassword, setNewPassword] = useState('');

  // Check for existing authenticated user on component mount
  useEffect(() => {
    const checkCurrentUser = async () => {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          onAuthSuccess({
            id: currentUser.userId,
            name: 'Plant Lover',
            email: currentUser.username
          });
        }
      } catch (err) {
        // No existing authenticated user
      }
    };
    
    checkCurrentUser();
  }, [onAuthSuccess]);

  // When switching tabs
  const handleTabChange = (value: string) => {
    setError('');
    setResetPasswordMode(false);
    setResetCodeSent(false);
    setConfirmationCode('');
    setNewPassword('');
  };

  const handleSignUp = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const fullName = formData.get('fullName') as string;
    const emailValue = formData.get('email') as string;
    const password = formData.get('password') as string;

    try {
      const { isSignUpComplete, nextStep }: SignUpOutput = await signUp({
        username: emailValue,
        password,
        options: {
          userAttributes: {
            email: emailValue,
            name: fullName,
          }
        }
      });

      setEmail(emailValue);
      
      if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        setConfirmationRequired(true);
        setError('Please check your email for a verification code.');
      } else if (isSignUpComplete) {
        // Auto sign in after successful sign up
        await handleSignIn(emailValue, password);
      }
    } catch (err: any) {
      // Handle specific sign-up errors more securely
      if (err.name === 'UsernameExistsException') {
        setError('An account with this email already exists. Please sign in instead.');
      } else if (err.name === 'InvalidPasswordException') {
        setError('Password must be at least 8 characters with uppercase, lowercase, and numbers.');
      } else {
        setError('Sign up failed. Please check your information and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (emailValue: string, passwordValue: string) => {
    try {
      // First check if user is already signed in
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          onAuthSuccess({
            id: currentUser.userId,
            name: 'Plant Lover', // You can get this from user attributes later
            email: emailValue
          });
          return;
        }
      } catch (currentUserError) {
        // User not signed in, continue with sign-in process
      }

      const signInResult = await signIn({
        username: emailValue,
        password: passwordValue
      });

      if (signInResult.isSignedIn) {
        onAuthSuccess({
          id: emailValue,
          name: 'Plant Lover', // You can get this from user attributes later
          email: emailValue
        });
      } else if (signInResult.nextStep) {
        // Handle additional sign-in steps if needed
        setError('Sign in requires additional steps: ' + signInResult.nextStep.signInStep);
      } else {
        setError('Sign in incomplete. Please try again.');
      }
    } catch (err: any) {
      // Check if the error is because user is already signed in
      if (err.name === 'UserAlreadyAuthenticatedException' || err.message?.includes('already authenticated')) {
        try {
          const currentUser = await getCurrentUser();
          onAuthSuccess({
            id: currentUser.userId,
            name: 'Plant Lover',
            email: emailValue
          });
          return;
        } catch (getCurrentUserErr) {
          // Could not get current user
        }
      }
      
      // Generic error message for security - don't reveal if user exists or not
      setError('Invalid email or password. Please check your credentials and try again.');
    }
  };

  const handleForgotPassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const emailValue = formData.get('email') as string;

    try {
      await resetPassword({ username: emailValue });
      setEmail(emailValue);
      setResetCodeSent(true);
      setError('Password reset code sent to your email. Please check your inbox.');
    } catch (err: any) {
      if (err.name === 'UserNotFoundException') {
        // For security, don't reveal if user exists or not
        setError('If an account exists with this email, a reset code will be sent.');
      } else {
        setError('Failed to send password reset code. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmResetPassword = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await confirmResetPassword({
        username: email,
        confirmationCode,
        newPassword
      });

      setError('Password reset successful! Please sign in with your new password.');
      setResetPasswordMode(false);
      setResetCodeSent(false);
      setConfirmationCode('');
      setNewPassword('');
    } catch (err: any) {
      if (err.name === 'CodeMismatchException' || err.name === 'ExpiredCodeException') {
        setError('Invalid or expired reset code. Please request a new one.');
      } else if (err.name === 'InvalidPasswordException') {
        setError('Password must be at least 8 characters with uppercase, lowercase, and numbers.');
      } else {
        setError('Failed to reset password. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const emailValue = formData.get('email') as string;
    const passwordValue = formData.get('password') as string;

    await handleSignIn(emailValue, passwordValue);
    setLoading(false);
  };

  const handleConfirmSignUp = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { isSignUpComplete } = await confirmSignUp({
        username: email,
        confirmationCode
      });

      if (isSignUpComplete) {
        setConfirmationRequired(false);
        setError('Account confirmed! Please sign in.');
        // You could auto sign in here if you stored the password
      }
    } catch (err: any) {
      // Generic error for email confirmation
      if (err.name === 'CodeMismatchException' || err.name === 'ExpiredCodeException') {
        setError('Invalid or expired verification code. Please check your email.');
      } else {
        setError('Verification failed. Please try again or request a new code.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (confirmationRequired) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 px-4 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-green-200 rounded-full opacity-20 animate-pulse"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-200 rounded-full opacity-10 animate-pulse delay-500"></div>
        </div>
        
        <Card className="w-full max-w-md relative z-10 shadow-2xl border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mb-6 shadow-lg">
              <Leaf className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              Verify Your Email
            </CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-2">
              Enter the verification code sent to {email}
            </CardDescription>
          </CardHeader>
          <CardContent className="px-8 pb-8">
            <form onSubmit={handleConfirmSignUp} className="space-y-5">
              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertDescription className="text-red-600">{error}</AlertDescription>
                </Alert>
              )}
              <div className="space-y-2">
                <Input 
                  type="text" 
                  placeholder="Enter verification code" 
                  required 
                  value={confirmationCode}
                  onChange={(e) => setConfirmationCode(e.target.value)}
                  className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300" 
                disabled={loading}
              >
                {loading ? 'Verifying...' : 'Verify Email'}
              </Button>
              <Button 
                type="button"
                variant="ghost"
                className="w-full text-green-600 hover:text-green-700"
                onClick={() => setConfirmationRequired(false)}
              >
                Back to Sign In
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Reset Password Flow
  if (resetPasswordMode) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 px-4 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-green-200 rounded-full opacity-20 animate-pulse"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-200 rounded-full opacity-10 animate-pulse delay-500"></div>
        </div>
        
        <Card className="w-full max-w-md relative z-10 shadow-2xl border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-8">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mb-6 shadow-lg">
              <Leaf className="w-8 h-8 text-white" />
            </div>
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
              {resetCodeSent ? 'Reset Password' : 'Forgot Password'}
            </CardTitle>
            <CardDescription className="text-lg text-gray-600 mt-2">
              {resetCodeSent ? `Enter the code sent to ${email}` : 'Enter your email to reset your password'}
            </CardDescription>
          </CardHeader>
          <CardContent className="px-8 pb-8">
            {!resetCodeSent ? (
              <form onSubmit={handleForgotPassword} className="space-y-5">
                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-600">{error}</AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Input 
                    name="email"
                    type="email" 
                    placeholder="Enter your email" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300" 
                  disabled={loading}
                >
                  {loading ? 'Sending...' : 'Send Reset Code'}
                </Button>
                <Button 
                  type="button"
                  variant="ghost"
                  className="w-full text-green-600 hover:text-green-700"
                  onClick={() => setResetPasswordMode(false)}
                >
                  Back to Sign In
                </Button>
              </form>
            ) : (
              <form onSubmit={handleConfirmResetPassword} className="space-y-5">
                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-600">{error}</AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Input 
                    type="text" 
                    placeholder="Enter reset code" 
                    required 
                    value={confirmationCode}
                    onChange={(e) => setConfirmationCode(e.target.value)}
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <div className="space-y-2">
                  <Input 
                    type="password" 
                    placeholder="Enter new password" 
                    required 
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300" 
                  disabled={loading}
                >
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
                <Button 
                  type="button"
                  variant="ghost"
                  className="w-full text-green-600 hover:text-green-700"
                  onClick={() => {
                    setResetPasswordMode(false);
                    setResetCodeSent(false);
                    setConfirmationCode('');
                    setNewPassword('');
                  }}
                >
                  Back to Sign In
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 px-4 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-green-200 rounded-full opacity-20 animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-200 rounded-full opacity-20 animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-teal-200 rounded-full opacity-10 animate-pulse delay-500"></div>
      </div>
      
      <Card className="w-full max-w-md relative z-10 shadow-2xl border-0 bg-white/90 backdrop-blur-sm">
        <CardHeader className="text-center pb-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mb-6 shadow-lg">
            <Leaf className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
            PlantPal 🌱
          </CardTitle>
          <CardDescription className="text-lg text-gray-600 mt-2">
            Identify plants, track health, and grow your green thumb
          </CardDescription>
        </CardHeader>
        <CardContent className="px-8 pb-8">
          <Tabs defaultValue="login" onValueChange={handleTabChange} className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 bg-green-50 p-1 rounded-xl">
              <TabsTrigger 
                value="login" 
                className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-green-600 font-medium"
              >
                Sign In
              </TabsTrigger>
              <TabsTrigger 
                value="register"
                className="rounded-lg data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-green-600 font-medium"
              >
                Sign Up
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="login" className="space-y-4">
              <form onSubmit={handleLogin} data-login="true" className="space-y-5">
                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-600">{error}</AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Input 
                    name="email"
                    type="email" 
                    placeholder="Enter your email" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <div className="space-y-2">
                  <Input 
                    name="password"
                    type="password" 
                    placeholder="Enter your password" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300" 
                  disabled={loading}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
                <div className="text-center">
                  <Button 
                    type="button"
                    variant="ghost"
                    className="text-green-600 hover:text-green-700 text-sm"
                    onClick={() => setResetPasswordMode(true)}
                  >
                    Forgot Password?
                  </Button>
                </div>
              </form>
            </TabsContent>
            
            <TabsContent value="register" className="space-y-4">
              <form onSubmit={handleSignUp} className="space-y-5">
                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertDescription className="text-red-600">{error}</AlertDescription>
                  </Alert>
                )}
                <div className="space-y-2">
                  <Input 
                    name="fullName"
                    type="text" 
                    placeholder="Full Name" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <div className="space-y-2">
                  <Input 
                    name="email"
                    type="email" 
                    placeholder="Email Address" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <div className="space-y-2">
                  <Input 
                    name="password"
                    type="password" 
                    placeholder="Create Password" 
                    required 
                    className="h-12 border-green-200 focus:border-green-500 focus:ring-green-500"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full h-12 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-medium shadow-lg hover:shadow-xl transition-all duration-300" 
                  disabled={loading}
                >
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