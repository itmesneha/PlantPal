import { Card } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { CheckCircle, Lock } from 'lucide-react';
import { UserAchievement } from '../services/achievementService';

interface AchievementCardProps {
  userAchievement: UserAchievement;
}

export function AchievementCard({ userAchievement }: AchievementCardProps) {
    if (!userAchievement || !userAchievement.achievement) {
        return <div>Achievement data unavailable</div>;
      }
    const { achievement, current_progress, is_completed, completed_at } = userAchievement;
    
    const progressPercent = Math.min(
        (current_progress / achievement.requirement_value) * 100,
        100
    );

    return (
        <Card className={`achievement-card ${is_completed ? 'completed' : ''}`}>
        <div className="flex items-start gap-4">
            {/* Achievement Icon */}
            <div className={`text-3xl flex-shrink-0 ${is_completed ? 'scale-110' : ''}`}>
            {achievement.icon || '🏆'}
            </div>

            {/* Achievement Details */}
            <div className="flex-1 min-w-0">
            {/* Header with Title and Badge */}
            <div className="flex items-center justify-between gap-2 mb-1">
                <h3 className="achievement-title truncate">
                {achievement.name}
                </h3>
                {is_completed ? (
                <Badge className="bg-green-500 hover:bg-green-600 text-white whitespace-nowrap">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Unlocked
                </Badge>
                ) : (
                <Badge variant="secondary" className="whitespace-nowrap">
                    <Lock className="w-3 h-3 mr-1" />
                    Locked
                </Badge>
                )}
            </div>

            {/* Description */}
            <p className="achievement-description mb-3">
                {achievement.description}
            </p>

            {/* Progress Bar - Only show if NOT completed */}
            {!is_completed && (
                <div className="space-y-1">
                <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400">
                    <span>Progress</span>
                    <span>{current_progress} / {achievement.requirement_value}</span>
                </div>
                <Progress value={progressPercent} className="h-2" />
                </div>
            )}

            {/* Points and Completion Date */}
            <div className="flex items-center justify-between mt-3 text-xs">
                <span className="achievement-points flex items-center gap-2">
                {achievement.points_awarded} pts
                <span className="inline-flex items-center gap-1 bg-yellow-50 border border-yellow-200 text-yellow-800 px-2 py-0.5 rounded-full">
                    <span role="img" aria-label="coin">🪙</span>
                    +20 coins on unlock
                </span>
                </span>
                {is_completed && completed_at && (
                <span className="achievement-date">
                    Unlocked {new Date(completed_at).toLocaleDateString()}
                </span>
                )}
            </div>
            </div>
        </div>
        </Card>
    );
}