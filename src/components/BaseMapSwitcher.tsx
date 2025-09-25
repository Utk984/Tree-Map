import { FC } from 'react';

export type BaseMapType = 'satellite' | 'streets' | 'minimal';

interface BaseMapSwitcherProps {
  currentLayer: BaseMapType;
  onLayerChange: (layer: BaseMapType) => void;
}

export const BaseMapSwitcher: FC<BaseMapSwitcherProps> = ({
  currentLayer,
  onLayerChange
}) => {
  console.log('🗺️ BaseMapSwitcher render - current layer:', currentLayer);
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

  const controlStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: '20px',
    left: '20px',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0, 0, 0, 0.15)',
    overflow: 'hidden',
    zIndex: 100
  };

  const buttonStyle = (isActive: boolean): React.CSSProperties => ({
    display: 'block',
    width: '100%',
    padding: '10px 15px',
    border: 'none',
    backgroundColor: isActive ? '#2196f3' : 'transparent',
    color: isActive ? 'white' : '#333',
    cursor: 'pointer',
    fontSize: '14px',
    textAlign: 'left',
    transition: 'all 0.2s ease',
    borderBottom: '1px solid rgba(0, 0, 0, 0.1)'
  });

  const lastButtonStyle = (isActive: boolean): React.CSSProperties => ({
    ...buttonStyle(isActive),
    borderBottom: 'none'
  });

  return (
    <div style={controlStyle}>
      {mapStyles.map((style, index) => (
        <button
          key={style.id}
          style={index === mapStyles.length - 1 ? lastButtonStyle(currentLayer === style.id) : buttonStyle(currentLayer === style.id)}
          onClick={() => onLayerChange(style.id)}
          onMouseEnter={(e) => {
            if (currentLayer !== style.id) {
              (e.target as HTMLButtonElement).style.backgroundColor = '#f5f5f5';
            }
          }}
          onMouseLeave={(e) => {
            if (currentLayer !== style.id) {
              (e.target as HTMLButtonElement).style.backgroundColor = 'transparent';
            }
          }}
        >
          <div>
            <strong>{style.name}</strong>
          </div>
          <div style={{ fontSize: '12px', color: 'inherit', opacity: 0.7 }}>
            {style.description}
          </div>
        </button>
      ))}
    </div>
  );
};
