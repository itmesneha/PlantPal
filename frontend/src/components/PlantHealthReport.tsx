import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { CheckCircle, AlertTriangle, Droplets, Sun, Scissors } from 'lucide-react';

interface PlantScanResult {
  species: string;
  confidence: number;
  isHealthy: boolean;
  disease?: string;
  healthScore: number;
  careRecommendations: string[];
}

interface PlantHealthReportProps {
  result: PlantScanResult;
  streak: number;
  onAddToGarden: () => void;
}

export function PlantHealthReport({ result, streak, onAddToGarden }: PlantHealthReportProps) {
  const getHealthBadgeVariant = (score: number) => {
    if (score >= 80) return 'default';
    if (score >= 60) return 'secondary';
    return 'destructive';
  };

  const getCareIcon = (recommendation: string) => {
    if (recommendation.toLowerCase().includes('water')) return <Droplets className="w-4 h-4" />;
    if (recommendation.toLowerCase().includes('light') || recommendation.toLowerCase().includes('sun')) return <Sun className="w-4 h-4" />;
    if (recommendation.toLowerCase().includes('remove') || recommendation.toLowerCase().includes('trim')) return <Scissors className="w-4 h-4" />;
    return <CheckCircle className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6 w-full max-w-2xl mx-auto">
      {/* Main Results Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Plant Identification Results</span>
            <div className="flex items-center gap-2">
              {result.isHealthy ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              )}
            </div>
          </CardTitle>
          <CardDescription>
            Confidence: {Math.round(result.confidence * 100)}%
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="mb-2">Species</h3>
            <p className="text-lg">{result.species}</p>
          </div>
          
          <div>
            <h3 className="mb-2">Health Score</h3>
            <div className="flex items-center gap-3">
              <Progress value={result.healthScore} className="flex-1" />
              <Badge variant={getHealthBadgeVariant(result.healthScore)}>
                {result.healthScore}/100
              </Badge>
            </div>
          </div>

          {!result.isHealthy && result.disease && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>Disease Detected:</strong> {result.disease}
              </AlertDescription>
            </Alert>
          )}

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Health streak: {streak} days
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Care Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Care Recommendations</CardTitle>
          <CardDescription>
            {result.isHealthy 
              ? 'Keep up the great work! Here are tips to maintain your plant\'s health:'
              : 'Follow these steps to help your plant recover:'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {result.careRecommendations.map((recommendation, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                <div className="mt-0.5 text-muted-foreground">
                  {getCareIcon(recommendation)}
                </div>
                <p className="flex-1">{recommendation}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}