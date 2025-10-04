import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface PlantScan {
  id: string;
  plant_id: string | null;  // Made nullable to match backend
  user_id: string;
  scan_date: string;
  health_score: number;
  care_notes: string | null;
  disease_detected: string | null;
  is_healthy: boolean;
  created_at: string;
}

export const scanService = {
  async getPlantScanHistory(plantId: string): Promise<PlantScan[]> {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      
      if (!token) {
        throw new Error('No authentication token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/history/${plantId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch scan history: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching scan history:', error);
      throw error;
    }
  },

  async getLatestPlantHealthInfo(plantId: string): Promise<{
    lastDisease: string | null;
    lastCareNotes: string[] | null;
    lastScanDate: string | null;
    isHealthy: boolean;
  }> {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      
      if (!token) {
        throw new Error('No authentication token available');
      }

      // Use our new simplified endpoint
      const response = await fetch(`${API_BASE_URL}/api/v1/latest-health/${plantId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch latest health info: ${response.statusText}`);
      }

      const healthData = await response.json();
      
      // Parse care notes - split by semicolon as requested
      let careNotes: string[] | null = null;
      if (healthData.care_notes) {
        careNotes = healthData.care_notes
          .split(';')
          .map((note: string) => note.trim())
          .filter((note: string) => note.length > 0);
      }

      return {
        lastDisease: healthData.disease_detected,
        lastCareNotes: careNotes,
        lastScanDate: healthData.scan_date,
        isHealthy: healthData.is_healthy
      };
    } catch (error) {
      console.error('Error fetching latest plant health info:', error);
      // Return safe defaults if API fails
      return {
        lastDisease: null,
        lastCareNotes: null,
        lastScanDate: null,
        isHealthy: true
      };
    }
  }
};