import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { plantIconService } from '../services/plantIconService';
import myGardenIcon from '../assets/my_garden.png';

interface Plant {
  id: string;
  name: string;
  species: string;
  healthScore: number;
  streak: number;
  lastCheckIn: string;
  image?: string;
  icon?: string;
}

interface GardenVisualizationProps {
  plants: Plant[];
  onScanPlant: () => void;
}

export function GardenVisualization({ plants, onScanPlant }: GardenVisualizationProps) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <img
            src={myGardenIcon}
            width={32}
            height={32}
            alt="icon"
            className="inline-block"
          />
          <h3 className="text-2xl font-bold text-gray-800">My Garden</h3>
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
              {plants.map((plant) => {
                const iconAsset = plantIconService.getIconAsset(plant.icon || 'default');
                return (
                  <Tooltip key={plant.id}>
                    <TooltipTrigger asChild>
                      <div className="aspect-square bg-muted/30 rounded-lg p-3 hover:bg-muted/50 transition-colors cursor-pointer hover:scale-105 transform transition-transform flex items-center justify-center">
                        <img 
                          src={iconAsset} 
                          alt={plant.name}
                          className="w-8 h-8 object-contain"
                        />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <div className="text-center">
                        <p className="font-medium">{plant.name}</p>
                        <p className="text-sm text-muted-foreground">{plant.species}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant={plant.healthScore >= 80 ? 'default' : 'secondary'}>
                            {Math.round(plant.healthScore)}/100
                          </Badge>
                          <span className="text-sm">🔥 {plant.streak} days</span>
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}

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