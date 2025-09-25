// Core data types
export interface TreeData {
  tree_lat: number;
  tree_lng: number;
  pano_id: string;
  csv_index: number;
  image_x?: number;
  image_y?: number;
  conf?: number;
  distance_pano?: number;
  stview_lat?: number;
  stview_lng?: number;
  theta?: number;
  image_path?: string;
}

export interface StreetViewData {
  lat: number;
  lng: number;
  pano_id: string;
}


// UI state types
export interface ClickedTreeInfo {
  csv_index: number;
  pano_id: string;
  tree_lat: number;
  tree_lng: number;
}

export interface LayerVisibility {
  trees: boolean;
  streetViews: boolean;
}

export type BaseMapType = 'satellite' | 'streets' | 'minimal';

// API response types
export interface TreeViewResponse {
  success: boolean;
  csv_index: number;
  pano_id: string;
  tree_lat: number;
  tree_lng: number;
  image_x: number;
  image_y: number;
  confidence: number;
  image_base64: string;
  error?: string;
}
