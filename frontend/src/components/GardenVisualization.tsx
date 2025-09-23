import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';

interface Plant {
  id: string;
  name: string;
  species: string;
  healthScore: number;
  streak: number;
  lastCheckIn: string;
  image?: string;
}

interface GardenVisualizationProps {
  plants: Plant[];
  onScanPlant: () => void;
}

export function GardenVisualization({ plants, onScanPlant }: GardenVisualizationProps) {
  const getPlantIcon = (species: string, healthScore: number) => {
    const isHealthy = healthScore >= 80;
    const isModerate = healthScore >= 60;
    
    // Different SVG icons based on plant type and health
    if (species.toLowerCase().includes('monstera')) {
      return (
        <svg viewBox="0 0 48 48" className="w-full h-full">
          <path
            d="M24 6c-2 0-4 1-6 3-1 1-2 3-2 5 0 1 0 2 1 3l-3 3c-2 2-3 4-3 7 0 3 1 5 3 7l6 6c2 2 4 3 7 3s5-1 7-3l6-6c2-2 3-4 3-7 0-3-1-5-3-7l-3-3c1-1 1-2 1-3 0-2-1-4-2-5-2-2-4-3-6-3z"
            fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'}
            opacity="0.8"
          />
          <path
            d="M18 18c0-1 1-2 2-2h8c1 0 2 1 2 2v2c0 1-1 2-2 2h-8c-1 0-2-1-2-2v-2z"
            fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'}
          />
          <circle cx="20" cy="26" r="2" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
          <circle cx="28" cy="26" r="2" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
        </svg>
      );
    } else if (species.toLowerCase().includes('snake') || species.toLowerCase().includes('sansevieria')) {
      return (
        <svg viewBox="0 0 48 48" className="w-full h-full">
          <rect x="14" y="8" width="4" height="32" rx="2" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} />
          <rect x="18" y="6" width="4" height="36" rx="2" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
          <rect x="22" y="4" width="4" height="40" rx="2" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} />
          <rect x="26" y="8" width="4" height="32" rx="2" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
          <rect x="30" y="12" width="4" height="24" rx="2" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} />
        </svg>
      );
    } else if (species.toLowerCase().includes('rose')) {
      return (
        <svg viewBox="0 0 48 48" className="w-full h-full">
          <circle cx="24" cy="20" r="8" fill={isHealthy ? '#f43f5e' : isModerate ? '#fb7185' : '#fda4af'} opacity="0.8" />
          <circle cx="24" cy="20" r="5" fill={isHealthy ? '#e11d48' : isModerate ? '#f43f5e' : '#fb7185'} />
          <rect x="22" y="20" width="4" height="16" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} />
          <path d="M18 28 L22 26 L18 24" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
          <path d="M30 28 L26 26 L30 24" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} />
        </svg>
      );
    } else {
      // Generic plant icon
      return (
        <svg viewBox="0 0 48 48" className="w-full h-full">
          <circle cx="24" cy="16" r="10" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} opacity="0.6" />
          <circle cx="20" cy="20" r="6" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} opacity="0.8" />
          <circle cx="28" cy="20" r="6" fill={isHealthy ? '#16a34a' : isModerate ? '#ca8a04' : '#dc2626'} opacity="0.8" />
          <rect x="22" y="26" width="4" height="14" fill={isHealthy ? '#22c55e' : isModerate ? '#eab308' : '#ef4444'} />
        </svg>
      );
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          🌻 My Garden
        </CardTitle>
        <CardDescription>
          Visual overview of your plant collection
        </CardDescription>
      </CardHeader>
      <CardContent>
        {plants.length === 0 ? (
          <div className="flex items-center justify-center min-h-[200px]">
            <div className="text-center space-y-4">
              <div className="text-6xl">🌱</div>
              <div>
                <h3 className="text-lg mb-2">Your garden is empty</h3>
                <p className="text-muted-foreground mb-4">
                  Start by scanning your first plant to create your digital garden
                </p>
                <button
                  onClick={onScanPlant}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                >
                  Scan Your First Plant
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-4 p-4">
            <TooltipProvider>
              {plants.map((plant) => (
                <Tooltip key={plant.id}>
                  <TooltipTrigger asChild>
                    <div className="aspect-square bg-muted/30 rounded-lg p-3 hover:bg-muted/50 transition-colors cursor-pointer hover:scale-105 transform transition-transform">
                      {getPlantIcon(plant.species, plant.healthScore)}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <div className="text-center">
                      <p className="font-medium">{plant.name}</p>
                      <p className="text-sm text-muted-foreground">{plant.species}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant={plant.healthScore >= 80 ? 'default' : 'secondary'}>
                          {plant.healthScore}/100
                        </Badge>
                        <span className="text-sm">🔥 {plant.streak} days</span>
                      </div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              ))}
              
              {/* Add plant button */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={onScanPlant}
                    className="aspect-square bg-muted/20 border-2 border-dashed border-muted-foreground/30 rounded-lg flex items-center justify-center hover:bg-muted/40 hover:border-muted-foreground/50 transition-all hover:scale-105 transform"
                  >
                    <span className="text-2xl text-muted-foreground">+</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Add a new plant</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </CardContent>
    </Card>
  );
}