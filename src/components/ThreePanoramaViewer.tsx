import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { getApiUrl } from '../config';

interface ThreePanoramaViewerProps {
  panoId: string | null;
  treeLat?: number;
  treeLng?: number;
  clickedImagePath?: string;
}

export const ThreePanoramaViewer: React.FC<ThreePanoramaViewerProps> = ({ 
  panoId, 
  treeLat, 
  treeLng,
  clickedImagePath
}) => {
  const [panoramaImage, setPanoramaImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    sphere: THREE.Mesh;
    isMouseDown: boolean;
    mouseX: number;
    mouseY: number;
    lon: number;
    lat: number;
    phi: number;
    theta: number;
    animate: () => void;
    cleanup: () => void;
  } | null>(null);

  useEffect(() => {
    if (!panoId) {
      setPanoramaImage(null);
      setError(null);
      return;
    }

    const fetchPanorama = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch the panorama image with masks already applied
        const url = clickedImagePath 
          ? `${getApiUrl()}/api/panorama/${panoId}?image_path=${encodeURIComponent(clickedImagePath)}`
          : `${getApiUrl()}/api/panorama/${panoId}`;
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch panorama: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        setPanoramaImage(imageUrl);
        
      } catch (err) {
        console.error('Error fetching panorama:', err);
        setError(err instanceof Error ? err.message : 'Failed to load panorama');
      } finally {
        setLoading(false);
      }
    };

    fetchPanorama();
  }, [panoId, clickedImagePath]);

  // Initialize Three.js scene when panorama loads
  useEffect(() => {
    if (!panoramaImage || !mountRef.current) return;

    const mount = mountRef.current;
    
    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, mount.clientWidth / mount.clientHeight, 1, 1100);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    // Improve clarity and correct color space
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    // Create sphere geometry for panorama with high resolution
    const geometry = new THREE.SphereGeometry(500, 128, 64);
    // Flip the geometry inside out
    geometry.scale(-1, 1, 1);

    // Load texture with high quality settings
    const textureLoader = new THREE.TextureLoader();
    const texture = textureLoader.load(panoramaImage, () => {
      // Apply high quality sampling once the texture is loaded
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.generateMipmaps = true;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      texture.magFilter = THREE.LinearFilter;
      texture.anisotropy = renderer.capabilities.getMaxAnisotropy();
      texture.needsUpdate = true;
    });
    
    const material = new THREE.MeshBasicMaterial({ map: texture });
    
    const sphere = new THREE.Mesh(geometry, material);
    scene.add(sphere);

    // Camera controls
    let isMouseDown = false;
    let mouseX = 0;
    let mouseY = 0;
    let lon = 0;
    let lat = 0;
    let phi = 0;
    let theta = 0;

    const onMouseDown = (event: MouseEvent) => {
      event.preventDefault();
      isMouseDown = true;
      mouseX = event.clientX;
      mouseY = event.clientY;
    };

    const onMouseUp = () => {
      isMouseDown = false;
    };

    const onMouseMove = (event: MouseEvent) => {
      if (!isMouseDown) return;

      const deltaX = event.clientX - mouseX;
      const deltaY = event.clientY - mouseY;

      mouseX = event.clientX;
      mouseY = event.clientY;

      lon -= deltaX * 0.1;
      lat += deltaY * 0.1;
      lat = Math.max(-85, Math.min(85, lat));
    };

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const fov = camera.fov + event.deltaY * 0.05;
      camera.fov = THREE.MathUtils.clamp(fov, 10, 75);
      camera.updateProjectionMatrix();
    };

    const animate = () => {
      phi = THREE.MathUtils.degToRad(90 - lat);
      theta = THREE.MathUtils.degToRad(lon);

      const x = 500 * Math.sin(phi) * Math.cos(theta);
      const y = 500 * Math.cos(phi);
      const z = 500 * Math.sin(phi) * Math.sin(theta);

      camera.lookAt(x, y, z);
      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    };

    // Event listeners
    mount.addEventListener('mousedown', onMouseDown);
    mount.addEventListener('mousemove', onMouseMove);
    mount.addEventListener('mouseup', onMouseUp);
    mount.addEventListener('wheel', onWheel);
    mount.addEventListener('contextmenu', (e) => e.preventDefault());

    // Handle resize
    const handleResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    // Start animation
    animate();

    // Store references for cleanup
    sceneRef.current = {
      scene,
      camera,
      renderer,
      sphere,
      isMouseDown,
      mouseX,
      mouseY,
      lon,
      lat,
      phi,
      theta,
      animate,
      cleanup: () => {
        mount.removeEventListener('mousedown', onMouseDown);
        mount.removeEventListener('mousemove', onMouseMove);
        mount.removeEventListener('mouseup', onMouseUp);
        mount.removeEventListener('wheel', onWheel);
        window.removeEventListener('resize', handleResize);
        
        if (mount.contains(renderer.domElement)) {
          mount.removeChild(renderer.domElement);
        }
        
        geometry.dispose();
        material.dispose();
        texture.dispose();
        
        // Clean up any additional meshes (if any)
        scene.children.forEach(child => {
          if (child instanceof THREE.Mesh && child !== sphere) {
            child.geometry.dispose();
            if (child.material instanceof THREE.Material) {
              child.material.dispose();
            }
          }
        });
        
        renderer.dispose();
      }
    };

    // Cleanup on unmount
    return () => {
      if (sceneRef.current) {
        sceneRef.current.cleanup();
      }
    };
  }, [panoramaImage]);

  // Cleanup object URL when component unmounts or image changes
  useEffect(() => {
    return () => {
      if (panoramaImage) {
        URL.revokeObjectURL(panoramaImage);
      }
    };
  }, [panoramaImage]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f5f5f5',
      border: '1px solid #ddd',
      borderRadius: '8px',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {!panoId ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          textAlign: 'center',
          color: '#666',
          fontSize: '16px',
          padding: '20px'
        }}>
          <div>
            <h3>360° Panorama Viewer</h3>
            <p>Click on a tree to view its 360° panorama</p>
            <p style={{ fontSize: '12px', color: '#999' }}>
              🖱️ Drag to look around • 🔍 Scroll to zoom
            </p>
          </div>
        </div>
      ) : loading ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          textAlign: 'center',
          color: '#666',
          fontSize: '16px'
        }}>
          <div>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #3498db',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }} />
            <p>Loading 360° panorama...</p>
          </div>
        </div>
      ) : error ? (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          textAlign: 'center',
          color: '#d32f2f',
          fontSize: '16px',
          padding: '20px'
        }}>
          <div>
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        </div>
      ) : panoramaImage ? (
        <>
          {/* Header with panorama info */}
          <div style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            right: '10px',
            zIndex: 1000,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '12px',
            pointerEvents: 'none'
          }}>
            <div><strong>Panorama ID:</strong> {panoId}</div>
            {treeLat && treeLng && (
              <div><strong>Tree Location:</strong> {treeLat.toFixed(6)}, {treeLng.toFixed(6)}</div>
            )}
            <div style={{ fontSize: '10px', marginTop: '4px', opacity: 0.8 }}>
              🖱️ Drag to look around • 🔍 Scroll to zoom • 🎭 Red overlays show detected trees
            </div>
          </div>

          {/* Three.js container */}
          <div 
            ref={mountRef} 
            style={{ 
              width: '100%', 
              height: '100%',
              cursor: 'grab'
            }}
          />
        </>
      ) : null}
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
