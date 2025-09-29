import { TreeData, StreetViewData, PanoramaMaskData } from '../types';
import { getApiUrl } from '../config';

// Load tree data from API (server-side preprocessing for performance)
export const loadTreeData = async (): Promise<TreeData[]> => {
  try {
    console.log('🌳 Loading tree data from API...');
    const startTime = Date.now();
    
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/api/tree-data`);
    console.log('📡 API response status:', response.status, response.statusText);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch tree data: ${response.statusText}`);
    }
    
    const trees: TreeData[] = await response.json();
    const loadTime = Date.now() - startTime;
    
    console.log(`✅ Loaded ${trees.length} tree records in ${loadTime}ms`);
    return trees;
    
  } catch (error) {
    console.error('Error loading tree data:', error);
    throw new Error(`Failed to load tree data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Load street view data from API (server-side preprocessing for performance)
export const loadStreetViewData = async (): Promise<StreetViewData[]> => {
  try {
    console.log('📍 Loading street view data from API...');
    const startTime = Date.now();
    
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/api/streetview-data`);
    if (!response.ok) {
      throw new Error(`Failed to fetch street view data: ${response.statusText}`);
    }
    
    const streetViews: StreetViewData[] = await response.json();
    const loadTime = Date.now() - startTime;
    
    console.log(`✅ Loaded ${streetViews.length} street view records in ${loadTime}ms`);
    return streetViews;
    
  } catch (error) {
    console.error('Error loading street view data:', error);
    throw new Error(`Failed to load street view data: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

// Load mask data for a specific panorama
export const loadPanoramaMaskData = async (panoId: string): Promise<PanoramaMaskData | null> => {
  try {
    console.log('🎭 Loading mask data for panorama:', panoId);
    const startTime = Date.now();
    
    const apiUrl = getApiUrl();
    const response = await fetch(`${apiUrl}/api/mask-data/${panoId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        console.log('⚠️ No mask data found for panorama:', panoId);
        return null;
      }
      throw new Error(`Failed to fetch mask data: ${response.statusText}`);
    }
    
    const maskData: PanoramaMaskData = await response.json();
    const loadTime = Date.now() - startTime;
    
    console.log(`✅ Loaded mask data for ${panoId} in ${loadTime}ms`);
    return maskData;
    
  } catch (error) {
    console.error('Error loading mask data:', error);
    return null; // Return null instead of throwing to allow panorama to load without masks
  }
};
