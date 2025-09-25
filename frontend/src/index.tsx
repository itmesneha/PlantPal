// src/index.tsx
'use client';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { Amplify } from 'aws-amplify';

// Validate required environment variables (simplified for direct auth)
const requiredEnvVars = [
  'REACT_APP_USER_POOL_ID',
  'REACT_APP_USER_POOL_CLIENT_ID'
];

const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);
if (missingEnvVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
}

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: process.env.REACT_APP_USER_POOL_ID!,
      userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID!,
      loginWith: {
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
