import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface Plant {
  id: string;
  user_id: string;
  name: string;
  species: string;
  common_name?: string;
  location?: string;
  care_notes?: string;
  current_health_score: number;
  streak_days: number;
  last_check_in: string;
  image_url?: string;
  plant_icon?: string;
  created_at: string;
  updated_at?: string;
}

export interface GetUserPlantsParams {
  skip?: number;
  limit?: number;
}

class PlantsService {
  private async getAuthToken(): Promise<string> {
    try {
      const session = await fetchAuthSession();
      const token = session.tokens?.idToken?.toString();
      if (!token) {
        throw new Error('No auth token available');
      }
      return token;
    } catch (error) {
      console.error('Failed to get auth token:', error);
      throw new Error('Authentication required');
    }
  }

  private async makeAuthenticatedRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const token = await this.getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  }

  /**
   * Get all plants for the current user
   */
  async getUserPlants(params: GetUserPlantsParams = {}): Promise<Plant[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
      if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
      
      const endpoint = `/api/v1/plants${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      
      console.log('🌱 Fetching user plants from:', endpoint);
      
      const response = await this.makeAuthenticatedRequest(endpoint);
      const plants = await response.json();
      
      console.log('✅ User plants fetched successfully:', plants);
      return plants;
      
    } catch (error) {
      console.error('❌ Failed to fetch user plants:', error);
      throw error;
    }
  }

  /**
   * Transform backend plant data to match Dashboard interface
   */
  transformPlantForDashboard(plant: Plant): {
    id: string;
    name: string;
    species: string;
    healthScore: number;
    streak: number;
    lastCheckIn: string;
    image?: string;
    icon?: string;
  } {
    return {
      id: plant.id,
      name: plant.name,
      species: plant.species,
      healthScore: plant.current_health_score,
      streak: plant.streak_days,
      lastCheckIn: new Date(plant.last_check_in).toLocaleDateString(),
      image: plant.image_url || undefined,
      icon: plant.plant_icon || '🌱',
    };
  }

  /**
   * Get user plants formatted for Dashboard component
   */
  async getUserPlantsForDashboard(params: GetUserPlantsParams = {}): Promise<{
    id: string;
    name: string;
    species: string;
    healthScore: number;
    streak: number;
    lastCheckIn: string;
    image?: string;
    icon?: string;
  }[]> {
    const plants = await this.getUserPlants(params);
    return plants.map(plant => this.transformPlantForDashboard(plant));
  }
}

export const plantsService = new PlantsService();