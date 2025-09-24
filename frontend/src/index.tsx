import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { Amplify } from 'aws-amplify';

const amplifyConfig = {
  Auth: {
    Cognito: {
      region: "ap-southeast-1",
      userPoolId: process.env.REACT_APP_USER_POOL_ID || "ap-southeast-1_km8Z7zM54",
      userPoolClientId: process.env.REACT_APP_USER_POOL_CLIENT_ID || "1ugluq9v60811tf40482j6t6in",
      // Optional: identity pool
      // identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID,
      // Optional: login mechanisms
      loginWith: {
        email: true,
        // phone: true,
        // username: true
      }
    }
  }
};

Amplify.configure(amplifyConfig);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
