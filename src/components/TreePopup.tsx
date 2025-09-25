import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TreeViewResponse } from '../types';
import { getApiUrl } from '../config';

interface TreePopupProps {
  csvIndex: number;
  panoId: string;
  treeLat: number;
  treeLng: number;
  onClose: () => void;
  position: { x: number; y: number };
}

export const TreePopup: React.FC<TreePopupProps> = ({
  csvIndex,
  onClose,
  position
}) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<TreeViewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTreeView = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log(`Fetching tree view for CSV index: ${csvIndex}`);
        
        const apiUrl = getApiUrl();
        const response = await axios.get<TreeViewResponse>(
          `${apiUrl}/api/tree-view/${csvIndex}`,
          { timeout: 30000 }
        );
        
        if (response.data.success) {
          setData(response.data);
        } else {
          setError(response.data.error || 'Unknown error occurred');
        }
      } catch (err) {
        console.error('Error fetching tree view:', err);
        setError('Failed to load tree view');
      } finally {
        setLoading(false);
      }
    };

    fetchTreeView();
  }, [csvIndex]);

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <div
      style={{
        position: 'fixed',
        left: `${position.x + 10}px`,
        top: `${position.y + 10}px`,
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '12px',
        maxWidth: '300px',
        width: '280px',
        maxHeight: '400px',
        overflow: 'auto',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
        border: '1px solid #ddd',
        zIndex: 1000,
        fontSize: '12px'
      }}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '8px',
          right: '8px',
          background: 'none',
          border: 'none',
          fontSize: '16px',
          cursor: 'pointer',
          color: '#aaa',
          padding: '0',
          width: '20px',
          height: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        ×
      </button>

      {/* Header */}
      <div style={{ marginBottom: '8px', fontWeight: 'bold', color: '#333' }}>
        Tree View - Index {csvIndex}
      </div>

      {/* Content */}
      {loading && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <div style={{ 
            display: 'inline-block',
            width: '20px',
            height: '20px',
            border: '2px solid #f3f3f3',
            borderTop: '2px solid #3498db',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <div style={{ marginTop: '8px', fontSize: '11px' }}>Loading...</div>
        </div>
      )}

      {error && (
        <div style={{ color: '#d32f2f', fontSize: '11px', padding: '8px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {data && !loading && (
        <div>
          {/* Tree view image */}
          <img
            src={`data:image/jpeg;base64,${data.image_base64}`}
            alt={`Tree view for ${data.pano_id}`}
            style={{
              width: '100%',
              height: 'auto',
              borderRadius: '4px',
              marginBottom: '8px'
            }}
          />

          {/* Metadata */}
          <div style={{
            fontSize: '10px',
            lineHeight: '1.3'
          }}>
            <div><strong>Panorama ID:</strong> {data.pano_id}</div>
            <div><strong>Location:</strong> {data.tree_lat.toFixed(4)}, {data.tree_lng.toFixed(4)}</div>
            <div><strong>Image:</strong> ({data.image_x.toFixed(0)}, {data.image_y.toFixed(0)})</div>
            <div style={{ 
              color: data.confidence > 0.7 ? '#4caf50' : data.confidence > 0.5 ? '#ff9800' : '#f44336'
            }}>
              <strong>Confidence:</strong> {data.confidence.toFixed(3)}
            </div>
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
