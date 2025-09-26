// Plant scan service for disease detection using Hugging Face AI
import { fetchAuthSession } from 'aws-amplify/auth';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ScanResult {
  species: string;
  confidence: number;
  is_healthy: boolean;
  disease: string | null;
  health_score: number;
  care_recommendations: string[];
}

export interface ScanError {
  message: string;
  details?: string;
}

class PlantScanService {
  private getAuthToken = async (): Promise<string> => {
    try {
      const session = await fetchAuthSession();
      console.log('🔍 Plant Scan Session:', session);
      
      const idToken = session.tokens?.idToken;
      console.log('🔍 ID token exists for scan:', !!idToken);
      
      if (!idToken) {
        throw new Error('No ID token available');
      }
      
      const tokenString = idToken.toString();
      console.log('🔍 Plant scan token (first 50 chars):', tokenString.substring(0, 50));
      
      return tokenString;
    } catch (error) {
      console.error('Failed to get auth token for plant scan:', error);
      throw new Error('Authentication required for plant scanning');
    }
  };

  /**
   * Scan a plant image for disease detection
   * @param imageFile - The image file to analyze
   * @returns Promise<ScanResult> - Analysis results
   */
  scanPlantImage = async (imageFile: File): Promise<ScanResult> => {
    try {
      // Validate file type
      if (!imageFile.type.startsWith('image/')) {
        throw new Error('Please upload a valid image file');
      }

      // Validate file size (10MB limit)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (imageFile.size > maxSize) {
        throw new Error('Image file is too large. Please use an image smaller than 10MB');
      }

      console.log('📸 Scanning plant image:', {
        name: imageFile.name,
        size: `${(imageFile.size / 1024 / 1024).toFixed(2)}MB`,
        type: imageFile.type
      });

      // Get authentication token
      const token = await this.getAuthToken();

      // Create FormData for file upload
      const formData = new FormData();
      formData.append('image', imageFile);

      // Make API request
      const response = await fetch(`${API_BASE_URL}/api/v1/scan`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          // Don't set Content-Type header - let the browser set it for FormData
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `Scan failed with status ${response.status}: ${response.statusText}`
        );
      }

      const result: ScanResult = await response.json();
      console.log('✅ Plant scan successful:', result);

      return result;

    } catch (error) {
      console.error('❌ Plant scan failed:', error);
      
      if (error instanceof Error) {
        throw error;
      }
      
      throw new Error('Failed to scan plant image. Please try again.');
    }
  };

  /**
   * Validate image file before scanning
   * @param file - File to validate
   * @returns validation result and error message if invalid
   */
  validateImageFile = (file: File): { isValid: boolean; error?: string } => {
    // Check if file exists
    if (!file) {
      return { isValid: false, error: 'No file selected' };
    }

    // Check file type
    if (!file.type.startsWith('image/')) {
      return { isValid: false, error: 'Please select an image file (JPEG, PNG, etc.)' };
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      return { isValid: false, error: 'Image file is too large (max 10MB)' };
    }

    // Check minimum size (to avoid tiny images)
    const minSize = 1024; // 1KB
    if (file.size < minSize) {
      return { isValid: false, error: 'Image file is too small' };
    }

    return { isValid: true };
  };

  /**
   * Get supported image types for file input
   */
  getSupportedImageTypes = (): string => {
    return 'image/jpeg,image/jpg,image/png,image/gif,image/webp';
  };

  /**
   * Format file size for display
   */
  formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
}

export const plantScanService = new PlantScanService();