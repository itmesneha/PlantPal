import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Button } from './ui/button';
import { plantIconService } from '../services/plantIconService';
import plantScanIcon from '../assets/plant_scan_icon.png';
import myGardenIcon from '../assets/my_garden.png';
import plant1Icon from '../assets/plant-icons/plant1.png';

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
  onScanPlant: (plantId?: string) => void;
}

export function GardenVisualization({ plants, onScanPlant }: GardenVisualizationProps) {
  return (
    <Card className="mb-4 sm:mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <img
            src={myGardenIcon}
            width={24}
            height={24}
            alt="icon"
            className="inline-block sm:w-8 sm:h-8"
          />
          <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-gray-800">My Garden</h3>
        </CardTitle>
        <CardDescription className="text-xs sm:text-sm">
          Overview of your plant collection
        </CardDescription>
      </CardHeader>
      <CardContent>
        {plants.length === 0 ? (
          <div className="flex items-center justify-center min-h-[150px] sm:min-h-[200px]">
            <div className="text-center space-y-3 sm:space-y-4">
              <div className="text-4xl sm:text-6xl"> <img
              src={plant1Icon}
              width={32}
              height={32}
              alt="icon"
              className="inline-block sm:w-12 sm:h-12"
            /> </div>
              <div>
                <h3 className="text-base sm:text-lg mb-2">Your garden is empty</h3>
                <p className="text-xs sm:text-sm text-muted-foreground mb-3 sm:mb-4 px-4">
                  Start by scanning your first plant to create your digital garden
                </p>
                 <Button
                      onClick={() => onScanPlant()}
                      variant="outline"
                      size="lg"
                      className="border-green-600 text-green-600 hover:border-green-600 hover:text-green-800 hover:bg-green-50 transition-all duration-300 text-xs sm:text-sm md:text-base">
                      <img src={plantScanIcon} width={24} height={24} className="inline-block mr-1 sm:mr-2 sm:w-8 sm:h-8" alt="scan icon" /> 
                      {plants.length === 0 ? 'Scan Your First Plant' : 'Scan New Plant'}
                    </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-5 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2 sm:gap-3 md:gap-4 p-2 sm:p-4">
            <TooltipProvider>
              {plants.map((plant) => {
                const iconAsset = plantIconService.getIconAsset(plant.icon || 'default');
                return (
                  <Tooltip key={plant.id}>
                    <TooltipTrigger asChild>
                      <div className="aspect-square bg-muted/30 rounded-lg p-2 sm:p-3 hover:bg-muted/50 cursor-pointer hover:scale-105 transform transition-all flex items-center justify-center">
                        <img 
                          src={iconAsset} 
                          alt={plant.name}
                          className="w-6 h-6 sm:w-8 sm:h-8 object-contain"
                        />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent 
                      className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 shadow-xl rounded-lg p-2 opacity-100 backdrop-blur-none"
                      sideOffset={8}
                      hideWhenDetached={true}
                    >
                      <div className="text-center space-y-1">
                        <p className="font-bold text-green-800 text-sm">{plant.name}</p>
                        <p className="text-xs text-green-600 font-medium">{plant.species}</p>
                        <div className="flex items-center justify-center gap-2 mt-1">
                          <Badge 
                            variant={plant.healthScore >= 80 ? 'default' : 'secondary'}
                            className={`px-2 py-0.5 rounded-full font-medium shadow-sm text-xs ${
                              plant.healthScore >= 80 
                                ? 'bg-green-100 text-green-800 border-green-300' 
                                : 'bg-yellow-100 text-yellow-800 border-yellow-300'
                            }`}
                          >
                            💚 {Math.round(plant.healthScore)}/100
                          </Badge>
                          <span className="text-xs font-medium text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded-full border border-orange-200">
                            🔥 {plant.streak} days
                          </span>
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
                    onClick={() => onScanPlant()}
                    className="aspect-square bg-muted/20 border-2 border-dashed border-muted-foreground/30 rounded-lg flex items-center justify-center hover:bg-muted/40 hover:border-muted-foreground/50 transition-all hover:scale-105 transform"
                  >
                    <span className="text-xl sm:text-2xl text-muted-foreground">+</span>
                  </button>
                </TooltipTrigger>
                <TooltipContent 
                  className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 shadow-xl rounded-lg p-2 opacity-100 backdrop-blur-none"
                  sideOffset={8}
                  hideWhenDetached={true}
                >
                  <p className="text-blue-800 font-medium flex items-center gap-1 text-xs">
                    ✨ Add a new plant
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )}
      </CardContent>
    </Card>
  );
}