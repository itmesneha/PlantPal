import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Flame, Users, LogOut, Loader2, X, Camera, Calendar, FileText, ChevronDown, ChevronUp, Edit3 } from 'lucide-react';
import { GardenVisualization } from './GardenVisualization';
import { plantsService } from '../services/plantsService';
import { plantIconService } from '../services/plantIconService';
import { gardenService } from '../services/gardenService';
import { scanService } from '../services/scanService';
import { achievementService, AchievementStats, UserAchievement } from '../services/achievementService';
import { AchievementCard } from './AchievementCard';
import plantScanIcon from '../assets/plant_scan_icon.png';
import fireIcon from '../assets/fire.png';
import plantUserIcon from '../assets/plant_user.png';
import gardenIcon from '../assets/garden.png';
import plantHealthIcon from '../assets/plantHealth.png';
import TrophyIcon from '../assets/trophy.png';
import myPlantsIcon from '../assets/my_plants.png';
import starIcon from '../assets/star.png';
import leaderboardIcon from '../assets/leaderboard.png';
import myPlantCollectionIcon from '../assets/plant_collection.png';
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
  commonName?: string;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  earned: boolean;
  progress: number;
  requirement: number;
}

interface User {
  id: string;
  cognito_user_id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at?: string;
}

interface PlantHealthInfo {
  lastDisease: string | null;
  lastCareNotes: string[] | null;
  lastScanDate: string | null;
  isHealthy: boolean;
}

interface DashboardProps {
  user: User;
  onScanPlant: (plantId?: string) => void;
  onSignOut: () => void;
}

