# Frontend Setup & Running Instructions

## Prerequisites
- Node.js 18+ and npm/yarn installed
- Backend running on http://localhost:8000

## Installation

```bash
cd frontend
npm install
```

## Running the Frontend

```bash
npm run dev
```

The frontend will start at http://localhost:5173

## Build for Production

```bash
npm run build
npm run preview
```

## Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── TopBar.jsx              # Header with app name & user
│   │   ├── IconRail.jsx            # Left navigation (Chat, Orders)
│   │   ├── Layout.jsx              # Main layout wrapper
│   │   ├── ChatWindow.jsx          # Chat interface
│   │   ├── MessageBubble.jsx       # Message display
│   │   ├── ChatInput.jsx           # Message input form
│   │   ├── ActivityFeed.jsx        # Activity log from backend
│   │   └── UserSummary.jsx         # Order stats
│   ├── pages/
│   │   └── OrdersPage.jsx          # Orders history page
│   ├── App.jsx                     # Main app component
│   ├── main.jsx                    # Entry point
│   └── styles.css                  # Dark theme styles
├── public/
├── index.html
├── vite.config.js
└── package.json
```

## Features Implemented

### Step 1: Backend Foundation ✅
- FastAPI with Gemini agent
- All 4 tools: search_products, check_stock, get_price, initiate_purchase
- Guardrails (stock, budget checks)
- Audit logging
- CORS enabled for frontend

### Step 2-3: Customer Page Layout ✅
- Top bar with app name and user avatar
- Left icon rail (Chat active, Orders)
- Main chat window with messages
- Right panel (Activity Feed, User Summary)

### Step 3: Chat Core ✅
- Real-time chat with Gemini agent
- Product search and display
- Purchase flow
- Status indicators
- Message timestamps

### Step 4: Right Panel ✅
- ActivityFeed: Pulls audit log from backend
- UserSummary: Shows total orders and spent amount

### Step 5: Orders Page ✅
- List of completed orders
- Order details (Date, Amount, Status)
- Empty state

## Dark Theme Color Palette

- Background: #0A0A0F
- Surface: #14141C
- Elevated: #1C1C26
- Primary (Teal): #2DD4BF
- Success (Green): #3ECF8E
- Danger (Red): #F76C6C
- Text Primary: #F2F2F7
- Text Secondary: #9C9CAE

## API Endpoints Used

```
GET  /health              - Health check
POST /chat                - Chat with agent
GET  /search              - Direct search
GET  /audit-log           - Activity feed data
```

## Response Format Expected

### Chat Response
```json
{
  "reply": "Agent response text",
  "products": [
    {
      "id": 1,
      "name": "Product Name",
      "price": 999.99,
      "inStock": true
    }
  ],
  "status": {
    "type": "success|failed|pending",
    "message": "Status message",
    "icon": "✓|✕|⏳"
  }
}
```

### Audit Log Response
```json
[
  {
    "id": 1,
    "timestamp": "2024-08-23T10:30:45",
    "action_type": "search|check_stock|get_price|initiate_purchase",
    "input_data": {...},
    "output_data": {...},
    "razorpay_order_id": "order_xxx",
    "status": "success|failed|blocked",
    "user_message": "Original user intent"
  }
]
```

## Troubleshooting

### "Failed to fetch" errors
- Ensure backend is running on http://localhost:8000
- Check CORS is enabled
- Check browser console for specific errors

### Components not showing
- Verify all CSS files are imported
- Check console for import errors
- Ensure vite.config.js is properly configured

### Styling issues
- Check styles.css is imported in main.jsx
- Verify CSS variables are defined in :root
- Check for CSS specificity conflicts

## Development Tips

- Use React DevTools browser extension for component inspection
- Check Network tab in DevTools to see API calls
- Use console.log in components to debug state
- Live reload is enabled - changes auto-refresh

## Production Deployment

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Deploy `dist/` folder to your web server

3. Configure environment variables for API endpoint

4. Update VITE_API_URL if backend URL differs

## Next Steps

- Implement landing hero (optional)
- Add admin page with metrics
- Implement payment confirmation modal
- Add error boundaries
- Add loading skeletons
