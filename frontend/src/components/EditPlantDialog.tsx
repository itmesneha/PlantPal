import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X, Loader2, Edit3, Save } from 'lucide-react';
import { gardenService, Plant, UpdatePlantRequest } from '../services/gardenService';

interface EditPlantDialogProps {
  plant: Plant;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedPlant: Plant) => void;
}

export function EditPlantDialog({ plant, isOpen, onClose, onSuccess }: EditPlantDialogProps) {
  const [plantName, setPlantName] = useState(plant.name);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState('');

  const handleUpdate = async () => {
    if (!plantName.trim()) {
      setError('Please enter a plant name');
      return;
    }

    if (plantName.trim() === plant.name) {
      // No changes made
      onClose();
      return;
    }

    setIsUpdating(true);
    setError('');

    try {
      const updateRequest: UpdatePlantRequest = {
        name: plantName.trim(),
      };

      const updatedPlant = await gardenService.updatePlant(plant.id, updateRequest);
      
      console.log('🌱 Plant updated:', updatedPlant);
      onSuccess(updatedPlant);
      onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to update plant');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleCancel = () => {
    setPlantName(plant.name); // Reset to original name
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md bg-white shadow-2xl">
        <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b relative">
          <button
            onClick={handleCancel}
            className="absolute right-4 top-4 p-2 rounded-full hover:bg-white/50 transition-colors"
            disabled={isUpdating}
          >
            <X className="w-5 h-5" />
          </button>
          <CardTitle className="text-xl flex items-center gap-3">
            <Edit3 className="w-5 h-5 text-blue-600" />
            Edit Plant
          </CardTitle>
          <CardDescription>
            Update your plant's name
          </CardDescription>
        </CardHeader>

        <CardContent className="p-6 space-y-4">
          {/* Plant Preview */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 p-4 rounded-xl border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 flex items-center justify-center text-2xl">
                {plant.plant_icon || '🌱'}
              </div>
              <div>
                <p className="text-sm text-gray-600">{plant.species}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs px-2 py-1 rounded ${
                    plant.current_health_score < 50 
                      ? 'bg-red-100 text-red-700' 
                      : 'bg-green-100 text-green-700'
                  }`}>
                    Health: {Math.round(plant.current_health_score)}/100
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {plant.streak_days} days
                  </span>
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
              disabled={isUpdating}
              autoFocus
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">❌ {error}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <Button
              onClick={handleCancel}
              variant="outline"
              className="flex-1"
              disabled={isUpdating}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdate}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
              disabled={isUpdating || !plantName.trim() || plantName.trim() === plant.name}
            >
              {isUpdating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}