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

  const getHealthScoreColor = (score: number) => {
    if (score >= 70) return 'bg-green-600 text-white hover:bg-green-700';
    if (score >= 50) return 'bg-yellow-600 text-white hover:bg-yellow-700';
    return 'bg-red-600 text-white hover:bg-red-700';
  };

  const getCareIcon = (recommendation: string) => {
    if (recommendation.toLowerCase().includes('water')) return <Droplets className="w-4 h-4" />;
    if (recommendation.toLowerCase().includes('light') || recommendation.toLowerCase().includes('sun')) return <Sun className="w-4 h-4" />;
    if (recommendation.toLowerCase().includes('remove') || recommendation.toLowerCase().includes('trim')) return <Scissors className="w-4 h-4" />;
    return <CheckCircle className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6 w-full max-w-4xl mx-auto">
      {/* Main Results Card */}
      <Card className="overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 border-b">
          <CardTitle className="flex items-center justify-between text-2xl">
            <span className="font-light flex items-center gap-3">
              🌿 Analysis Results
            </span>
            <div className="flex items-center gap-2">
              {result.isHealthy ? (
                <div className="flex items-center gap-2 bg-green-100 px-3 py-1 rounded-full">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-green-700">Healthy</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 bg-yellow-100 px-3 py-1 rounded-full">
                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-700">Needs Care</span>
                </div>
              )}
            </div>
          </CardTitle>
          {!result.isHealthy && result.confidence > 0.5 && (
            <CardDescription className="text-base">
              AI Confidence: <span className="font-semibold">{(result.confidence * 100).toFixed(1)}%</span>
            </CardDescription>
          )}
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Species Information */}
            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-lg border">
                <h3 className="text-sm font-medium text-slate-600 mb-2">IDENTIFIED SPECIES</h3>
                <p className="text-xl font-semibold text-slate-900">{result.species}</p>
              </div>
              
              <div className="bg-slate-50 p-4 rounded-lg border">
                <h3 className="text-sm font-medium text-slate-600 mb-2">CARE STREAK</h3>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-orange-600">{streak}</span>
                  <span className="text-slate-600">consecutive days</span>
                  <span className="text-orange-500">🔥</span>
                </div>
              </div>
            </div>

            {/* Health Score Section */}
            <div className="space-y-4">
              <div className="bg-white p-6 rounded-xl border-2 border-slate-200 shadow-sm">
                <div className="text-center mb-4">
                  <h3 className="text-lg font-semibold text-slate-800 mb-2">Plant Health Score</h3>
                  <div className={`inline-block rounded-full px-6 py-3 text-3xl font-bold ${getHealthScoreColor(result.healthScore)} shadow-lg`}>
                    {Math.round(result.healthScore)}/100
                  </div>
                </div>
                
                <div className="mb-4">
                  <Progress value={result.healthScore} className="h-4 bg-slate-200" />
                </div>
                
                {/* Status Messages */}
                <div className="text-center">
                  {result.healthScore >= 90 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <div className="text-green-700 font-semibold flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Excellent! Your plant is thriving! 🌟
                      </div>
                    </div>
                  )}
                  {result.healthScore >= 80 && result.healthScore < 90 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <div className="text-green-600 font-semibold flex items-center justify-center gap-2">
                        <CheckCircle className="w-5 h-5" />
                        Great job! Very healthy plant! 🌱
                      </div>
                    </div>
                  )}
                  {result.healthScore >= 70 && result.healthScore < 80 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="text-blue-600 font-semibold">
                        Good health - keep up the routine! 👍
                      </div>
                    </div>
                  )}
                  {result.healthScore < 70 && result.healthScore >= 50 && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="text-yellow-700 font-semibold">
                        ⚠️ Needs attention - check recommendations
                      </div>
                    </div>
                  )}
                  {result.healthScore < 50 && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <div className="text-red-700 font-semibold">
                        🚨 Requires immediate care!
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Disease Alert */}
          {!result.isHealthy && result.disease && (
            <div className="mt-6">
              <Alert className="border-orange-200 bg-orange-50">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <AlertDescription className="text-orange-800">
                  <div className="font-semibold">Disease Detected: {result.disease} </div>
                </AlertDescription>
              </Alert>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Care Recommendations */}
      <Card className="overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-emerald-50 to-teal-50 border-b">
          <CardTitle className="flex items-center gap-2 text-xl">
            <span>🩺</span>
            Care Recommendations
          </CardTitle>
          <CardDescription className="text-base">
            {result.isHealthy 
              ? 'Keep up the excellent work! Here are tips to maintain your plant\'s health:'
              : 'Here are some recommendations to help your plant recover:'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          {/* Treatment Information (for diseased plants) */}
          {/* {!result.isHealthy && result.careRecommendations.length > 0 && 
           result.careRecommendations[0].toLowerCase().includes('treatment') && (
            <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-orange-800 mb-1">Recommended Treatment</h4>
                   <p className="text-orange-700 font-medium">{result.careRecommendations[0]}</p> 
                </div>
              </div>
            </div>
          )} */}

          {/* Care Steps */}
          <div className="grid gap-4">
            {result.careRecommendations
              .slice(result.isHealthy ? 0 : 1) // Skip first item for diseased plants (treatment info)
              .map((recommendation, index) => (
              <div key={index} className="group">
                <div className="flex items-start gap-4 p-4 bg-white border border-slate-200 rounded-xl hover:border-slate-300 hover:shadow-sm transition-all duration-200">
                  <div className="flex-shrink-0 mt-1">
                    <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 group-hover:bg-emerald-200 transition-colors">
                      {getCareIcon(recommendation)}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-slate-700 leading-relaxed font-medium">
                        {recommendation}
                      </p>
                      {/* <span className="flex-shrink-0 bg-slate-100 text-slate-600 text-xs px-2 py-1 rounded-full font-medium">
                        Step {index + 1}
                      </span> */}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Action Button */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            <button 
              onClick={onAddToGarden}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              🌱 Add to My Garden
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}