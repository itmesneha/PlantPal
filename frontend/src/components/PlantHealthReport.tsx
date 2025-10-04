import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { CheckCircle, AlertTriangle, Droplets, Sun, Scissors, Loader2, Bot } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { gardenService, AddToGardenRequest } from '../services/gardenService';
import { plantScanService, CareRecommendationsResponse } from '../services/plantScanService';
import { AddPlantDialog } from './AddPlantDialog';
import analysisIcon from '../assets/analysis_results.png';
import prescriptionIcon from '../assets/prescription.png';
import plant1Icon from '../assets/plant-icons/plant1.png';

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
  onAddToGarden?: (plantId: string, plantName: string) => void; // Optional callback with plant details
  originalImage?: File; // Original image file for adding to garden
}

export function PlantHealthReport({ result, streak, onAddToGarden, originalImage }: PlantHealthReportProps) {
  const [isAddingToGarden, setIsAddingToGarden] = useState(false);
  const [addToGardenStatus, setAddToGardenStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [showAddPlantDialog, setShowAddPlantDialog] = useState(false);
  const [aiCareRecommendations, setAiCareRecommendations] = useState<CareRecommendationsResponse | null>(null);
  const [isLoadingAiRecommendations, setIsLoadingAiRecommendations] = useState(false);
  const [aiRecommendationsError, setAiRecommendationsError] = useState<string>('');

  // Refs to prevent duplicate API calls
  const lastRequestRef = useRef<string>('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Automatically fetch AI care recommendations when disease is detected
  useEffect(() => {
    const fetchAiCareRecommendations = async () => {
      // Only fetch AI recommendations if plant is not healthy and has disease/confidence > 0.5
      if (!result.isHealthy && (result.disease || result.confidence > 0.5)) {

        // Create a unique request identifier
        const requestKey = `${result.species}-${result.disease || 'unknown'}-${result.confidence}`;

        // Prevent duplicate requests
        if (lastRequestRef.current === requestKey || isLoadingAiRecommendations) {
          console.log('🚫 Skipping duplicate AI recommendation request:', requestKey);
          return;
        }

        // Cancel any existing request
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }

        // Create new abort controller
        abortControllerRef.current = new AbortController();
        lastRequestRef.current = requestKey;

        setIsLoadingAiRecommendations(true);
        setAiRecommendationsError('');
        setAiCareRecommendations(null); // Clear previous recommendations

        try {
          console.log('🚀 Fetching AI care recommendations for:', {
            species: result.species,
            disease: result.disease,
            confidence: result.confidence,
            requestKey
          });

          const aiResponse = await plantScanService.getCareRecommendations({
            species: result.species,
            disease: result.disease || undefined
          });

          // Only update if request wasn't aborted
          if (!abortControllerRef.current?.signal.aborted) {
            setAiCareRecommendations(aiResponse);
            console.log('🤖 AI care recommendations received:', aiResponse);
            console.log('📋 Recommendations count:', aiResponse.care_recommendations?.length);
          }

        } catch (error) {
          // Only handle error if request wasn't aborted
          if (!abortControllerRef.current?.signal.aborted) {
            console.error('❌ Failed to get AI care recommendations:', error);
            setAiRecommendationsError(error instanceof Error ? error.message : 'Failed to get AI recommendations');
            lastRequestRef.current = ''; // Reset on error to allow retry
          }
        } finally {
          // Only update loading state if request wasn't aborted
          if (!abortControllerRef.current?.signal.aborted) {
            setIsLoadingAiRecommendations(false);
          }
        }
      } else {
        console.log('🔍 Skipping AI recommendations - plant is healthy or low confidence');
        // Clear previous recommendations for healthy plants
        setAiCareRecommendations(null);
        setAiRecommendationsError('');
        lastRequestRef.current = '';
      }
    };

    fetchAiCareRecommendations();

    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [result.species, result.disease, result.isHealthy]); // Removed confidence from deps to prevent too many calls

  const handleOpenAddDialog = () => {
    setShowAddPlantDialog(true);
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
            <span className="font-light flex items-end gap-3">
              <img
                src={analysisIcon}
                width={32}
                height={32}
                alt="icon"
                className="inline-block"
              />
              <h3 className="text-2xl text-gray-800">Analysis Results</h3>
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
            <span><img
              src={prescriptionIcon}
              width={32}
              height={32}
              alt="icon"
              className="inline-block"
            />
            </span>
            <h4 className="text-2xl text-gray-800">Care Recommendations</h4>
          </CardTitle>
          <CardDescription className="text-base">
            {result.isHealthy
              ? 'Keep up the excellent work! Here are tips to maintain your plant\'s health:'
              : 'Here are some recommendations to help your plant recover:'
            }
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          {/* AI Care Recommendations Loading State */}
          {isLoadingAiRecommendations && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                <div>
                  <h4 className="font-semibold text-blue-800 mb-1">Getting AI-Powered Care Recommendations</h4>
                  <p className="text-blue-700">Analyzing your plant's specific needs...</p>
                </div>
              </div>
            </div>
          )}

          {/* AI Recommendations Error */}
          {aiRecommendationsError && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-xl">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
                <div>
                  <h4 className="font-semibold text-yellow-800 mb-1">AI Recommendations Unavailable</h4>
                  <p className="text-yellow-700 text-sm">{aiRecommendationsError}</p>
                </div>
              </div>
            </div>
          )}

          {/* AI-Enhanced Care Recommendations */}
          {aiCareRecommendations && !isLoadingAiRecommendations && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <Bot className="w-5 h-5 text-purple-600" />
                {/* <h4 className="font-semibold text-purple-800">AI-Powered Recommendations</h4> */}
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                  {aiCareRecommendations.source}
                </span>
              </div>
              <div className="grid gap-3">
                {aiCareRecommendations.care_recommendations.map((recommendation, index) => (
                  <div key={`ai-${index}`} className="group">
                    <div className="flex items-start gap-4 p-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-xl hover:border-purple-300 hover:shadow-sm transition-all duration-200">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 group-hover:bg-purple-200 transition-colors">
                          {getCareIcon(recommendation)}
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-700 leading-relaxed font-medium">
                          {recommendation}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fallback to Original Care Recommendations */}
          {(!aiCareRecommendations || aiRecommendationsError) && !isLoadingAiRecommendations && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <h4 className="font-semibold text-emerald-800">Basic Care Recommendations</h4>
              </div>
              <div className="grid gap-4">
                {result.careRecommendations.map((recommendation, index) => (
                  <div key={`basic-${index}`} className="group">
                    <div className="flex items-start gap-4 p-4 bg-white border border-slate-200 rounded-xl hover:border-slate-300 hover:shadow-sm transition-all duration-200">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 group-hover:bg-emerald-200 transition-colors">
                          {getCareIcon(recommendation)}
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-slate-700 leading-relaxed font-medium">
                          {recommendation}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Button */}
          <div className="mt-6 pt-4 border-t border-slate-200">
            {/* Error Message */}
            {addToGardenStatus === 'error' && errorMessage && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700 text-sm">
                  ❌ {errorMessage}
                </p>
              </div>
            )}

            <button
              onClick={handleOpenAddDialog}
              disabled={isAddingToGarden || addToGardenStatus === 'success'}
              className={`w-full font-semibold py-3 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl ${addToGardenStatus === 'success'
                ? 'bg-green-600 text-white cursor-not-allowed opacity-75'
                : isAddingToGarden
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white'
                }`}
            >
              <div className="flex items-center justify-center gap-2">
                {isAddingToGarden ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Adding to Garden...
                  </>
                ) : addToGardenStatus === 'success' ? (
                  <>
                    <CheckCircle className="w-5 h-5" />
                    Added to Garden
                  </>
                ) : (
                  <>
                    <img
                      src={plant1Icon}
                      width={32}
                      height={32}
                      alt="icon"
                      className="inline-block"
                    /> Add to My Garden
                  </>
                )}
              </div>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Add Plant Dialog */}
      <AddPlantDialog
        result={result}
        isOpen={showAddPlantDialog}
        onClose={() => setShowAddPlantDialog(false)}
        onSuccess={(plantId, plantName) => {
          setAddToGardenStatus('success');
          setShowAddPlantDialog(false);
          if (onAddToGarden) {
            onAddToGarden(plantId, plantName);
          }
        }}
        originalImage={originalImage}
        aiCareRecommendations={aiCareRecommendations?.care_recommendations || undefined}
      />
    </div>
  );
}