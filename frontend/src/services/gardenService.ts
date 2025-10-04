// Garden service for managing user's plant collection
import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface AddToGardenRequest {
  plant_name: string;
  species: string;
  health_score?: number;
  plant_icon?: string;
  
  // Scan data (from scan results)
  disease_detected?: string;
  is_healthy?: boolean;
  care_notes?: string;
  
  // Legacy fields (keep for compatibility)
  image_data?: string; // Base64 encoded image
}

export interface AddToGardenResponse {
  success: boolean;
  plant_id: string;
  message: string;
  plant: {
    id: string;
    name: string;
    species: string;
    common_name?: string;
    current_health_score: number;
    streak_days: number;
    created_at: string;
  };
}

export interface DeletePlantResponse {
  success: boolean;
  message: string;
  deleted_plant_id: string;
}

export interface UpdatePlantRequest {
  name?: string;
  current_health_score?: number;
}

export interface UpdatePlantResponse {
  success: boolean;
  message: string;
  plant: Plant;
}

export interface Plant {
  id: string;
  name: string;
  species: string;
  common_name?: string;
  care_notes?: string;
  current_health_score: number;
  streak_days: number;
  last_check_in?: string;
  plant_icon?: string;
  created_at: string;
  updated_at?: string;
}

export interface GardenError {
  message: string;
  details?: string;
}

class GardenService {
  private getAuthToken = async (): Promise<string> => {
    try {
      const session = await fetchAuthSession();
      console.log('🌱 Garden Service Session:', session);
      
      const idToken = session.tokens?.idToken;
      console.log('🌱 ID token exists for garden service:', !!idToken);
      
      if (!idToken) {
        throw new Error('No ID token available');
      }
      
      const tokenString = idToken.toString();
      console.log('🌱 Garden service token (first 50 chars):', tokenString.substring(0, 50));
      
      return tokenString;
    } catch (error) {
      console.error('Failed to get auth token for garden service:', error);
      throw new Error('Authentication required for garden operations');
    }
  };

  /**
   * Add a plant to user's garden
   * @param request - Plant details to add
   * @returns Promise<AddToGardenResponse> - Response with plant details
   */
  addToGarden = async (request: AddToGardenRequest): Promise<AddToGardenResponse> => {
    try {
      console.log('🌱 Adding plant to garden:', {
        name: request.plant_name,
        species: request.species,
        health_score: request.health_score
      });

      // Get authentication token
      const token = await this.getAuthToken();

      // Make API request
      const response = await fetch(`${API_BASE_URL}/api/v1/plants/add-to-garden`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `Failed to add plant with status ${response.status}: ${response.statusText}`
        );
      }

      const result: AddToGardenResponse = await response.json();
      console.log('✅ Plant added to garden successfully:', result);

      return result;

    } catch (error) {
      console.error('❌ Failed to add plant to garden:', error);
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('Unknown error occurred while adding plant to garden');
    }
  };

  /**
   * Delete a plant from user's garden
   * @param plantId - ID of the plant to delete
   * @returns Promise<DeletePlantResponse> - Response confirming deletion
   */
  deletePlant = async (plantId: string): Promise<DeletePlantResponse> => {
    try {
      console.log('🗑️ Deleting plant from garden:', plantId);
      console.log('🔗 API URL:', `${API_BASE_URL}/api/v1/plants/${plantId}`);

      // Get authentication token
      const token = await this.getAuthToken();
      console.log('🔑 Auth token obtained for delete request');

      // Make API request
      const response = await fetch(`${API_BASE_URL}/api/v1/plants/${plantId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Delete response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        console.error('❌ Delete API error response:', errorData);
        throw new Error(
          errorData?.detail || 
          `Failed to delete plant with status ${response.status}: ${response.statusText}`
        );
      }

      const result: DeletePlantResponse = await response.json();
      console.log('✅ Plant deleted from garden successfully:', result);

      return result;

    } catch (error) {
      console.error('❌ Failed to delete plant from garden:', error);
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('Unknown error occurred while deleting plant from garden');
    }
  };

  /**
   * Update a plant in user's garden
   * @param plantId - ID of the plant to update
   * @param request - Plant update details
   * @returns Promise<Plant> - Updated plant details
   */
  updatePlant = async (plantId: string, request: UpdatePlantRequest): Promise<Plant> => {
    try {
      console.log('🔄 Updating plant:', plantId, request);

      const token = await this.getAuthToken();

      const response = await fetch(`${API_BASE_URL}/api/v1/plants/${plantId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `Failed to update plant with status ${response.status}: ${response.statusText}`
        );
      }

      const updatedPlant: Plant = await response.json();
      console.log('✅ Plant updated successfully:', updatedPlant);

      return updatedPlant;

    } catch (error) {
      console.error('❌ Failed to update plant:', error);
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('Unknown error occurred while updating plant');
    }
  };

  /**
   * Get all plants in user's garden
   * @returns Promise<Plant[]> - Array of user's plants
   */
  getUserPlants = async (): Promise<Plant[]> => {
    try {
      console.log('🌱 Fetching user plants from garden');

      // Get authentication token
      const token = await this.getAuthToken();

      // Make API request
      const response = await fetch(`${API_BASE_URL}/api/v1/plants/`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `Failed to fetch plants with status ${response.status}: ${response.statusText}`
        );
      }

      const plants: Plant[] = await response.json();
      console.log('✅ User plants fetched successfully:', plants.length, 'plants found');

      return plants;

    } catch (error) {
      console.error('❌ Failed to fetch user plants:', error);
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('Unknown error occurred while fetching user plants');
    }
  };

  /**
   * Convert image file to base64 string
   * @param file - Image file
   * @returns Promise<string> - Base64 encoded image
   */
  convertImageToBase64 = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (reader.result && typeof reader.result === 'string') {
          // Remove data:image/jpeg;base64, prefix
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to convert image to base64'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read image file'));
      reader.readAsDataURL(file);
    });
  };
}

// Export singleton instance
export const gardenService = new GardenService();
export default gardenService;