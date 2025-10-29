// User service for managing user data sync between Cognito and backend
import { getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface User {
  id: string;
  cognito_user_id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at?: string;
}

export interface UserCreate {
  cognito_user_id: string;
  email: string;
  name: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  email: string;
  score: number;
  total_plants: number;
  achievements_completed: number;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  current_user_rank: number | null;
}

class UserService {
  private getAuthToken = async (): Promise<string> => {
    try {
      const session = await fetchAuthSession();
      console.log('🔍 Session:', session);
      
      // Use ID token instead of access token to get user profile info
      const idToken = session.tokens?.idToken;
      console.log('🔍 ID token exists:', !!idToken);
      
      if (!idToken) {
        throw new Error('No ID token available');
      }
      
      const tokenString = idToken.toString();
      console.log('🔍 Token string (first 50 chars):', tokenString.substring(0, 50));
      
      return tokenString;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      throw new Error('Authentication required');
    }
  };

  private makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
    const token = await this.getAuthToken();
    
    return fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  };

  /**
   * Get current user from backend (creates if doesn't exist)
   */
  getCurrentUser = async (): Promise<User> => {
    try {
      const response = await this.makeAuthenticatedRequest(`${API_BASE_URL}/api/v1/users/me`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`Failed to get user: ${response.statusText}`);
      }

      const user = await response.json();
      console.log('✅ Got user from backend:', user);
      return user;
    } catch (error) {
      console.error('Failed to get current user:', error);
      throw error;
    }
  };

  /**
   * Create user in backend after Cognito signup
   */
  createUser = async (userData: UserCreate): Promise<User> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        throw new Error(`Failed to create user: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to create user:', error);
      throw error;
    }
  };

  /**
   * Sync user data after Cognito authentication
   * This ensures the user exists in our backend database
   */
  syncUserAfterAuth = async (): Promise<User> => {
    try {
      // For development: just get/create the test user
      const user = await this.getCurrentUser();
      console.log('✅ User synced:', user.name);
      return user;
    } catch (error) {
      console.error('User sync failed:', error);
      throw error;
    }
  };

  /**
   * Get leaderboard data
   */
  getLeaderboard = async (limit: number = 10): Promise<LeaderboardResponse> => {
    try {
      const response = await this.makeAuthenticatedRequest(
        `${API_BASE_URL}/api/v1/leaderboard?limit=${limit}`,
        {
          method: 'GET',
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get leaderboard: ${response.statusText}`);
      }

      const leaderboardData = await response.json();
      console.log('✅ Leaderboard fetched:', leaderboardData);
      return leaderboardData;
    } catch (error) {
      console.error('Failed to get leaderboard:', error);
      throw error;
    }
  };
}

export const userService = new UserService();