export function Dashboard({ user, onScanPlant, onSignOut }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<'plants' | 'achievements' | 'leaderboard'>('plants');
  const [plants, setPlants] = useState<Plant[]>([]);
  const [isLoadingPlants, setIsLoadingPlants] = useState(true);
  const [plantsError, setPlantsError] = useState<string>('');
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [plantToDelete, setPlantToDelete] = useState<Plant | null>(null);
  const [isDeletingPlant, setIsDeletingPlant] = useState(false);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editingPlantName, setEditingPlantName] = useState('');
  const [isUpdatingPlant, setIsUpdatingPlant] = useState(false);
  const [showPlantDetails, setShowPlantDetails] = useState(false);
  const [selectedPlantForDetails, setSelectedPlantForDetails] = useState<Plant | null>(null);
  const [plantHealthInfo, setPlantHealthInfo] = useState<PlantHealthInfo | null>(null);
  const [isLoadingHealthInfo, setIsLoadingHealthInfo] = useState(false);
  const [isCareNotesExpanded, setIsCareNotesExpanded] = useState(false);
  
  const [userAchievements, setUserAchievements] = useState<UserAchievement[]>([]);
  const [achievementStats, setAchievementStats] = useState<AchievementStats | null>(null);
  const [achievementsLoading, setAchievementsLoading] = useState(true);
  const [achievementsError, setAchievementsError] = useState('');

  // Fetch user plants on component mount
  useEffect(() => {
    const fetchUserPlants = async () => {
      try {
        setIsLoadingPlants(true);
        setPlantsError('');

        console.log('🌱 Fetching user plants for dashboard...');
        const userPlants = await plantsService.getUserPlantsForDashboard();
        setPlants(userPlants);
        console.log('✅ User plants loaded:', userPlants);

      } catch (error) {
        console.error('❌ Failed to fetch user plants:', error);
        setPlantsError(error instanceof Error ? error.message : 'Failed to load plants');
        // Keep empty array so dashboard still renders
        setPlants([]);
      } finally {
        setIsLoadingPlants(false);
      }
    };

    fetchUserPlants();
  }, []);

  // Fetch Achievements
  useEffect(() => {
    const fetchAchievements = async () => {
      try {
        setAchievementsLoading(true);
        setAchievementsError('');

        console.log('🏆 Fetching achievements for dashboard...');
        // Fetch user's achievements and stats
        const [userAchievementsList, stats] = await Promise.all([
          achievementService.getUserAchievements(),
          achievementService.getAchievementStats()
        ]);

        setUserAchievements(userAchievementsList);
        setAchievementStats(stats);
        console.log('✅ Achievements loaded:', userAchievementsList);
        console.log('✅ Achievement stats loaded:', stats);
        // Check streaks on load
        await achievementService.checkStreaks();
      } catch (error) {
        console.error('Failed to fetch achievements:', error);
        setAchievementsError('Failed to load achievements');
      } finally {
        setAchievementsLoading(false);
      }
    };

    fetchAchievements(); // Call without user dependency check
  }, []);

  // Function to refresh plants (can be called after adding a new plant)
  const refreshPlants = async () => {
    try {
      const userPlants = await plantsService.getUserPlantsForDashboard();
      setPlants(userPlants);
    } catch (error) {
      console.error('❌ Failed to refresh plants:', error);
    }
  };

  const handleEditPlant = (plant: Plant) => {
    setIsEditingName(true);
    setEditingPlantName(plant.name);
  };

  const handleSaveEdit = async () => {
    if (!selectedPlantForDetails || !editingPlantName.trim()) return;

    if (editingPlantName.trim() === selectedPlantForDetails.name) {
      // No changes made
      setIsEditingName(false);
      return;
    }

    setIsUpdatingPlant(true);

    try {
      const updatedPlant = await gardenService.updatePlant(selectedPlantForDetails.id, {
        name: editingPlantName.trim()
      });

      // Update the plant in the local state
      setPlants(prevPlants =>
        prevPlants.map(p =>
          p.id === updatedPlant.id
            ? { ...p, name: updatedPlant.name }
            : p
        )
      );

      // Update the selected plant for details
      setSelectedPlantForDetails(prev => prev ? { ...prev, name: updatedPlant.name } : null);

      setIsEditingName(false);
      console.log('✅ Plant name updated:', updatedPlant.name);
    } catch (error) {
      console.error('❌ Failed to update plant name:', error);
      // You could add a toast notification here
    } finally {
      setIsUpdatingPlant(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditingName(false);
    setEditingPlantName('');
  };

  const handleDeletePlant = (plant: Plant) => {
    setPlantToDelete(plant);
    setShowDeleteDialog(true);
  };

  const confirmDeletePlant = async () => {
    if (!plantToDelete) return;

    console.log('🗑️ Attempting to delete plant:', {
      id: plantToDelete.id,
      name: plantToDelete.name,
      species: plantToDelete.species
    });

    setIsDeletingPlant(true);
    try {
      await gardenService.deletePlant(plantToDelete.id);
      // Remove the plant from the local state
      setPlants(prevPlants => prevPlants.filter(p => p.id !== plantToDelete.id));
      console.log('🗑️ Plant deleted successfully:', plantToDelete.name);
    } catch (error) {
      console.error('❌ Failed to delete plant:', error);
      // You might want to show an error toast here
    } finally {
      setIsDeletingPlant(false);
      setShowDeleteDialog(false);
      setPlantToDelete(null);
    }
  };

  const cancelDeletePlant = () => {
    setShowDeleteDialog(false);
    setPlantToDelete(null);
  };

  const handlePlantClick = async (plant: Plant) => {
    setSelectedPlantForDetails(plant);
    setShowPlantDetails(true);

    // Fetch health info including care notes from latest scan
    setIsLoadingHealthInfo(true);
    try {
      console.log('🔍 Fetching latest health info for plant:', plant.id);
      const healthInfo = await scanService.getLatestPlantHealthInfo(plant.id);
      setPlantHealthInfo(healthInfo);
      console.log('✅ Health info loaded:', healthInfo);
    } catch (error) {
      console.error('❌ Failed to fetch plant health info:', error);
      // Set default values if fetch fails
      setPlantHealthInfo({
        lastDisease: null,
        lastCareNotes: null,
        lastScanDate: null,
        isHealthy: true
      });
    } finally {
      setIsLoadingHealthInfo(false);
    }
  };

  const closePlantDetails = () => {
    setShowPlantDetails(false);
    setSelectedPlantForDetails(null);
    setPlantHealthInfo(null);
    setIsLoadingHealthInfo(false);
    setIsCareNotesExpanded(false);
  };

  const handleDeleteFromDetails = (plant: Plant) => {
    setPlantToDelete(plant);
    setShowDeleteDialog(true);
    setShowPlantDetails(false); // Close details modal
  };

  const handleScanFromDetails = (plant: Plant) => {
    // Close the details modal and trigger scan with plant ID for rescanning
    setShowPlantDetails(false);
    onScanPlant(plant.id); // Pass plant ID to rescan existing plant
  };

  // Mock data for leaderboard (these would also come from backend eventually)

  const leaderboard = [
    { rank: 1, name: 'Emma Green', score: 2847, plants: 12 },
    { rank: 2, name: 'John Plant', score: 2156, plants: 8 },
    { rank: 3, name: user.name, score: 1890, plants: plants.length },
    { rank: 4, name: 'Sarah Bloom', score: 1654, plants: 6 },
    { rank: 5, name: 'Mike Garden', score: 1432, plants: 5 }
  ];

  const totalHealthScore = plants.length > 0
    ? plants.reduce((sum, plant) => sum + plant.healthScore, 0) / plants.length
    : 0;
  const bestStreak = plants.length > 0 ? Math.max(...plants.map(p => p.streak)) : 0;

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent flex items-center">
            Welcome back, {user.name}!
            <img
              src={plantUserIcon}
              width={32}
              alt="icon"
              className="inline-block ml-2 align-middle"
            />
          </h1>
          <p className="text-lg text-gray-600">
            Track your plants, earn achievements, and grow your garden
          </p>
          <p className="text-sm text-gray-400">
            Member since {new Date(user.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Button
            onClick={() => onScanPlant()}
            variant="outline"
            size="lg"
            className="border-green-600 text-green-600 hover:border-green-600 hover:text-green-800 hover:bg-green-50 transition-all duration-300">
            <img src={plantScanIcon} width={32} height={32} className="inline-block mr-2" alt="scan icon" /> Scan New Plant
          </Button>
          <Button
            onClick={onSignOut}
            variant="outline"
            size="lg"
            className="border-gray-300 hover:border-red-300 hover:text-red-600 hover:bg-red-50 transition-all duration-300"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="card-hover plant-card border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Plants</p>
                <p className="text-3xl font-bold text-green-600">{plants.length}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center shadow-lg">
                <span className="text-2xl"><img
                  src={gardenIcon}
                  width={32}
                  height={32}
                  alt="icon"
                  className="inline-block"
                /></span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover plant-card border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Health</p>
                <p className="text-3xl font-bold text-blue-600">{Math.round(totalHealthScore)}%</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center shadow-lg">
                <img
                  src={plantHealthIcon}
                  width={32}
                  height={32}
                  alt="icon"
                  className="inline-block"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover plant-card border-yellow-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Achievements</p>
                <p className="text-3xl font-bold text-yellow-600">{achievementStats?.completed ?? 0}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-full flex items-center justify-center shadow-lg">
                <img
                  src={TrophyIcon}
                  width={32}
                  height={32}
                  alt="icon"
                  className="inline-block"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover plant-card border-orange-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Best Streak</p>
                <p className="text-3xl font-bold text-orange-600">{bestStreak}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-orange-200 rounded-full flex items-center justify-center shadow-lg">
                <img
                  src={fireIcon}
                  width={32}
                  height={32}
                  alt="icon"
                  className="inline-block"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-2 bg-white/80 backdrop-blur-sm p-2 rounded-xl shadow-lg border border-green-100 w-fit">
        <button
          onClick={() => setActiveTab('plants')}
          className={`px-6 py-3 rounded-lg transition-all duration-300 font-medium flex items-center gap-2 ${activeTab === 'plants'
            ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
            : 'text-gray-600 hover:bg-green-50 hover:text-green-600'
            }`}
        >
          <img
            src={myPlantsIcon}
            width={24}
            height={24}
            alt="icon"
            className="inline-block"
          />
          My Plants
        </button>
        <button
          onClick={() => setActiveTab('achievements')}
          className={`px-6 py-3 rounded-lg transition-all duration-300 font-medium flex items-center gap-2 ${activeTab === 'achievements'
            ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
            : 'text-gray-600 hover:bg-green-50 hover:text-green-600'
            }`}
        >
          <img
            src={starIcon}
            width={24}
            height={24}
            alt="icon"
            className="inline-block"
          />
          Achievements
        </button>
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`px-6 py-3 rounded-lg transition-all duration-300 font-medium flex items-center gap-2 ${activeTab === 'leaderboard'
            ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
            : 'text-gray-600 hover:bg-green-50 hover:text-green-600'
            }`}
        >
          <img
            src={leaderboardIcon}
            width={24}
            height={24}
            alt="icon"
            className="inline-block"
          />
          Leaderboard
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'plants' && (
        <div className="space-y-6">
          {/* Garden Visualization */}
          <GardenVisualization plants={plants} onScanPlant={onScanPlant} />

          {/* Plant Cards Grid */}
          <div>
            <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
              <img
                src={myPlantCollectionIcon}
                width={32}
                height={32}
                alt="icon"
                className="inline-block"
              />
              My Plant Collection
            </h3>

            {/* Loading State */}
            {isLoadingPlants && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center space-y-4">
                  <Loader2 className="w-8 h-8 animate-spin text-green-600 mx-auto" />
                  <p className="text-gray-600">Loading your plants...</p>
                </div>
              </div>
            )}

            {/* Error State */}
            {plantsError && !isLoadingPlants && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-700 mb-4">❌ {plantsError}</p>
                <Button
                  onClick={refreshPlants}
                  variant="outline"
                  className="border-red-300 text-red-600 hover:bg-red-50"
                >
                  Try Again
                </Button>
              </div>
            )}

            {/* Plants Carousel */}
            {!isLoadingPlants && !plantsError && (
              <div className="relative">
                {/* Scroll container */}
                <div className="flex gap-6 overflow-x-auto scrollbar-hide pb-4 pt-6 snap-x snap-mandatory scroll-smooth">
                  {plants.map((plant) => (
                    <Card
                      key={plant.id}
                      className="card-hover plant-card border-green-200 shadow-lg flex-shrink-0 w-80 snap-start mt-2 group relative cursor-pointer"
                      onClick={() => handlePlantClick(plant)}
                    >
                      {/* Action buttons - appear on hover */}
                      <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        {/* Delete button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeletePlant(plant);
                          }}
                          className="w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-md"
                          title={`Delete ${plant.name}`}
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                      <CardHeader className="pb-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 flex items-center justify-center">
                              <img
                                src={plantIconService.getIconAsset(plant.icon || 'default')}
                                alt={plant.name}
                                className="w-8 h-8 object-contain"
                              />
                            </div>
                            <div>
                              <CardTitle className="text-xl font-bold text-gray-800">{plant.name}</CardTitle>
                              <CardDescription className="text-gray-600 font-medium">{plant.species}</CardDescription>
                            </div>
                          </div>
                          <Badge
                            className={`px-3 py-1 text-sm font-medium ${plant.healthScore >= 80
                              ? 'bg-green-100 text-green-800 border-green-200'
                              : plant.healthScore >= 60
                                ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                                : 'bg-red-100 text-red-800 border-red-200'
                              }`}
                          >
                            {Math.round(plant.healthScore)}/100
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm font-medium">
                            <span>Health Score</span>
                            <span className={plant.healthScore >= 80 ? 'text-green-600' : plant.healthScore >= 60 ? 'text-yellow-600' : 'text-red-600'}>
                              {Math.round(plant.healthScore)}%
                            </span>
                          </div>
                          <Progress
                            value={plant.healthScore}
                            className="h-3"
                          />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="flex items-center gap-2 text-orange-600 font-medium">
                            <Flame className="w-4 h-4" />
                            {plant.streak} day streak
                          </span>
                          <span className="text-gray-500">
                            {plant.lastCheckIn}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {/* Add Plant Card - Always at the end */}
                  <Card className="border-2 border-dashed border-green-300 card-hover flex-shrink-0 w-80 snap-start mt-2">
                    <CardContent className="flex flex-col items-center justify-center h-full min-h-[250px] space-y-4 p-6">
                      <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center shadow-lg">
                        <span className="text-3xl"><img
                          src={plant1Icon}
                          width={32}
                          height={32}
                          alt="icon"
                          className="inline-block"
                        /> </span>
                      </div>
                      <div className="text-center space-y-2">
                        <p className="text-lg font-medium text-gray-700">
                          {plants.length === 0 ? 'Start Your Garden' : 'Add More Plants'}
                        </p>
                        <p className="text-gray-500">
                          {plants.length === 0
                            ? 'Scan your first plant to begin your digital garden'
                            : 'Scan a new plant to expand your garden'
                          }
                        </p>
                      </div>
                      <Button
                        onClick={() => onScanPlant()}
                        variant="outline"
                        size="lg"
                        className="border-green-600 text-green-600 hover:border-green-600 hover:text-green-800 hover:bg-green-50 transition-all duration-300">
                        <img src={plantScanIcon} width={32} height={32} className="inline-block mr-2" alt="scan icon" />
                        {plants.length === 0 ? 'Scan Your First Plant' : 'Scan New Plant'}
                      </Button>
                    </CardContent>
                  </Card>
                </div>

                {/* Scroll hint for mobile */}
                {plants.length > 0 && (
                  <div className="text-center mt-2">
                    <p className="text-sm text-gray-400">← Scroll horizontally to see all plants →</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'achievements' && (
        <div>
          {/* Achievement Loading (ADDED) */}
          {achievementsLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading achievements...</p>
            </div>
          ) : achievementsError ? (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <p className="text-red-700">❌ {achievementsError}</p>
            </div>
          ) : (
            // Display all possible achievements with user's progress - completed and in-progress
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* {userAchievements.map((userAchievement) => (
                <Card key={userAchievement.id} className={userAchievement.is_completed ? 'border-green-200 bg-green-50/50' : ''}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{userAchievement.achievement?.icon || '🏆'}</div>
                      <div className="flex-1">
                        <CardTitle className="text-lg">{userAchievement.achievement?.name}</CardTitle>
                        <CardDescription>{userAchievement.achievement?.description}</CardDescription>
                      </div>
                      {userAchievement.is_completed && (
                        <Badge className="bg-green-100 text-green-800">Earned!</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Progress</span>
                        <span>{userAchievement.current_progress}/{userAchievement.achievement?.requirement_value}</span>
                      </div>
                      <Progress value={(userAchievement.current_progress / (userAchievement.achievement?.requirement_value || 1)) * 100} />
                    </div>
                  </CardContent>
                </Card>
              ))} */
                userAchievements
                .sort((a, b) => {
                  if (a.is_completed !== b.is_completed) {
                    return a.is_completed ? 1 : -1;
                  }
                  return 0;
                })
                .map((userAchievement) => (
                  <AchievementCard 
                    key={userAchievement.id} 
                    userAchievement={userAchievement}
                  />
                ))
              }
            </div>
          )}
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Community Leaderboard
            </CardTitle>
            <CardDescription>
              See how you rank among other plant enthusiasts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {leaderboard.map((entry) => (
                <div
                  key={entry.rank}
                  className={`flex items-center justify-between p-3 rounded-lg ${entry.name === user.name ? 'bg-primary/10 border' : 'bg-muted/50'
                    }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${entry.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
                      entry.rank === 2 ? 'bg-gray-100 text-gray-800' :
                        entry.rank === 3 ? 'bg-orange-100 text-orange-800' :
                          'bg-muted text-muted-foreground'
                      }`}>
                      #{entry.rank}
                    </div>
                    <div>
                      <p className={entry.name === user.name ? 'font-medium' : ''}>
                        {entry.name} {entry.name === user.name && '(You)'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {entry.plants} plants
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{entry.score}</p>
                    <p className="text-sm text-muted-foreground">points</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Plant Details Modal */}
      {showPlantDetails && selectedPlantForDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white shadow-xl">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b relative">
              <button
                onClick={closePlantDetails}
                className="absolute right-4 top-4 p-2 rounded-full hover:bg-white/50 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 flex items-center justify-center bg-white rounded-full shadow-md">
                  <img
                    src={plantIconService.getIconAsset(selectedPlantForDetails.icon || 'default')}
                    alt={selectedPlantForDetails.name}
                    className="w-12 h-12 object-contain"
                  />
                </div>
                <div className="flex-1">
                  {isEditingName ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={editingPlantName}
                        onChange={(e) => setEditingPlantName(e.target.value)}
                        className="text-2xl font-light bg-white border border-gray-300 rounded px-2 py-1 flex-1"
                        disabled={isUpdatingPlant}
                        autoFocus
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleSaveEdit();
                          } else if (e.key === 'Escape') {
                            handleCancelEdit();
                          }
                        }}
                      />
                      <button
                        onClick={handleSaveEdit}
                        disabled={isUpdatingPlant || !editingPlantName.trim()}
                        className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 disabled:opacity-50"
                      >
                        {isUpdatingPlant ? '...' : '✓'}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        disabled={isUpdatingPlant}
                        className="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600 disabled:opacity-50"
                      >
                        ✗
                      </button>
                    </div>
                  ) : (
                    <div className="flex">
                      <CardTitle className="text-2xl font-light text-gray-800">{selectedPlantForDetails.name}</CardTitle>
                      <Button
                        onClick={() => handleEditPlant(selectedPlantForDetails)}
                      >
                        <Edit3 className="text-green-500" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {/* Health Score Section */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  Plant Health
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between text-sm font-medium">
                    <span>Health Score</span>
                    <span className={selectedPlantForDetails.healthScore >= 80 ? 'text-green-600' : selectedPlantForDetails.healthScore >= 60 ? 'text-yellow-600' : 'text-red-600'}>
                      {Math.round(selectedPlantForDetails.healthScore)}%
                    </span>
                  </div>
                  <Progress value={selectedPlantForDetails.healthScore} className="h-3" />
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-orange-600">
                      <Flame className="w-4 h-4" />
                      <span className="font-medium">{selectedPlantForDetails.streak} day streak</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-500">
                      <Calendar className="w-4 h-4" />
                      <span>Last check: {selectedPlantForDetails.lastCheckIn}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Plant Information */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                  <FileText className="w-4 h-4" />
                  Species
                </h4>
                <p className="text-blue-700">{selectedPlantForDetails.species}</p>
              </div>

              {/* Disease Status */}
              <div className={`p-4 rounded-lg ${isLoadingHealthInfo
                  ? 'bg-gray-50'
                  : plantHealthInfo?.isHealthy === false || plantHealthInfo?.lastDisease
                    ? 'bg-red-50 border border-red-200'
                    : 'bg-green-50 border border-green-200'
                }`}>
                <h4 className={`font-semibold mb-2 flex items-center gap-2 ${isLoadingHealthInfo
                    ? 'text-gray-600'
                    : plantHealthInfo?.isHealthy === false || plantHealthInfo?.lastDisease
                      ? 'text-red-800'
                      : 'text-green-800'
                  }`}>
                  <div className={`w-2 h-2 rounded-full ${isLoadingHealthInfo
                      ? 'bg-gray-400'
                      : plantHealthInfo?.isHealthy === false || plantHealthInfo?.lastDisease
                        ? 'bg-red-500'
                        : 'bg-green-500'
                    }`}></div>
                  Disease Status
                </h4>
                {isLoadingHealthInfo ? (
                  <div className="flex items-center gap-2 text-gray-500">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading health information...</span>
                  </div>
                ) : plantHealthInfo?.lastDisease ? (
                  <div className="space-y-2">
                    <p className="text-red-700 font-medium">
                      Last detected: {plantHealthInfo.lastDisease}
                    </p>
                    {plantHealthInfo.lastScanDate && (
                      <p className="text-red-600 text-xs">
                        Scanned: {new Date(plantHealthInfo.lastScanDate).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-green-700 font-medium">Plant appears healthy!</p>
                    {plantHealthInfo?.lastScanDate ? (
                      <p className="text-green-600 text-xs">
                        Last scan: {new Date(plantHealthInfo.lastScanDate).toLocaleDateString()}
                      </p>
                    ) : (
                      <p className="text-gray-500 text-xs">No scans performed yet</p>
                    )}
                  </div>
                )}
              </div>

              {/* Care Notes - Collapsible */}
              <div className="bg-purple-50 rounded-lg border border-purple-200">
                <button
                  onClick={() => setIsCareNotesExpanded(!isCareNotesExpanded)}
                  className="w-full p-4 flex items-center justify-between hover:bg-purple-100 transition-colors rounded-lg"
                >
                  <h4 className="font-semibold text-purple-800 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Care Notes
                    {!isLoadingHealthInfo && plantHealthInfo?.lastCareNotes && plantHealthInfo.lastCareNotes.length > 0 && (
                      <Badge className="bg-purple-100 text-purple-700 border-purple-300 text-xs">
                        {plantHealthInfo.lastCareNotes.length}
                      </Badge>
                    )}
                  </h4>
                  {isCareNotesExpanded ? (
                    <ChevronUp className="w-4 h-4 text-purple-600" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-purple-600" />
                  )}
                </button>

                {isCareNotesExpanded && (
                  <div className="px-4 pb-4 border-t border-purple-200/50">
                    {isLoadingHealthInfo ? (
                      <div className="flex items-center gap-2 text-gray-500 pt-3">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">Loading care recommendations...</span>
                      </div>
                    ) : plantHealthInfo?.lastCareNotes && plantHealthInfo.lastCareNotes.length > 0 ? (
                      <div className="space-y-3 pt-3">
                        <p className="text-purple-700 text-sm font-medium">Latest AI recommendations:</p>
                        <ul className="space-y-2">
                          {plantHealthInfo.lastCareNotes.map((note, index) => (
                            <li key={index} className="text-purple-600 text-sm flex items-start gap-2 p-2 bg-white rounded border border-purple-100">
                              <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0"></span>
                              <span className="leading-relaxed">{note}</span>
                            </li>
                          ))}
                        </ul>
                        {plantHealthInfo.lastScanDate && (
                          <p className="text-purple-500 text-xs mt-3 flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            From scan on {new Date(plantHealthInfo.lastScanDate).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    ) : (
                      <div className="pt-3">
                        <p className="text-purple-600 text-sm italic">
                          No care notes available. Scan your plant to get AI-powered care recommendations!
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-4 border-t">
                <Button
                  onClick={() => handleScanFromDetails(selectedPlantForDetails)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Scan New Photo
                </Button>
                <Button
                  onClick={() => handleDeleteFromDetails(selectedPlantForDetails)}
                  variant="outline"
                  className="flex-1 border-red-300 text-red-600 hover:bg-red-50 hover:border-red-400"
                >
                  <X className="w-4 h-4 mr-2" />
                  Delete Plant
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteDialog && plantToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md bg-white shadow-xl">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl text-red-600 flex items-center gap-2">
                <X className="w-5 h-5" />
                Delete Plant
              </CardTitle>
              <CardDescription>
                Are you sure you want to remove <strong>{plantToDelete.name}</strong> from your garden? This action cannot be undone.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 flex items-center justify-center">
                  <img
                    src={plantIconService.getIconAsset(plantToDelete.icon || 'default')}
                    alt={plantToDelete.name}
                    className="w-6 h-6 object-contain"
                  />
                </div>
                <div>
                  <p className="font-medium text-gray-800">{plantToDelete.name}</p>
                  <p className="text-sm text-gray-600">{plantToDelete.species}</p>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  onClick={cancelDeletePlant}
                  variant="outline"
                  className="flex-1"
                  disabled={isDeletingPlant}
                >
                  Cancel
                </Button>
                <Button
                  onClick={confirmDeletePlant}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                  disabled={isDeletingPlant}
                >
                  {isDeletingPlant ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    <>
                      <X className="w-4 h-4 mr-2" />
                      Delete Plant
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}