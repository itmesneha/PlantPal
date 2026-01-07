# PlantPal Frontend - Code Explanation

## Overview
PlantPal is a React-TypeScript application that helps users identify plants, track their health, earn achievements, and purchase coupons with earned coins. Built with AWS Cognito authentication and a FastAPI backend.

---

## Architecture & Tech Stack

**Core Technologies:**
- React 18 + TypeScript
- React Router for navigation
- AWS Amplify (Cognito authentication)
- Tailwind CSS for styling
- shadcn/ui component library

**Key Libraries:**
- `lucide-react` - Icon library
- `aws-amplify/auth` - AWS Cognito integration
- `react-router-dom` - Client-side routing

---

## Application Structure

### 1. Entry Point (`App.tsx`)

**State Management:**
- `AppState`: Tracks UI flow (`loading` → `auth` → `dashboard` → `scanner` → `results`)
- `user`: Current authenticated user data
- `scanResult`: Plant scan analysis results
- `rescanPlantId`: Tracks if rescanning existing plant vs. new plant

**Authentication Flow:**
```typescript
checkAuthStatus() → getCurrentUser() → syncUserAfterAuth() → Dashboard
                   ↓ (if fails)
                 AuthForm
```

**Key Functions:**
- `checkAuthStatus()`: Verifies AWS Cognito session on app load
- `handleAuthSuccess()`: Syncs Cognito user with backend database
- `handleScanComplete()`: Stores scan results and transitions to results view
- `handleAddToGarden()`: Adds new plant or updates existing plant, then returns to dashboard

**Navigation Pattern:**
```
Auth → Dashboard → Scanner → Results → Dashboard
         ↓
    (back button available)
```

---

### 2. Dashboard Component (`Dashboard.tsx`)

**Purpose:** Central hub showing user's plants, achievements, leaderboard, and storefront.

**State Structure:**
- **Plants Data:** User's plant collection with health scores and streaks
- **Achievements:** Progress tracking for various milestones
- **Leaderboard:** Community rankings based on score
- **Coins/Score:** Virtual currency earned from achievements and scans

**Tab Navigation System:**
Four main tabs managed by `activeTab` state:
1. **My Plants** - Garden visualization + plant cards carousel
2. **Achievements** - Progress bars for unlockable achievements
3. **Leaderboard** - Top 10 users ranked by score
4. **Storefront** - Purchase discount coupons with coins

**Stats Cards (Top Row):**
- Total Plants (green)
- Avg Health (blue)
- Achievements (yellow)
- Best Streak (orange)
- Coins Remaining (yellow)
- User Score (purple)

**Plant Management Features:**
- Click plant → View details modal (health info, disease status, care notes)
- Edit plant name (inline editing)
- Delete plant (confirmation dialog)
- Rescan plant (triggers scanner with plant ID)

**Data Fetching:**
```typescript
useEffect(() => {
  fetchUserPlants();
  fetchAchievements();
  fetchUserScore();
  refreshCoinBalance();
}, []);
```

---

### 3. Plant Scanner (`PlantScanner.tsx`)

**Purpose:** Captures/uploads plant images for AI analysis.

**Workflow:**
1. User selects image (file input or camera)
2. Validates file (type, size via `plantScanService`)
3. Shows image preview
4. Sends to backend API (`/api/v1/scan`)
5. Receives: species, confidence, health score, disease, care recommendations

**Key Features:**
- Supports both new scans and rescans (via `plantId` prop)
- File validation (max 10MB, image types only)
- Loading state with spinner during API call
- Error handling with user-friendly messages

**API Call:**
```typescript
plantScanService.scanPlantImage(file, plantId?)
  → Backend: Plant.Net API + HuggingFace disease model
  → Returns: ScanResult
```

---

### 4. Plant Health Report (`PlantHealthReport.tsx`)

**Purpose:** Displays scan results and allows adding to garden.

**Shows:**
- Plant species identification + confidence %
- Health score (0-100) with visual indicator
- Disease detection status (if any)
- AI-generated care recommendations
- Current streak counter

**User Actions:**
- **Add to Garden** (new plants): Creates plant entry in DB
- **Update** (rescans): Updates existing plant's health data
- Automatically navigates back to dashboard after save

