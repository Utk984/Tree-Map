#!/usr/bin/env python3
"""
Mask Processing Module

This module handles all mask-related operations including RLE decoding,
mask application to panoramas, and coordinate transformations.
"""

import cv2
import numpy as np
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import pycocotools.mask as maskUtils
from utils import map_perspective_point_to_original

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MaskProcessor:
    """Handles all mask processing operations."""
    
    def __init__(self):
        """Initialize the mask processor."""
        pass
    
    def decode_rle_mask(self, rle_data: Dict, shape: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        Decode RLE (Run Length Encoding) mask data to binary mask.
        
        Args:
            rle_data: RLE encoded mask data
            shape: (height, width) of the mask
            
        Returns:
            Binary mask as numpy array or None if failed
        """
        try:
            # Use pycocotools to decode RLE mask
            rle = rle_data.copy()
            if isinstance(rle['counts'], str):
                rle['counts'] = rle['counts'].encode('utf-8')
            
            # Decode RLE to binary mask
            binary_mask = maskUtils.decode(rle)
            return binary_mask
            
        except Exception as e:
            logger.error(f"Error decoding RLE mask: {e}")
            return None
    
    def deserialize_mask(self, mask_data_obj: Dict) -> Optional[Dict]:
        """
        Deserialize mask data from JSON.
        
        Args:
            mask_data_obj: Mask data object from JSON
            
        Returns:
            Dictionary with polygon coordinates or None if failed
        """
        try:
            if mask_data_obj.get("encoding") == "rle" and mask_data_obj.get("rle"):
                # Use the existing decode_rle_mask method
                binary_mask = self.decode_rle_mask(mask_data_obj["rle"], mask_data_obj.get("orig_shape", (720, 1024)))
                
                if binary_mask is not None:
                    # Find contours to get polygon coordinates
                    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if contours:
                        # Get the largest contour
                        largest_contour = max(contours, key=cv2.contourArea)
                        polygon = largest_contour.squeeze().astype(np.float32)
                        if polygon.ndim == 2 and polygon.shape[0] > 2:
                            return {"xy": [polygon]}
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ Error deserializing mask: {str(e)}")
            return None
    
    def plot_single_mask_on_panorama(self, mask_info: Dict, panorama_image: np.ndarray, 
                                   theta: float, panorama_width: int, panorama_height: int,
                                   highlight: bool = False) -> np.ndarray:
        """
        Plot a single mask on panorama image.
        
        Args:
            mask_info: Mask information from JSON
            panorama_image: Panorama image array
            theta: Theta angle for coordinate mapping
            panorama_width, panorama_height: Panorama dimensions
            highlight: Whether to highlight this mask (for clicked trees)
            
        Returns:
            Panorama with mask overlay
        """
        try:
            # Create a copy of the panorama for mask overlay
            panorama_with_mask = panorama_image.copy()
            img_shape = (panorama_width, panorama_height)
            
            # Deserialize mask
            mask_data_obj = mask_info["mask_data"]
            deserialized_mask = self.deserialize_mask(mask_data_obj)
            
            if deserialized_mask and deserialized_mask.get("xy"):
                mask_points = deserialized_mask["xy"][0]
                
                # Convert perspective coordinates to panorama coordinates
                panorama_points = []
                for point in mask_points:
                    panorama_point = map_perspective_point_to_original(
                        point[0], point[1], theta, img_shape, 
                        720, 1024, 90  # height, width, FOV
                    )
                    panorama_point = tuple(map(int, panorama_point))
                    panorama_points.append(panorama_point)
                
                # Draw mask on panorama
                if len(panorama_points) > 2:
                    points_array = np.array(panorama_points, np.int32)
                    
                    if highlight:
                        # Draw filled polygon with very light overlay
                        overlay = panorama_with_mask.copy()
                        cv2.fillPoly(overlay, [points_array], (0, 255, 0))
                        cv2.addWeighted(overlay, 0.05, panorama_with_mask, 0.95, 0, panorama_with_mask)
                        
                        # Draw outline
                        cv2.polylines(panorama_with_mask, [points_array], 
                                    isClosed=True, color=(0, 255, 0), thickness=3)
                        
                        # Draw bounding box in bright red
                        x_coords = [p[0] for p in panorama_points]
                        y_coords = [p[1] for p in panorama_points]
                        x1, x2 = min(x_coords), max(x_coords)
                        y1, y2 = min(y_coords), max(y_coords)
                        cv2.rectangle(panorama_with_mask, (x1, y1), (x2, y2), (0, 0, 255), 4)
                        
                        # Draw center point in bright red
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        cv2.circle(panorama_with_mask, (center_x, center_y), 12, (0, 0, 255), -1)
                        cv2.circle(panorama_with_mask, (center_x, center_y), 16, (255, 255, 255), 3)
                    else:
                        # Draw filled polygon with very light overlay for other trees
                        overlay = panorama_with_mask.copy()
                        cv2.fillPoly(overlay, [points_array], (0, 255, 0))
                        cv2.addWeighted(overlay, 0.05, panorama_with_mask, 0.95, 0, panorama_with_mask)
                        
                        # Draw outline
                        cv2.polylines(panorama_with_mask, [points_array], 
                                    isClosed=True, color=(0, 255, 0), thickness=2)
            
            return panorama_with_mask
            
        except Exception as e:
            logger.error(f"❌ Error plotting mask: {str(e)}")
            return panorama_image
    
    def apply_masks_to_panorama(self, panorama_image: Image.Image, mask_data: Dict, 
                               csv_data, clicked_image_path: Optional[str] = None) -> Image.Image:
        """
        Apply mask overlays to panorama image using proper coordinate transformation.
        
        Args:
            panorama_image: PIL Image of the panorama
            mask_data: Mask data from JSON file
            csv_data: CSV data for validation
            clicked_image_path: Path of the clicked tree to highlight with bounding box
            
        Returns:
            PIL Image with masks applied
        """
        try:
            # Convert PIL to numpy array for processing
            panorama_array = np.array(panorama_image)
            panorama_with_masks = panorama_array.copy()
            
            # Get panorama dimensions
            panorama_height, panorama_width = panorama_array.shape[:2]
            img_shape = (panorama_width, panorama_height)
            
            # Create lookup for CSV entries
            csv_lookup = {}
            for _, row in csv_data.iterrows():
                key = f"{row['pano_id']}_{row['image_path']}"
                csv_lookup[key] = row
            
            masks_applied = 0
            
            # Process all views in the mask data
            for view_key, trees in mask_data['views'].items():
                for tree in trees:
                    # Check if this mask has a corresponding CSV entry
                    csv_key = f"{mask_data['pano_id']}_{tree['image_path']}"
                    if csv_key not in csv_lookup:
                        logger.debug(f"Skipping mask {tree['tree_index']} - no CSV entry found")
                        continue
                    
                    csv_entry = csv_lookup[csv_key]
                    theta = csv_entry.get('theta', 0)  # Get theta from CSV
                    
                    # Check if this is the clicked tree
                    is_clicked_tree = (clicked_image_path and tree['image_path'] == clicked_image_path)
                    
                    # Apply the mask
                    panorama_with_masks = self.plot_single_mask_on_panorama(
                        tree, panorama_with_masks, theta, panorama_width, panorama_height, 
                        highlight=is_clicked_tree
                    )
                    
                    masks_applied += 1
            
            logger.info(f"Applied {masks_applied} masks to panorama")
            return Image.fromarray(panorama_with_masks)
            
        except Exception as e:
            logger.error(f"Error applying masks: {e}")
            return panorama_image
    
    def load_mask_data(self, pano_id: str) -> Optional[Dict]:
        """
        Load mask data for a given panorama ID.
        
        Args:
            pano_id: Panorama ID
            
        Returns:
            Mask data dictionary or None if not found
        """
        try:
            mask_file_path = Path("masks") / f"{pano_id}_masks.json"
            if mask_file_path.exists():
                with open(mask_file_path, 'r') as f:
                    mask_data = json.load(f)
                return mask_data
            return None
        except Exception as e:
            logger.error(f"Error loading mask data for {pano_id}: {e}")
            return None
