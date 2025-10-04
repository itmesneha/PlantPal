import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Flame, Users, LogOut, Loader2 } from 'lucide-react';
import { GardenVisualization } from './GardenVisualization';
import { plantsService } from '../services/plantsService';
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

interface DashboardProps {
  user: User;
  onScanPlant: () => void;
  onSignOut: () => void;
}

export function Dashboard({ user, onScanPlant, onSignOut }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<'plants' | 'achievements' | 'leaderboard'>('plants');
  const [plants, setPlants] = useState<Plant[]>([]);
  const [isLoadingPlants, setIsLoadingPlants] = useState(true);
  const [plantsError, setPlantsError] = useState<string>('');

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

  // Function to refresh plants (can be called after adding a new plant)
  const refreshPlants = async () => {
    try {
      const userPlants = await plantsService.getUserPlantsForDashboard();
      setPlants(userPlants);
    } catch (error) {
      console.error('❌ Failed to refresh plants:', error);
    }
  };

  // Mock data for achievements and leaderboard (these would also come from backend eventually)
  const achievements: Achievement[] = [
    {
      id: '1',
      name: 'Plant Doctor',
      description: 'Successfully treat 5 diseased plants',
      icon: '🩺',
      earned: false,
      progress: 2,
      requirement: 5
    },
    {
      id: '2',
      name: 'Green Thumb',
      description: 'Keep all plants healthy for 30 days',
      icon: '👍',
      earned: false,
      progress: 15,
      requirement: 30
    },
    {
      id: '3',
      name: 'Plant Collector',
      description: 'Add 10 plants to your garden',
      icon: '🌱',
      earned: false,
      progress: 2,
      requirement: 10
    },
    {
      id: '4',
      name: 'Daily Gardener',
      description: 'Check in daily for 7 days straight',
      icon: '📅',
      earned: true,
      progress: 7,
      requirement: 7
    }
  ];

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
  const earnedAchievements = achievements.filter(a => a.earned).length;
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
            onClick={onScanPlant}
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
                {/* <TrendingUp className="w-6 h-6 text-blue-600" /> */}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="card-hover plant-card border-yellow-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Achievements</p>
                <p className="text-3xl font-bold text-yellow-600">{earnedAchievements}</p>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-full flex items-center justify-center shadow-lg">
                <img
                  src={TrophyIcon}
                  width={32}
                  height={32}
                  alt="icon"
                  className="inline-block"
                />
                {/* <Trophy className="w-6 h-6 text-yellow-600" /> */}
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
                {/* <Flame className="w-6 h-6 text-orange-600" /> */}
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

            {/* Plants Grid */}
            {!isLoadingPlants && !plantsError && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {plants.map((plant) => (
                  <Card key={plant.id} className="card-hover plant-card border-green-200 shadow-lg">
                    <CardHeader className="pb-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{plant.icon || '🌱'}</span>
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

                {/* Add Plant Card - Only show if we have plants or no error */}
                <Card className="border-2 border-dashed border-green-300 card-hover">
                  <CardContent className="flex flex-col items-center justify-center h-full min-h-[250px] space-y-4 p-6">
                    <div className="w-16 h-16 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center shadow-lg">
                      <span className="text-3xl">🌱</span>
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
                      onClick={onScanPlant}
                      variant="outline"
                      size="lg"
                      className="border-green-600 text-green-600 hover:border-green-600 hover:text-green-800 hover:bg-green-50 transition-all duration-300">
                      <img src={plantScanIcon} width={32} height={32} className="inline-block mr-2" alt="scan icon" /> 
                      {plants.length === 0 ? 'Scan Your First Plant' : 'Scan New Plant'}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'achievements' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {achievements.map((achievement) => (
            <Card key={achievement.id} className={achievement.earned ? 'border-green-200 bg-green-50/50' : ''}>
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{achievement.icon}</div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{achievement.name}</CardTitle>
                    <CardDescription>{achievement.description}</CardDescription>
                  </div>
                  {achievement.earned && (
                    <Badge className="bg-green-100 text-green-800">Earned!</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{achievement.progress}/{achievement.requirement}</span>
                  </div>
                  <Progress value={(achievement.progress / achievement.requirement) * 100} />
                </div>
              </CardContent>
            </Card>
          ))}
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
    </div>
  );
}