import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X, Loader2, CheckCircle } from 'lucide-react';
import { plantIconService, PlantIcon } from '../services/plantIconService';
import { gardenService, AddToGardenRequest } from '../services/gardenService';

interface PlantScanResult {
    species: string;
    confidence: number;
    isHealthy: boolean;
    disease?: string;
    healthScore: number;
    careRecommendations: string[];
}

interface AddPlantDialogProps {
    result: PlantScanResult;
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: (plantId: string, plantName: string) => void; // Optional success callback
    originalImage?: File;
}

// Icon Button Component
function IconButton({
    icon,
    isSelected,
    onClick,
    disabled
}: {
    icon: PlantIcon;
    isSelected: boolean;
    onClick: () => void;
    disabled: boolean;
}) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`p-3 rounded-lg border-2 transition-all ${disabled
                    ? 'opacity-30 cursor-not-allowed border-gray-100 bg-gray-50'
                    : `hover:scale-110 ${isSelected
                        ? 'border-green-500 bg-green-50 shadow-md'
                        : 'border-gray-200 hover:border-green-300 hover:bg-green-50'
                    }`
                }`}
        >
            <img
                src={icon.asset}
                alt={`Plant icon ${icon.id}`}
                className={`w-6 h-6 object-contain mx-auto ${disabled ? 'grayscale' : ''
                    }`}
            />
        </button>
    );
}

export function AddPlantDialog({ result, isOpen, onClose, onSuccess, originalImage }: AddPlantDialogProps) {
    const [plantName, setPlantName] = useState(result.species || 'My Plant');
    const [selectedIcon, setSelectedIcon] = useState('default');
    const [isAdding, setIsAdding] = useState(false);
    const [error, setError] = useState('');
    const [availableIcons, setAvailableIcons] = useState<PlantIcon[]>([]);

    // Load available icons when component mounts
    useEffect(() => {
        const icons = plantIconService.getAvailableIcons();
        setAvailableIcons(icons);
    }, []);

    // Get current selected icon asset
    const selectedIconAsset = plantIconService.getIconAsset(selectedIcon);

    const handleAddToGarden = async () => {
        if (!plantName.trim()) {
            setError('Please enter a plant name');
            return;
        }

        setIsAdding(true);
        setError('');

        try {
            // Prepare the request data
            const addRequest: AddToGardenRequest = {
                plant_name: plantName.trim(),
                species: result.species,
                common_name: result.species, // Use species as common name for now
                health_score: result.healthScore,
                care_notes: result.careRecommendations.join('; '), // Join recommendations as notes
                plant_icon: selectedIcon, // Include the selected icon
            };

            // Add image data if available
            if (originalImage) {
                try {
                    const base64Image = await gardenService.convertImageToBase64(originalImage);
                    addRequest.image_data = base64Image;
                } catch (imageError) {
                    console.warn('Failed to convert image, proceeding without image:', imageError);
                }
            }

            // Call the API
            const response = await gardenService.addToGarden(addRequest);

            console.log('🌱 Plant added to garden:', response);
            
            // Call the success callback if provided
            if (onSuccess) {
                onSuccess(response.plant_id, response.plant.name);
            }
            
            onClose(); // Close dialog on success
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to add plant');
        } finally {
            setIsAdding(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white shadow-2xl">
                <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b relative">
                    <button
                        onClick={onClose}
                        className="absolute right-4 top-4 p-2 rounded-full hover:bg-white/50 transition-colors"
                        disabled={isAdding}
                    >
                        <X className="w-5 h-5" />
                    </button>
                    <CardTitle className="text-2xl flex items-center gap-3">
                        <span className="text-3xl">🌱</span>
                        Customize Your Plant
                    </CardTitle>
                    <CardDescription className="text-base">
                        Give your {result.species} a personal touch before adding it to your garden
                    </CardDescription>
                </CardHeader>

                <CardContent className="p-6 space-y-6">
                    {/* Plant Preview */}
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-xl border">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 flex items-center justify-center">
                                <img
                                    src={selectedIconAsset}
                                    alt="Selected plant icon"
                                    className="w-10 h-10 object-contain"
                                />
                            </div>
                            <div>
                                <h3 className="font-semibold text-lg">{plantName || 'Unnamed Plant'}</h3>
                                <p className="text-gray-600">{result.species}</p>
                                <div className="flex items-center gap-2 mt-1">
                                    <span className="text-sm bg-green-100 text-green-700 px-2 py-1 rounded">
                                        Health: {Math.round(result.healthScore)}/100
                                    </span>
                                    {!result.isHealthy && result.disease && (
                                        <span className="text-sm bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                            {result.disease}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Plant Name Input */}
                    <div className="space-y-2">
                        <label htmlFor="plantName" className="text-sm font-medium text-gray-700">
                            Plant Name
                        </label>
                        <Input
                            id="plantName"
                            type="text"
                            value={plantName}
                            onChange={(e) => setPlantName(e.target.value)}
                            placeholder="Enter a name for your plant..."
                            className="text-lg"
                            disabled={isAdding}
                        />
                        <p className="text-sm text-gray-500">
                            Give your plant a unique name to make it personal!
                        </p>
                    </div>

                    {/* Icon Selection */}
                    <div className="space-y-3">
                        <label className="text-sm font-medium text-gray-700">
                            Choose an Icon
                        </label>
                        <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-2">
                            {availableIcons.map((icon, index) => {
                                const isIconDisabled = index >= 12; // First 12 icons (index 0-11) are enabled
                                return (
                                    <IconButton
                                        key={icon.id}
                                        icon={icon}
                                        isSelected={selectedIcon === icon.id}
                                        onClick={() => !isIconDisabled && setSelectedIcon(icon.id)}
                                        disabled={isAdding || isIconDisabled}
                                    />
                                );
                            })}
                        </div>
                        {/* <p className="text-sm text-gray-500">
              Selected: {availableIcons.find(icon => icon.id === selectedIcon)?.name || 'Default'}
            </p> */}
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                            <p className="text-red-700 text-sm">❌ {error}</p>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4 border-t">
                        <Button
                            onClick={onClose}
                            variant="outline"
                            className="flex-1"
                            disabled={isAdding}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleAddToGarden}
                            className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                            disabled={isAdding || !plantName.trim()}
                        >
                            {isAdding ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Adding...
                                </>
                            ) : (
                                <>
                                    <CheckCircle className="w-4 h-4 mr-2" />
                                    Add to Garden
                                </>
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}