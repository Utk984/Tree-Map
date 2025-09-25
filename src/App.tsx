import { useState, useEffect, useCallback, useMemo } from 'react';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { MapViewState, PickingInfo } from '@deck.gl/core';
import Map from 'react-map-gl/maplibre'; // Import Map from react-map-gl
import 'maplibre-gl/dist/maplibre-gl.css';
import { loadTreeData, loadStreetViewData } from './utils/dataLoader';
import { TreePopup } from './components/TreePopup';
import { ControlPanel } from './components/ControlPanel';
import { ThreePanoramaViewer } from './components/ThreePanoramaViewer';
import { BaseMapType } from './components/BaseMapSwitcher';
import { TreeData, StreetViewData, ClickedTreeInfo, LayerVisibility } from './types';

const INITIAL_VIEW_STATE: MapViewState = {
  latitude: 28.6139,
  longitude: 77.2090,
  zoom: 11,
  pitch: 0,
  bearing: 0,
};

function App() {
  console.log('🏗️ App component initializing...');

  const [viewState, setViewState] = useState<MapViewState>(INITIAL_VIEW_STATE);
  const [treeData, setTreeData] = useState<TreeData[]>([]);
  const [streetViewData, setStreetViewData] = useState<StreetViewData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clickedTree, setClickedTree] = useState<ClickedTreeInfo | null>(null);
  const [popupPosition, setPopupPosition] = useState<{ x: number; y: number } | null>(null);
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    trees: true,
    streetViews: true,
  });
  const [currentBaseMap, setCurrentBaseMap] = useState<BaseMapType>('satellite');

  console.log('🏗️ App component state initialized');

  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        console.log('🚀 App: Starting data load process...');

        console.log('📊 App: Loading tree data...');
        const trees = await loadTreeData();
        console.log('✅ App: Tree data loaded:', trees.length, 'records');

        console.log('📍 App: Loading street view data...');
        const streetViews = await loadStreetViewData();
        console.log('✅ App: Street view data loaded:', streetViews.length, 'records');

        setTreeData(trees);
        setStreetViewData(streetViews);
        console.log('💾 App: Data stored in state');


        if (trees.length > 0) {
          console.log('🎯 App: Calculating map bounds...');
          const bounds = calculateBounds(trees, streetViews);
          console.log('🎯 App: Bounds calculated:', bounds);
          setViewState({
            ...INITIAL_VIEW_STATE,
            latitude: bounds.center.lat,
            longitude: bounds.center.lng,
            zoom: bounds.zoom,
          });
          console.log('🎯 App: View state updated');
        }

        console.log('✅ App: Setting loading to false');
        setLoading(false);
        console.log('🎉 App: Data loading complete!');
      } catch (err) {
        console.error('Error loading data:', err);
        setError(`Failed to load data: ${err instanceof Error ? err.message : 'Unknown error'}`);
        setLoading(false);
      }
    };

    loadData();
  }, []);


  const calculateBounds = useCallback((trees: TreeData[], streetViews: StreetViewData[]) => {
    // Use reduce instead of spread operator to avoid call stack overflow with large datasets
    const allLats = trees.map(t => t.tree_lat).concat(streetViews.map(sv => sv.lat));
    const allLngs = trees.map(t => t.tree_lng).concat(streetViews.map(sv => sv.lng));

    const minLat = allLats.reduce((min, lat) => Math.min(min, lat), allLats[0]);
    const maxLat = allLats.reduce((max, lat) => Math.max(max, lat), allLats[0]);
    const minLng = allLngs.reduce((min, lng) => Math.min(min, lng), allLngs[0]);
    const maxLng = allLngs.reduce((max, lng) => Math.max(max, lng), allLngs[0]);

    const centerLat = (minLat + maxLat) / 2;
    const centerLng = (minLng + maxLng) / 2;

    const latRange = maxLat - minLat;
    const lngRange = maxLng - minLng;
    const maxRange = Math.max(latRange, lngRange);

    let zoom = 16;
    if (maxRange > 1) zoom = 8;
    else if (maxRange > 0.1) zoom = 11;
    else if (maxRange > 0.01) zoom = 14;

    return {
      center: { lat: centerLat, lng: centerLng },
      zoom,
    };
  }, []);

  const handleTreeClick = useCallback((info: PickingInfo, event: any) => {
    if (info.object && info.layer?.id === 'trees') {
      const tree = info.object as TreeData;
      console.log('Tree clicked:', tree);
      
      // Get mouse position relative to the viewport for proper popup positioning
      const x = event.clientX;
      const y = event.clientY;
      
      setClickedTree({
        csv_index: tree.csv_index,
        pano_id: tree.pano_id,
        tree_lat: tree.tree_lat,
        tree_lng: tree.tree_lng,
      });
      setPopupPosition({ x, y });
    }
  }, []);

  const handleCloseModal = useCallback(() => {
    setClickedTree(null);
    setPopupPosition(null);
  }, []);

  const handleLayerVisibilityChange = useCallback((layer: keyof LayerVisibility, visible: boolean) => {
    setLayerVisibility(prev => ({
      ...prev,
      [layer]: visible,
    }));
  }, []);

  const handleBaseMapChange = useCallback((baseMap: BaseMapType) => {
    console.log('🗺️ Changing base map to:', baseMap);
    setCurrentBaseMap(baseMap);
  }, []);

  console.log('🏗️ App render - current base map:', currentBaseMap);

  const getMapStyle = useCallback((baseMapType: BaseMapType) => {
    console.log('🎨 Getting map style for:', baseMapType);

    switch (baseMapType) {
      case 'satellite':
        return {
          version: 8,
          sources: {
            'esri-satellite': {
              type: 'raster',
              tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
              tileSize: 256,
            },
          },
          layers: [{
            id: 'esri-satellite',
            type: 'raster',
            source: 'esri-satellite',
          }],
        };
      case 'streets':
        return {
          version: 8,
          sources: {
            'osm-streets': {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
            },
          },
          layers: [{
            id: 'osm-streets',
            type: 'raster',
            source: 'osm-streets',
          }],
        };
      case 'minimal':
        return {
          version: 8,
          sources: {
            'carto-minimal': {
              type: 'raster',
              tiles: ['https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],
              tileSize: 256,
            },
          },
          layers: [{
            id: 'carto-minimal',
            type: 'raster',
            source: 'carto-minimal',
          }],
        };
      default:
        return {
          version: 8,
          sources: {
            'default-satellite': {
              type: 'raster',
              tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
              tileSize: 256,
            },
          },
          layers: [{
            id: 'default-satellite',
            type: 'raster',
            source: 'default-satellite',
          }],
        };
    }
  }, []);

  const layers = useMemo(() => {
    console.log('📚 Creating data layers');
    const layerArray = [
      layerVisibility.streetViews && streetViewData.length > 0
        ? new ScatterplotLayer({
            id: 'streetviews',
            data: streetViewData,
            getPosition: (d: StreetViewData) => [d.lng, d.lat],
            getColor: [30, 144, 255, 200],
            getRadius: 1,
            radiusMinPixels: 1,
            radiusMaxPixels: 10,
            pickable: true,
            autoHighlight: true,
          })
        : null,
      layerVisibility.trees && treeData.length > 0
        ? new ScatterplotLayer({
            id: 'trees',
            data: treeData,
            getPosition: (d: TreeData) => [d.tree_lng, d.tree_lat],
            getColor: [34, 139, 34, 200],
            getRadius: 1,
            radiusMinPixels: 1,
            radiusMaxPixels: 15,
            pickable: true,
            autoHighlight: true,
          })
        : null,
    ].filter(Boolean);

    console.log('📚 Final layers array:', layerArray.map(l => l?.id || 'unknown').join(', '));
    return layerArray;
  }, [layerVisibility, streetViewData, treeData]);

  if (loading) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '18px',
        color: '#666',
      }}>
        Loading tree data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        fontSize: '18px',
        color: '#d32f2f',
        textAlign: 'center',
        padding: '20px',
      }}>
        <div>
          <h2>Error Loading Data</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      height: '100vh', 
      width: '100vw', 
      display: 'flex',
      position: 'relative'
    }}>
      {/* Left Side - Map */}
      <div style={{
        width: '50%',
        height: '100%',
        padding: '10px',
        boxSizing: 'border-box',
        position: 'relative',
        backgroundColor: '#f0f0f0',
        borderRadius: '8px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: '8px',
          overflow: 'hidden',
          position: 'relative'
        }}>
          <DeckGL
            viewState={viewState}
            onViewStateChange={({ viewState }) => setViewState(viewState as MapViewState)}
            controller={true}
            layers={layers}
            onClick={handleTreeClick}
            getTooltip={(info) => {
              if (!info.object) return null;

              if (info.layer?.id === 'trees') {
                const tree = info.object as TreeData;
                return {
                  html: `
                    <div>
                      <b>Tree Location:</b> ${tree.tree_lat.toFixed(6)}, ${tree.tree_lng.toFixed(6)}<br/>
                      <b>Panorama ID:</b> ${tree.pano_id}<br/>
                      <b>CSV Index:</b> ${tree.csv_index}<br/>
                      <b>Confidence:</b> ${tree.conf?.toFixed(3) || 'N/A'}
                    </div>
                  `,
                  style: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    fontSize: '12px',
                    padding: '8px',
                    borderRadius: '4px',
                    maxWidth: '300px',
                  },
                };
              }

              if (info.layer?.id === 'streetviews') {
                const sv = info.object as StreetViewData;
                return {
                  html: `
                    <div>
                      <b>Street View:</b> ${sv.lat.toFixed(6)}, ${sv.lng.toFixed(6)}<br/>
                      <b>Panorama ID:</b> ${sv.pano_id}
                    </div>
                  `,
                  style: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    color: 'white',
                    fontSize: '12px',
                    padding: '8px',
                    borderRadius: '4px',
                  },
                };
              }

              return null;
            }}
          >
            <Map
              mapStyle={getMapStyle(currentBaseMap)}
              style={{ width: '100%', height: '100%' }}
            />
          </DeckGL>

          {/* Control Panel - Top left */}
          <div style={{
            position: 'absolute',
            top: '15px',
            left: '15px',
            zIndex: 1000
          }}>
            <ControlPanel 
              layerVisibility={layerVisibility}
              onVisibilityChange={handleLayerVisibilityChange}
              treeCount={treeData.length}
              streetViewCount={streetViewData.length}
              currentBaseMap={currentBaseMap}
              onBaseMapChange={handleBaseMapChange}
            />
          </div>
        </div>

      </div>

      {/* Right Side - Panorama Viewer */}
      <div style={{
        width: '50%',
        height: '100%',
        padding: '10px',
        boxSizing: 'border-box',
        backgroundColor: '#f0f0f0'
      }}>
        <div style={{
          width: '100%',
          height: '100%',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <ThreePanoramaViewer 
            panoId={clickedTree?.pano_id || null}
            treeLat={clickedTree?.tree_lat}
            treeLng={clickedTree?.tree_lng}
          />
        </div>
      </div>

      {/* Tree Popup - At main container level to avoid overflow issues */}
      {clickedTree && popupPosition && (
        <TreePopup 
          csvIndex={clickedTree.csv_index}
          panoId={clickedTree.pano_id}
          treeLat={clickedTree.tree_lat}
          treeLng={clickedTree.tree_lng}
          onClose={handleCloseModal}
          position={popupPosition}
        />
      )}
    </div>
  );
}

export default App;