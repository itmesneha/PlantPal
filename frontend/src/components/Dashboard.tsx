import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Trophy, Award, Flame, Users, Calendar, TrendingUp } from 'lucide-react';
import { GardenVisualization } from './GardenVisualization';

interface Plant {
  id: string;
  name: string;
  species: string;
  healthScore: number;
  streak: number;
  lastCheckIn: string;
  image?: string;
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

interface DashboardProps {
  user: { name: string };
  onScanPlant: () => void;
}

export function Dashboard({ user, onScanPlant }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<'plants' | 'achievements' | 'leaderboard'>('plants');

  // Mock data - in real app this would come from your database
  const plants: Plant[] = [
    {
      id: '1',
      name: 'My Monstera',
      species: 'Monstera Deliciosa',
      healthScore: 92,
      streak: 14,
      lastCheckIn: '2024-01-15',
      image: 'https://images.unsplash.com/photo-1586771107445-d3ca888129ff?w=300'
    },
    {
      id: '2',
      name: 'Snake Plant',
      species: 'Sansevieria',
      healthScore: 85,
      streak: 7,
      lastCheckIn: '2024-01-14',
      image: 'https://images.unsplash.com/photo-1493652430944-bc5cd27c8e74?w=300'
    }
  ];

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
      progress: 14,
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

  const totalHealthScore = plants.reduce((sum, plant) => sum + plant.healthScore, 0) / plants.length;
  const earnedAchievements = achievements.filter(a => a.earned).length;

  return (
    <div className="space-y-6 p-4 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1>Welcome back, {user.name}!</h1>
          <p className="text-muted-foreground">
            Track your plants, earn achievements, and grow your garden
          </p>
        </div>
        <Button onClick={onScanPlant} className="w-full sm:w-auto">
          Scan New Plant
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Plants</p>
                <p className="text-2xl">{plants.length}</p>
              </div>
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span>🌱</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Health</p>
                <p className="text-2xl">{Math.round(totalHealthScore)}</p>
              </div>
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <TrendingUp className="w-4 h-4 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Achievements</p>
                <p className="text-2xl">{earnedAchievements}</p>
              </div>
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <Trophy className="w-4 h-4 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Best Streak</p>
                <p className="text-2xl">{Math.max(...plants.map(p => p.streak))}</p>
              </div>
              <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <Flame className="w-4 h-4 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('plants')}
          className={`px-4 py-2 rounded-md transition-colors ${
            activeTab === 'plants' ? 'bg-background shadow-sm' : 'hover:bg-background/50'
          }`}
        >
          My Plants
        </button>
        <button
          onClick={() => setActiveTab('achievements')}
          className={`px-4 py-2 rounded-md transition-colors ${
            activeTab === 'achievements' ? 'bg-background shadow-sm' : 'hover:bg-background/50'
          }`}
        >
          Achievements
        </button>
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`px-4 py-2 rounded-md transition-colors ${
            activeTab === 'leaderboard' ? 'bg-background shadow-sm' : 'hover:bg-background/50'
          }`}
        >
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
            <h3 className="mb-4">Plant Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {plants.map((plant) => (
                <Card key={plant.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{plant.name}</CardTitle>
                      <Badge variant={plant.healthScore >= 80 ? 'default' : 'secondary'}>
                        {plant.healthScore}/100
                      </Badge>
                    </div>
                    <CardDescription>{plant.species}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Progress value={plant.healthScore} />
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1">
                        <Flame className="w-3 h-3" />
                        {plant.streak} day streak
                      </span>
                      <span className="text-muted-foreground">
                        Last check: {plant.lastCheckIn}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              ))}
              
              {plants.length > 0 && (
                <Card className="border-dashed">
                  <CardContent className="flex flex-col items-center justify-center h-full min-h-[200px] space-y-3">
                    <div className="w-12 h-12 bg-muted rounded-full flex items-center justify-center">
                      <span className="text-2xl">🌱</span>
                    </div>
                    <p className="text-center text-muted-foreground">
                      Scan a new plant to add it to your garden
                    </p>
                    <Button onClick={onScanPlant} variant="outline">
                      Add Plant
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
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
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    entry.name === user.name ? 'bg-primary/10 border' : 'bg-muted/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      entry.rank === 1 ? 'bg-yellow-100 text-yellow-800' :
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