---

### 5. Achievement Card (`AchievementCard.tsx`)

**Purpose:** Displays individual achievement with progress tracking.

**Visual States:**
- **Completed:** Full color, checkmark badge, coin reward shown
- **Locked:** Greyscale filter, reduced opacity, grey badge

**Achievement Types (from backend):**
- `streak_*`: Maintain consecutive scan days
- `plants_count_*`: Own X number of plants
- `scans_count_*`: Perform X scans
- `healthy_plants_*`: Keep X plants healthy

**Progress Bar:** Shows `current_progress / requirement_value`

---

### 6. Garden Visualization (`GardenVisualization.tsx`)

**Purpose:** Visual grid display of user's plant collection.

**Layout:**
- Responsive grid (2-4 columns based on screen size)
- Plant icons with names and health scores
- Color-coded health indicators (green/yellow/red)
- "Add Plant" card prompts scanning

---

### 7. Storefront (`Storefront.tsx`)

**Purpose:** Virtual shop for purchasing discount coupons with coins.

**Features:**
- Displays coin balance (earned, spent, remaining)
- Lists 5 partner stores with plant products
- Three discount tiers: 5% (50 coins), 10% (100 coins), 20% (150 coins)
- Generates unique coupon codes on purchase
- Modal popup shows purchased coupon with code

**Coin Calculation:**
```typescript
earned = 30 (base) + (achievements * 20) + (streak * 5)
remaining = earned - spent
```

---

## Service Layer (`/services`)

### User Service (`userService.ts`)
- **syncUserAfterAuth()**: Creates/updates user in backend DB
- **getCurrentUser()**: Fetches user data with JWT auth
- **getUserStats()**: Returns streak, plants, scans, achievements
- **getLeaderboard()**: Fetches top N users by score

### Plant Services
- **plantsService.ts**: CRUD operations for plants
- **gardenService.ts**: Garden management (update, delete)
- **plantIconService.ts**: Maps icon strings to image assets

### Scan Services
- **plantScanService.ts**: Handles image upload and scan API calls
- **scanService.ts**: Retrieves plant health history

### Achievement Service (`achievementService.ts`)
- **getUserAchievements()**: Returns all achievements with progress
- **getAchievementStats()**: Summary (completed, in-progress)
- **checkStreaks()**: Backend call to update streak-based achievements

### Storefront Service (`storefrontService.ts`)
- **getBalance()**: Fetches coin balance
- **purchaseCoupon()**: Deducts coins, generates coupon code
- **listCoupons()**: Shows user's purchased coupons

---

## Authentication Flow

**AWS Cognito Integration:**
```typescript
// Sign in
signIn() → Cognito hosted UI → Redirect to /callback
         ↓
Callback component extracts tokens → syncUserAfterAuth()
         ↓
Backend creates User record → Returns User object
         ↓
Dashboard loads
```

**JWT Token Handling:**
- `fetchAuthSession()` retrieves ID token from Cognito
- Token sent in `Authorization: Bearer <token>` header
- Backend validates token against Cognito public keys
- Extracts `cognito:username` and `email` from token claims

**Protected Routes:**
All API calls use `makeAuthenticatedRequest()` which:
1. Gets current session
2. Extracts ID token
3. Adds to Authorization header
4. Backend validates and identifies user

---

## State Management Patterns

**No Redux/Context API** - Uses React hooks:
- `useState` for local component state
- `useEffect` for data fetching
- `useCallback` for memoized functions
- Prop drilling for sharing state between components

**Data Flow:**
```
App (top-level state)
 ↓ props
Dashboard (user, onScanPlant, onSignOut)
 ↓ props
PlantScanner (onScanComplete)
 ↓ callback
App (handleScanComplete) → updates scanResult state
 ↓ props
PlantHealthReport (result, onAddToGarden)
```

---

## UI Components (`/components/ui`)

**shadcn/ui Library:** Pre-built accessible components
- `Button`: Primary actions with variants (default, outline, ghost)
- `Card`: Container with header/content sections
- `Badge`: Labels and status indicators
- `Progress`: Visual progress bars
- `Tooltip`: Hover information popups
- `Alert`: Error/success messages
- `Toast`: Temporary notifications (via ToastContext)

