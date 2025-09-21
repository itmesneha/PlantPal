import { useState } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Camera, Upload, Loader2 } from 'lucide-react';

interface PlantScanResult {
  species: string;
  confidence: number;
  isHealthy: boolean;
  disease?: string;
  healthScore: number;
  careRecommendations: string[];
}

interface PlantScannerProps {
  onScanComplete: (result: PlantScanResult) => void;
}

export function PlantScanner({ onScanComplete }: PlantScannerProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleScan = async () => {
    if (!selectedImage) return;
    
    setScanning(true);
    
    // Mock AI analysis - in real app this would call Hugging Face API
    setTimeout(() => {
      const mockResults: PlantScanResult[] = [
        {
          species: 'Rose (Rosa rubiginosa)',
          confidence: 0.94,
          isHealthy: false,
          disease: 'Black Spot Disease',
          healthScore: 65,
          careRecommendations: [
            'Remove affected leaves immediately',
            'Apply fungicide spray weekly',
            'Improve air circulation around plant',
            'Water at soil level, avoid wetting leaves'
          ]
        },
        {
          species: 'Monstera Deliciosa',
          confidence: 0.91,
          isHealthy: true,
          healthScore: 92,
          careRecommendations: [
            'Water when top 2 inches of soil are dry',
            'Provide bright, indirect light',
            'Fertilize monthly during growing season',
            'Mist leaves regularly for humidity'
          ]
        },
        {
          species: 'Snake Plant (Sansevieria)',
          confidence: 0.88,
          isHealthy: true,
          healthScore: 85,
          careRecommendations: [
            'Water sparingly - every 2-3 weeks',
            'Tolerates low light conditions',
            'Fertilize 2-3 times per year',
            'Dust leaves monthly for optimal photosynthesis'
          ]
        }
      ];
      
      const randomResult = mockResults[Math.floor(Math.random() * mockResults.length)];
      onScanComplete(randomResult);
      setScanning(false);
    }, 2000);
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Camera className="w-5 h-5" />
          Plant Scanner
        </CardTitle>
        <CardDescription>
          Upload a photo to identify your plant and check its health
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          {selectedImage ? (
            <div className="space-y-4">
              {/* <ImageWithFallback
                src={selectedImage}
                alt="Selected plant"
                className="max-w-full max-h-64 mx-auto rounded-lg"
              /> */}
              <Button onClick={handleScan} disabled={scanning} className="w-full">
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
            <div className="space-y-4">
              <Upload className="w-12 h-12 mx-auto text-gray-400" />
              <div>
                <label htmlFor="plant-image" className="cursor-pointer">
                  <Button asChild>
                    <span>
                      <Camera className="w-4 h-4 mr-2" />
                      Upload Plant Photo
                    </span>
                  </Button>
                </label>
                <input
                  id="plant-image"
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </div>
              <p className="text-gray-500">
                Take a clear photo of your plant's leaves and stems
              </p>
            </div>
          )}
        </div>
        
        {selectedImage && !scanning && (
          <Button 
            variant="outline" 
            onClick={() => setSelectedImage(null)}
            className="w-full"
          >
            Choose Different Photo
          </Button>
        )}
      </CardContent>
    </Card>
  );
}