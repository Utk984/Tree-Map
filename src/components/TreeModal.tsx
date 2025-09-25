import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TreeViewResponse } from '../types';
import { getApiUrl } from '../config';

interface TreeModalProps {
  csvIndex: number;
  panoId: string;
  treeLat: number;
  treeLng: number;
  onClose: () => void;
}

export const TreeModal: React.FC<TreeModalProps> = ({
  csvIndex,
  onClose
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
          { timeout: 30000 } // 30 second timeout
        );
        
        if (response.data.success) {
          setData(response.data);
        } else {
          setError(response.data.error || 'Unknown error occurred');
        }
      } catch (err) {
        console.error('Error fetching tree view:', err);
        if (axios.isAxiosError(err)) {
          if (err.code === 'ECONNABORTED') {
            setError('Request timed out. Please try again.');
          } else if (err.response) {
            setError(`Server error: ${err.response.status} - ${err.response.statusText}`);
          } else if (err.request) {
            setError('Unable to connect to server. Please make sure the API server is running.');
          } else {
            setError(`Request error: ${err.message}`);
          }
        } else {
          setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchTreeView();
  }, [csvIndex]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

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
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px'
      }}
      onClick={handleBackdropClick}
    >
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '10px',
          padding: '20px',
          maxWidth: '800px',
          width: '100%',
          maxHeight: '90vh',
          overflow: 'auto',
          position: 'relative',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '15px',
            right: '20px',
            background: 'none',
            border: 'none',
            fontSize: '24px',
            cursor: 'pointer',
            color: '#aaa',
            zIndex: 1001
          }}
        >
          ×
        </button>

        {/* Modal header */}
        <h2 style={{ marginTop: 0, marginBottom: '20px', color: '#333' }}>
          Tree View - Index {csvIndex}
        </h2>

        {/* Content */}
        <div style={{ textAlign: 'center' }}>
          {loading && (
            <div>
              <p>Loading tree view...</p>
              <div style={{ 
                display: 'inline-block',
                width: '40px',
                height: '40px',
                border: '4px solid #f3f3f3',
                borderTop: '4px solid #3498db',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              <style>{`
                @keyframes spin {
                  0% { transform: rotate(0deg); }
                  100% { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          )}

          {error && (
            <div>
              <p style={{ color: '#d32f2f', margin: '20px 0' }}>
                <strong>Error:</strong> {error}
              </p>
              <div style={{ 
                backgroundColor: '#f5f5f5', 
                padding: '15px', 
                borderRadius: '5px',
                textAlign: 'left',
                marginTop: '20px'
              }}>
                <h4>Troubleshooting:</h4>
                <ul>
                  <li>Make sure the Flask API server is running on port 5001</li>
                  <li>Run: <code>python api_server.py</code></li>
                  <li>Check that the CSV data files are in the correct location</li>
                </ul>
              </div>
            </div>
          )}

          {data && !loading && (
            <div>
              {/* Tree view image */}
              <img
                src={`data:image/jpeg;base64,${data.image_base64}`}
                alt={`Tree view for ${data.pano_id}`}
                style={{
                  maxWidth: '100%',
                  height: 'auto',
                  borderRadius: '8px',
                  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)'
                }}
              />

              {/* Metadata */}
              <div style={{
                marginTop: '20px',
                textAlign: 'left',
                backgroundColor: '#f8f9fa',
                padding: '15px',
                borderRadius: '8px'
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div>
                    <strong>Panorama ID:</strong><br />
                    <code style={{ fontSize: '12px', color: '#666' }}>{data.pano_id}</code>
                  </div>
                  
                  <div>
                    <strong>Tree Location:</strong><br />
                    <span>{data.tree_lat.toFixed(6)}, {data.tree_lng.toFixed(6)}</span>
                  </div>
                  
                  <div>
                    <strong>Image Coordinates:</strong><br />
                    <span>({data.image_x.toFixed(1)}, {data.image_y.toFixed(1)})</span>
                  </div>
                  
                  <div>
                    <strong>Confidence:</strong><br />
                    <span style={{ 
                      color: data.confidence > 0.7 ? '#4caf50' : data.confidence > 0.5 ? '#ff9800' : '#f44336'
                    }}>
                      {data.confidence.toFixed(3)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Additional info */}
              <div style={{
                marginTop: '15px',
                padding: '10px',
                backgroundColor: '#e3f2fd',
                borderRadius: '5px',
                fontSize: '14px',
                color: '#1976d2'
              }}>
                <strong>Note:</strong> This view is centered on the detected tree location 
                and shows the perspective from the street view panorama.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
