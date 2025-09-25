// src/index.tsx
'use client';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { Amplify } from 'aws-amplify';

// Validate required environment variables
const requiredEnvVars = [
  'COGNITO_USER_POOL_ID',
  'COGNITO_CLIENT_ID', 
  'REACT_APP_COGNITO_DOMAIN',
  'REACT_APP_REDIRECT_SIGN_IN',
  'REACT_APP_REDIRECT_SIGN_OUT'
];

const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);
if (missingEnvVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
}

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: process.env.COGNITO_USER_POOL_ID!,
      userPoolClientId: process.env.COGNITO_CLIENT_ID!,
      loginWith: {
        oauth: {
          domain: process.env.REACT_APP_COGNITO_DOMAIN!,
          scopes: ["openid", "email", "profile"],
          redirectSignIn: [process.env.REACT_APP_REDIRECT_SIGN_IN!],
          redirectSignOut: [process.env.REACT_APP_REDIRECT_SIGN_OUT!],
          responseType: "code" as const,
        },
        email: true,
        username: false,
      },
    },
  },
};


Amplify.configure(amplifyConfig);



const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
