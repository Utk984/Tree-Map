import React from 'react';
import { LayerVisibility } from '../types';

interface LayerControlsProps {
  layerVisibility: LayerVisibility;
  onVisibilityChange: (layer: keyof LayerVisibility, visible: boolean) => void;
  treeCount: number;
  streetViewCount: number;
  connectionCount: number;
}

export const LayerControls: React.FC<LayerControlsProps> = ({
  layerVisibility,
  onVisibilityChange,
  treeCount,
  streetViewCount,
  connectionCount
}) => {
  const controlStyle: React.CSSProperties = {
    position: 'absolute',
    top: '20px',
    right: '20px',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    padding: '20px',
    borderRadius: '10px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: '14px',
    minWidth: '200px',
    zIndex: 100
  };

  const titleStyle: React.CSSProperties = {
    margin: '0 0 15px 0',
    fontSize: '16px',
    fontWeight: '600',
    color: '#333',
    borderBottom: '1px solid #eee',
    paddingBottom: '8px'
  };

  const layerItemStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '10px',
    padding: '5px 0'
  };

  const checkboxStyle: React.CSSProperties = {
    marginRight: '8px',
    transform: 'scale(1.2)'
  };

  const labelStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    cursor: 'pointer',
    flex: 1
  };

  const countStyle: React.CSSProperties = {
    fontSize: '12px',
    color: '#666',
    backgroundColor: '#f5f5f5',
    padding: '2px 6px',
    borderRadius: '10px',
    marginLeft: '8px'
  };

  const layerColorStyle = (color: string): React.CSSProperties => ({
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    backgroundColor: color,
    marginLeft: '8px',
    border: '1px solid rgba(0,0,0,0.1)'
  });

  return (
    <div style={controlStyle}>
      <h3 style={titleStyle}>Map Layers</h3>
      
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

      <div style={layerItemStyle}>
        <label style={labelStyle}>
          <input
            type="checkbox"
            checked={layerVisibility.connections}
            onChange={(e) => onVisibilityChange('connections', e.target.checked)}
            style={checkboxStyle}
          />
          Connections
          <div style={layerColorStyle('rgba(255, 69, 0, 0.5)')} />
        </label>
        <span style={countStyle}>{connectionCount.toLocaleString()}</span>
      </div>

      <div style={{
        marginTop: '15px',
        paddingTop: '10px',
        borderTop: '1px solid #eee',
        fontSize: '12px',
        color: '#666'
      }}>
        <p style={{ margin: '5px 0' }}>
          <strong>🌳 Click on trees</strong> to view street-level perspective
        </p>
        <p style={{ margin: '5px 0' }}>
          Satellite imagery © Esri
        </p>
      </div>
    </div>
  );
};
