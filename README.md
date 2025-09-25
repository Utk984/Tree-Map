# Tree Map - React + deck.gl Implementation

This project has been converted from Python + pydeck to **React + deck.gl** for better performance and modern web development practices.

## 🚀 Features

- **Interactive map:** deck.gl-powered visualization with satellite imagery
- **Tree markers:** Forest green markers showing detected tree locations
- **Street view markers:** Blue markers showing street view panorama locations  
- **Connection lines:** Orange lines connecting trees to their corresponding street views
- **Click interactions:** Click on any tree marker to view the street-level perspective
- **Layer controls:** Toggle visibility of different map layers
- **Real-time data loading:** Loads tree and street view data from CSV files
- **Responsive design:** Works on desktop and mobile devices

## 📁 Project Structure

```
src/
├── App.tsx              # Main application component with deck.gl map
├── main.tsx             # React entry point
├── types.ts             # TypeScript type definitions
├── utils/
│   └── dataLoader.ts    # CSV data loading and processing utilities
└── components/
    ├── TreeModal.tsx    # Modal for displaying tree street views
    └── LayerControls.tsx # Map layer visibility controls

public/
├── south_delhi_trees_cleaned.csv    # Tree detection data
└── south_delhi_panoramas.csv        # Street view panorama data
```

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
npm install --legacy-peer-deps
```

> **Note:** The `--legacy-peer-deps` flag is used to resolve dependency conflicts between deck.gl and luma.gl packages.

### 2. Start Development Server

```bash
npm run dev
```

This will start the Vite development server on `http://localhost:3000`

### 3. Start Python API Server

In a separate terminal, start the Flask API server:

```bash
python api_server.py
```

This will start the API server on `http://localhost:5001` for serving tree view images.

## 🎯 Usage

1. **Explore the Map:** 
   - Pan and zoom to navigate the Delhi area
   - Use mouse wheel to zoom, click and drag to pan

2. **Layer Controls:**
   - Use the control panel on the top-right to toggle layer visibility
   - View counts for trees, street views, and connections

3. **Tree Interaction:**
   - Click on any green tree marker to view its street-level perspective
   - The modal will show the centered view of the tree from the street view panorama
   - Includes metadata like coordinates, confidence scores, and panorama ID

4. **Visual Elements:**
   - 🌳 **Green markers**: Detected trees
   - 🔵 **Blue markers**: Street view locations
   - 🧡 **Orange lines**: Connections between trees and street views

## 📊 Data Processing

The application processes two CSV files:

- **south_delhi_trees_cleaned.csv**: Contains tree detection data with coordinates, confidence scores, and panorama references
- **south_delhi_panoramas.csv**: Contains street view panorama locations and metadata

Key features:
- Filters trees with distance < 12 meters from panoramas
- Removes duplicate trees within 3 meters using spatial clustering
- Generates connection lines between trees and their source panoramas

## 🛡️ API Integration

The React frontend communicates with the Python Flask API for:

- **Tree view generation**: `/api/tree-view/{csv_index}`
- **Tree information**: `/api/tree-info/{csv_index}` 
- **Health checks**: `/health`

The API serves base64-encoded images of tree-centered views generated from street view panoramas.

## 🚀 Production Build

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

To preview the production build:

```bash
npm run preview
```

## 🔧 Technical Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development
- **deck.gl** - High-performance WebGL-powered data visualization
- **Vite** - Fast build tool and development server
- **MapLibre GL** - Open-source mapping library
- **Papa Parse** - CSV parsing library
- **Axios** - HTTP client for API requests

## 🌐 Deployment Options

### Static Hosting
The React build can be deployed to any static hosting service:
- Vercel
- Netlify  
- GitHub Pages
- AWS S3 + CloudFront

### With API Server
For full functionality including tree view generation:
1. Deploy the React build to static hosting
2. Deploy the Python Flask API to a cloud service (Heroku, Railway, etc.)
3. Update API URLs in the React app configuration

## 🐛 Troubleshooting

### "Unable to connect to server" errors
- Make sure the Flask API server is running on port 5001
- Check that CORS is properly configured in `api_server.py`

### CSV loading errors
- Ensure CSV files are in the `public/` directory
- Check that file names match exactly: `south_delhi_trees_cleaned.csv` and `south_delhi_panoramas.csv`

### Dependency installation issues
- Use `npm install --legacy-peer-deps` to resolve deck.gl peer dependency conflicts
- Clear npm cache with `npm cache clean --force` if needed

## 📈 Performance

The React + deck.gl implementation offers significant performance improvements over the Python + pydeck version:

- **Faster rendering**: WebGL-accelerated rendering for thousands of markers
- **Better interactivity**: Smooth pan/zoom operations
- **Reduced memory usage**: More efficient data handling in the browser
- **Hot reloading**: Instant updates during development

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit with descriptive messages
5. Push to your fork and submit a pull request

## 📝 License

This project maintains the same license as the original Python implementation.
