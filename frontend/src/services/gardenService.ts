// Garden service for managing user's plant collection
import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface AddToGardenRequest {
  plant_name: string;
  species: string;
  common_name?: string;
  location?: string;
  care_notes?: string;
  health_score?: number;
  image_data?: string; // Base64 encoded image
  plant_icon?: string; // User-selected emoji icon
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