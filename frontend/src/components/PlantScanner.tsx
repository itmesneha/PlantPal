import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Camera, Upload, Loader2, AlertCircle } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';
import { plantScanService, ScanResult } from '../services/plantScanService';

interface PlantScanResult {
  species: string;
  confidence: number;
  isHealthy: boolean;
  disease?: string;
  healthScore: number;
  careRecommendations: string[];
}

interface PlantScannerProps {
  onScanComplete: (result: PlantScanResult, originalFile: File) => void;
  plantId?: string; // Optional plant ID for rescanning existing plants
}

export function PlantScanner({ onScanComplete, plantId }: PlantScannerProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset error
    setError(null);

    // Validate file
    const validation = plantScanService.validateImageFile(file);
    if (!validation.isValid) {
      setError(validation.error || 'Invalid file');
      return;
    }

    // Store file for API call
    setSelectedFile(file);

    // Create preview
    const reader = new FileReader(); 
    reader.onload = (e) => {
      setSelectedImage(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleScan = async () => {
    if (!selectedFile) return;
    
    setScanning(true);
    setError(null);
    
    try {
      console.log('🚀 Starting plant scan...');
      
      // Call the real API with optional plant ID for rescanning
      const result: ScanResult = await plantScanService.scanPlantImage(selectedFile, plantId);
      
      // Transform API response to match component interface
      const transformedResult: PlantScanResult = {
        species: result.species,
        confidence: result.confidence,
        isHealthy: result.is_healthy,
        disease: result.disease || undefined,
        healthScore: result.health_score,
        careRecommendations: result.care_recommendations
      };
      
      console.log('✅ Plant scan completed:', transformedResult);
      onScanComplete(transformedResult, selectedFile);
      
    } catch (error) {
      console.error('❌ Plant scan failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to scan plant. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
          <Camera className="w-4 h-4 sm:w-5 sm:h-5" />
          {plantId ? 'Rescan Plant' : 'Plant Scanner'}
        </CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          {plantId 
            ? 'Upload a new photo to update your plant\'s health data' 
            : 'Upload a photo to identify your plant and check its health'
          }
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 sm:space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs sm:text-sm">{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 sm:p-6 md:p-8 text-center">
          {selectedImage ? (
            <div className="space-y-3 sm:space-y-4">
              <img
                src={selectedImage}
                alt="Selected plant"
                className="max-w-full max-h-48 sm:max-h-64 mx-auto rounded-lg object-contain"
              />
              <div className="text-xs sm:text-sm text-gray-500">
                {selectedFile && `File: ${selectedFile.name} (${plantScanService.formatFileSize(selectedFile.size)})`}
              </div>
              <Button onClick={handleScan} disabled={scanning || !selectedFile} className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold py-2 sm:py-3 px-4 sm:px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl text-sm sm:text-base"
            >
                {scanning ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing Plant...
                  </>
                ) : (
                  'Scan Plant'
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-3 sm:space-y-4">
              <Upload className="w-10 h-10 sm:w-12 sm:h-12 mx-auto text-gray-400" />
              <div>
                <label htmlFor="plant-image" className="cursor-pointer">
                  <Button asChild className="text-sm sm:text-base">
                    <span>
                      <Camera className="w-4 h-4 mr-2" />
                      Upload Plant Photo
                    </span>
                  </Button>
                </label>
                <input
                  id="plant-image"
                  type="file"
                  accept={plantScanService.getSupportedImageTypes()}
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>
              <p className="text-gray-500 text-xs sm:text-sm px-2">
                Take a clear photo of your plant's leaves and stems<br />
                <span className="text-xs">Supported formats: JPEG, PNG, GIF, WebP (Max 10MB)</span>
              </p>
            </div>
          )}
        </div>
        
        {selectedImage && !scanning && (
          <Button 
            variant="outline" 
            onClick={() => {
              setSelectedImage(null);
              setSelectedFile(null);
              setError(null);
            }}
            className="w-full text-sm sm:text-base"
          >
            Choose Different Photo
          </Button>
        )}
      </CardContent>
    </Card>
  );
}