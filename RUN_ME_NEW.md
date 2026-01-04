# 🚀 CO2Watch India - Futuristic Dashboard

This is the **Hackathon Winning** version of the dashboard, combining your powerful AI backend with a cutting-edge Glassmorphism UI.

## ✨ Features
- **Futuristic UI**: Neon styling, glassmorphism cards, and Orbitron fonts.
- **3D Globe**: Interactive 3D Earth visualization on the landing page.
- **AI Integration**: Fully connected to your `src.ai.ClimateIntelligence` module.
- **Live Data**: Loads from `output/detections.csv` automatically.
- **Interactive Maps**: PyDeck 3D scatterplots for emission visualization.

## 🛠️ How to Run

1. **Install Dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   streamlit run app.py
   ```

3. **AI Configuration**:
   - Ensure your `.env` file has a valid `GROQ_API_KEY` to enable the AI features.
   - If the key is missing, the AI tabs will show a "Demo Mode" warning.

## 🎮 Controls
- **Landing Page**: Click "VIEW LIVE DASHBOARD" to enter the main interface.
- **Sidebar**: Use the hamburger menu (top-left) to filter data by confidence or date.
- **Tabs**: Switch between Geospatial Maps, Analytics, and AI Reports.
