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
  image_path?: string;
}

export interface LayerVisibility {
  trees: boolean;
  streetViews: boolean;
}

export type BaseMapType = 'satellite' | 'streets' | 'minimal';

// Mask data types
export interface MaskData {
  orig_shape: [number, number];
  encoding: string;
  rle: {
    size: [number, number];
    counts: string;
  };
  bbox: [number, number, number, number];
}

export interface TreeMask {
  tree_index: string;
  image_path: string;
  confidence: number;
  mask_data: MaskData;
}

export interface PanoramaMaskData {
  pano_id: string;
  views: {
    [viewKey: string]: TreeMask[];
  };
}