import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon?: string;
  achievement_type: string;
  requirement_value: number;
  points_awarded: number;
  is_active: boolean;
  created_at: string;
}

export interface UserAchievement {
  id: string;
  user_id: string;
  achievement_id: string;
  current_progress: number;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  updated_at?: string;
  achievement: Achievement;
}

export interface AchievementStats {
  total_achievements: number;
  completed: number;
  in_progress: number;
  total_points_earned: number;
  completion_percentage: number;
}

export interface UserStreak {
    current_streak: number;
}

class AchievementService {
  private async getAuthToken(): Promise<string> {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      if (!token) throw new Error('No auth token');
      return token;
    } catch (error) {
      console.error('❌ Failed to get auth token:', error);
      throw error;
    }
  }

  async getAllAchievements(): Promise<Achievement[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching all achievements:', error);
      return [];
    }
  }

  async getUserAchievements(): Promise<UserAchievement[]> {
    try {        
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/user`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching user achievements:', error);
      return [];
    }
  }

  async getCompletedAchievements(): Promise<UserAchievement[]> {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/user/completed`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching completed achievements:', error);
      return [];
    }
  }

  async getAchievementStats(): Promise<AchievementStats | null> {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/user/stats`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching achievement stats:', error);
      return null;
    }
  }

  async getCurrentStreak(): Promise<UserStreak | null> {
    try{
        const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/user/streak`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    }catch (error) {
        console.error('❌ Error checking streaks:', error);
        return null;
    }
  }

  async checkStreaks(): Promise<any> {
    try {
      const token = await this.getAuthToken();
      const response = await fetch(`${API_BASE_URL}/api/v1/achievements/user/check-streaks`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('❌ Error checking streaks:', error);
      return null;
    }
  }
}

export const achievementService = new AchievementService();