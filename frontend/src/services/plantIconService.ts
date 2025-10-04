// Service for managing plant icons
import defaultIcon from '../assets/plant-icons/default.png';
import plant3Icon from '../assets/plant-icons/plant3.png';
import plant1Icon from '../assets/plant-icons/plant1.png';
import plant4Icon from '../assets/plant-icons/plant4.png';
import plant2Icon from '../assets/plant-icons/plant2.png';
import plant5Icon from '../assets/plant-icons/plant5.png';
import plant6Icon from '../assets/plant-icons/plant6.png';
import plant7Icon from '../assets/plant-icons/plant7.png';
import plant8Icon from '../assets/plant-icons/plant8.png';
import plant9Icon from '../assets/plant-icons/plant9.png';
import plant10Icon from '../assets/plant-icons/plant10.png';
import plant11Icon from '../assets/plant-icons/plant11.png';
import plant12Icon from '../assets/plant-icons/plant12.png';
import plant13Icon from '../assets/plant-icons/plant13.png';
import plant14Icon from '../assets/plant-icons/plant14.png';
import plant15Icon from '../assets/plant-icons/plant15.png';
import plant16Icon from '../assets/plant-icons/plant16.png';
import plant17Icon from '../assets/plant-icons/plant17.png';
import plant18Icon from '../assets/plant-icons/plant18.png';
import plant19Icon from '../assets/plant-icons/plant19.png';
import plant20Icon from '../assets/plant-icons/plant20.png';

export interface PlantIcon {
    id: string;
    asset: string; // Direct import path
}

// Icon asset mapping
const ICON_ASSETS: Record<string, string> = {
    'default': defaultIcon,
    'plant3': plant3Icon,
    'plant1': plant1Icon,
    'plant4': plant4Icon,
    'plant2': plant2Icon,
    'plant5': plant5Icon,
    'plant6': plant6Icon,
    'plant7': plant7Icon,
    'plant8': plant8Icon,
    'plant9': plant9Icon,
    'plant10': plant10Icon,
    'plant11': plant11Icon,
    'plant12': plant12Icon,
    'plant13': plant13Icon,
    'plant14': plant14Icon,
    'plant15': plant15Icon,
    'plant16': plant16Icon,
    'plant17': plant17Icon,
    'plant18': plant18Icon,
    'plant19': plant19Icon,
    'plant20': plant20Icon,
};

// Define all available plant icons
export const PLANT_ICONS: PlantIcon[] = [
    { id: 'default', asset: defaultIcon },
    { id: 'plant1', asset: plant1Icon },
    { id: 'plant2', asset: plant2Icon },
    { id: 'plant3', asset: plant3Icon },
    { id: 'plant4', asset: plant4Icon },
    { id: 'plant5', asset: plant5Icon },
    { id: 'plant6', asset: plant6Icon },
    { id: 'plant7', asset: plant7Icon },
    { id: 'plant8', asset: plant8Icon },
    { id: 'plant9', asset: plant9Icon },
    { id: 'plant10', asset: plant10Icon },
    { id: 'plant11', asset: plant11Icon },
    { id: 'plant12', asset: plant12Icon },
    { id: 'plant13', asset: plant13Icon },
    { id: 'plant14', asset: plant14Icon },
    { id: 'plant15', asset: plant15Icon },
    { id: 'plant16', asset: plant16Icon },
    { id: 'plant17', asset: plant17Icon },
    { id: 'plant18', asset: plant18Icon },
    { id: 'plant19', asset: plant19Icon },
    { id: 'plant20', asset: plant20Icon },

    // Add more icons here as you add PNG files
];

class PlantIconService {
    /**
     * Get all available plant icons
     */
    getAvailableIcons(): PlantIcon[] {
        return PLANT_ICONS;
    }



    /**
     * Get icon by ID
     */
    getIconById(id: string): PlantIcon | undefined {
        return PLANT_ICONS.find(icon => icon.id === id);
    }

    /**
     * Get the asset URL for an icon (direct import)
     */
    getIconAsset(iconId: string): string {
        const icon = this.getIconById(iconId);
        if (!icon) {
            // Fallback to default icon
            return ICON_ASSETS['default'] || defaultIcon;
        }
        return icon.asset;
    }

    /**
     * Get icon asset async (for compatibility)
     */
    async getIconAssetAsync(iconId: string): Promise<string> {
        return this.getIconAsset(iconId);
    }

    /**
     * Check if icon exists
     */
    hasIcon(iconId: string): boolean {
        return PLANT_ICONS.some(icon => icon.id === iconId);
    }

    /**
     * Get default icon ID
     */
    getDefaultIconId(): string {
        return 'default';
    }

    /**
     * Get default icon asset
     */
    getDefaultIconAsset(): string {
        return defaultIcon;
    }
}

export const plantIconService = new PlantIconService();