**Styling Approach:**
- Tailwind utility classes for responsive design
- Custom CSS animations (plant-grow, card-hover)
- Breakpoints: `sm:` (640px), `md:` (768px), `lg:` (1024px)

---

## Key Features Implementation

### 1. Responsive Design
- Mobile-first approach with Tailwind breakpoints
- Grid layouts adapt: `grid-cols-2 lg:grid-cols-6`
- Text sizes scale: `text-xs sm:text-sm md:text-base`
- Icons resize: `w-5 h-5 sm:w-6 sm:h-6`

### 2. Plant Scanning Workflow
```
User uploads image → Validate (size, type) → Show preview
     ↓
Click "Scan Plant" → API call with FormData
     ↓
Backend: Plant.Net (species ID) + HuggingFace (disease detection)
     ↓
Return: species, confidence, health score, disease, care tips
     ↓
Display PlantHealthReport → User adds to garden
```

### 3. Achievement System
- Backend tracks progress automatically on scans/plants
- Frontend polls achievements on dashboard load
- Visual feedback: greyscale for locked, full color for completed
- Coin rewards shown on achievement cards

### 4. Streak Tracking
- Calculated based on consecutive days with scans
- Updated on each scan via `calculate_user_streak()` in backend
- Displayed in Dashboard stats and PlantHealthReport
- Affects coin earnings: `streak * 5 coins`

### 5. Plant Details Modal
- Shows comprehensive plant info:
  - Health score with color-coded progress bar
  - Disease status (red for detected, green for healthy)
  - Collapsible care notes from latest scan
  - Last scan date
- Actions: Edit name, Delete, Rescan

---

## Error Handling

**API Error Patterns:**
```typescript
try {
  const response = await fetch(url);
  if (!response.ok) throw new Error(response.statusText);
  return await response.json();
} catch (error) {
  console.error('API Error:', error);
  // Fallback to default values or show error UI
}
```

**Graceful Degradation:**
- Coin balance shows `0` if fetch fails (uses `?? 0` operator)
- Empty states for no plants/achievements/leaderboard entries
- Retry buttons on critical failures
- Toast notifications for user feedback

---

## Performance Optimizations

1. **Lazy Loading:** Components load on demand (React Router)
2. **Image Compression:** Scanner validates file size before upload
3. **Memoization:** `useCallback` for event handlers passed as props
4. **Conditional Rendering:** Only fetch leaderboard when tab active
5. **Debouncing:** Edit plant name waits for user to finish typing

---

## Environment Configuration

**Required Environment Variables:**
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_AWS_REGION=ap-southeast-1
REACT_APP_USER_POOL_ID=ap-southeast-1_xxxxx
REACT_APP_USER_POOL_CLIENT_ID=xxxxx
REACT_APP_COGNITO_DOMAIN=xxxxx.auth.ap-southeast-1.amazoncognito.com
```

**Files:** `.env`, `.env.local`, `.env.production`

---

## Build & Deployment

**Development:**
```bash
npm install
npm start  # Runs on localhost:3000
```

**Production:**
```bash
npm run build  # Creates optimized build in /build
```

**Deployed to:** AWS S3 static website hosting
**URL:** `http://plantpal-frontend-bucket.s3-website-ap-southeast-1.amazonaws.com`

---

## Integration with Backend

**API Endpoints Used:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/users/me` | GET | Get/create user |
| `/api/v1/users/stats` | GET | Fetch user statistics |
| `/api/v1/users/leaderboard` | GET | Get rankings |
| `/api/v1/scan` | POST | Analyze plant image |
| `/api/v1/plants` | GET | List user's plants |
| `/api/v1/garden` | POST/PUT/DELETE | Manage plants |
| `/api/v1/achievements` | GET | Fetch achievements |
| `/api/v1/storefront/balance` | GET | Get coin balance |
| `/api/v1/storefront/purchase` | POST | Buy coupon |

**Authentication:** All requests include `Authorization: Bearer <JWT>` header

---

## Future Enhancements

- Offline mode with local storage
- Push notifications for plant care reminders
- Social features (share garden, follow friends)
- Plant care calendar/scheduling
- Advanced filtering and search
- Export garden data (PDF/CSV)
