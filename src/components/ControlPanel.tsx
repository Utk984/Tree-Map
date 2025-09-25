import React, { useState } from 'react';
import { LayerVisibility, BaseMapType } from '../types';

interface ControlPanelProps {
  // Layer controls
  layerVisibility: LayerVisibility;
  onVisibilityChange: (layer: keyof LayerVisibility, visible: boolean) => void;
  treeCount: number;
  streetViewCount: number;
  
  // Base map controls
  currentBaseMap: BaseMapType;
  onBaseMapChange: (baseMap: BaseMapType) => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  layerVisibility,
  onVisibilityChange,
  treeCount,
  streetViewCount,
  currentBaseMap,
  onBaseMapChange
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const panelStyle: React.CSSProperties = {
    position: 'absolute',
    top: '20px',
    right: '20px',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: '10px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: '14px',
    minWidth: '200px',
    zIndex: 100,
    overflow: 'hidden',
    transition: 'all 0.3s ease'
  };

  const headerStyle: React.CSSProperties = {
    padding: '15px 20px',
    backgroundColor: '#f8f9fa',
    borderBottom: '1px solid #eee',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    userSelect: 'none'
  };

  const contentStyle: React.CSSProperties = {
    padding: '20px',
    display: isCollapsed ? 'none' : 'block'
  };

  const titleStyle: React.CSSProperties = {
    margin: '0',
    fontSize: '16px',
    fontWeight: '600',
    color: '#333'
  };

  const sectionStyle: React.CSSProperties = {
    marginBottom: '20px'
  };

  const sectionTitleStyle: React.CSSProperties = {
    margin: '0 0 10px 0',
    fontSize: '14px',
    fontWeight: '600',
    color: '#555',
    borderBottom: '1px solid #eee',
    paddingBottom: '5px'
  };

  const layerItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '8px',
    padding: '5px 0'
  };

  const checkboxStyle: React.CSSProperties = {
    marginRight: '8px',
    transform: 'scale(1.1)'
  };

  const labelStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    flex: 1
  };

  const countStyle: React.CSSProperties = {
    fontSize: '11px',
    color: '#666',
    backgroundColor: '#f5f5f5',
    padding: '2px 6px',
    borderRadius: '8px',
    marginLeft: '8px'
  };

  const layerColorStyle = (color: string): React.CSSProperties => ({
    width: '10px',
    height: '10px',
    borderRadius: '50%',
    backgroundColor: color,
    marginLeft: '6px',
    border: '1px solid rgba(0,0,0,0.1)'
  });

  const mapButtonStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'block',
    width: '100%',
    padding: '8px 12px',
    border: 'none',
    backgroundColor: isActive ? '#2196f3' : 'transparent',
    color: isActive ? 'white' : '#333',
    cursor: 'pointer',
    fontSize: '13px',
    textAlign: 'left',
    transition: 'all 0.2s ease',
    borderRadius: '4px',
    marginBottom: '4px'
  });

  const mapStyles = [
    {
      id: 'satellite' as BaseMapType,
      name: '🛰️ Satellite',
      description: 'Esri World Imagery'
    },
    {
      id: 'streets' as BaseMapType,
      name: '🗺️ Streets',
      description: 'OpenStreetMap'
    },
    {
      id: 'minimal' as BaseMapType,
      name: '⚪ Minimal',
      description: 'CartoDB Positron'
    }
  ];

  return (
    <div style={panelStyle}>
      <div style={headerStyle} onClick={() => setIsCollapsed(!isCollapsed)}>
        <h3 style={titleStyle}>Map Controls</h3>
        <span style={{ fontSize: '18px', color: '#666' }}>
          {isCollapsed ? '▼' : '▲'}
        </span>
      </div>
      
      <div style={contentStyle}>
        {/* Layer Controls Section */}
        <div style={sectionStyle}>
          <h4 style={sectionTitleStyle}>Layers</h4>
          
          <div style={layerItemStyle}>
            <label style={labelStyle}>
              <input
                type="checkbox"
                checked={layerVisibility.trees}
                onChange={(e) => onVisibilityChange('trees', e.target.checked)}
                style={checkboxStyle}
              />
              Trees
              <div style={layerColorStyle('rgba(34, 139, 34, 0.8)')} />
            </label>
            <span style={countStyle}>{treeCount.toLocaleString()}</span>
          </div>

          <div style={layerItemStyle}>
            <label style={labelStyle}>
              <input
                type="checkbox"
                checked={layerVisibility.streetViews}
                onChange={(e) => onVisibilityChange('streetViews', e.target.checked)}
                style={checkboxStyle}
              />
              Street Views
              <div style={layerColorStyle('rgba(30, 144, 255, 0.8)')} />
            </label>
            <span style={countStyle}>{streetViewCount.toLocaleString()}</span>
          </div>

        </div>

        {/* Base Map Section */}
        <div style={sectionStyle}>
          <h4 style={sectionTitleStyle}>Base Map</h4>
          {mapStyles.map((style) => (
            <button
              key={style.id}
              style={mapButtonStyle(currentBaseMap === style.id)}
              onClick={() => onBaseMapChange(style.id)}
              onMouseEnter={(e) => {
                if (currentBaseMap !== style.id) {
                  (e.target as HTMLButtonElement).style.backgroundColor = '#f5f5f5';
                }
              }}
              onMouseLeave={(e) => {
                if (currentBaseMap !== style.id) {
                  (e.target as HTMLButtonElement).style.backgroundColor = 'transparent';
                }
              }}
            >
              <div>
                <strong>{style.name}</strong>
              </div>
              <div style={{ fontSize: '11px', color: 'inherit', opacity: 0.7 }}>
                {style.description}
              </div>
            </button>
          ))}
        </div>

        {/* Info Section */}
        <div style={{
          marginTop: '15px',
          paddingTop: '10px',
          borderTop: '1px solid #eee',
          fontSize: '11px',
          color: '#666'
        }}>
          <p style={{ margin: '3px 0' }}>
            <strong>🌳 Click trees</strong> for street view
          </p>
          <p style={{ margin: '3px 0' }}>
            Satellite imagery © Esri
          </p>
        </div>
      </div>
    </div>
  );
};
