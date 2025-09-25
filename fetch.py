#!/usr/bin/env python3
"""
Tree-Centered View Generator

This script provides functions to process individual panoramas:
1. Generate centered view for a specific CSV row with masks
2. Generate full panorama with all masks from CSV data for a pano_id

Uses existing code from utils.py for panorama fetching and view generation.
"""

import asyncio
import pandas as pd
import numpy as np
import cv2
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
import aiohttp

try:
    import pycocotools.mask as maskUtils
    HAS_PYCOCOTOOLS = True
except ImportError:
    HAS_PYCOCOTOOLS = False
    print("⚠️ pycocotools not available, mask decoding will be limited")

from utils import map_perspective_point_to_original, fetch_pano_by_id, get_perspective

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PanoramaProcessor:
    """Process individual panoramas for tree-centered views and mask overlays."""
    
    def __init__(self, max_concurrent: int = 4):
        """
        Initialize the processor.
        
        Args:
            max_concurrent: Maximum number of concurrent panorama fetches
        """
        self.max_concurrent = max_concurrent
        
    def calculate_centered_theta(self, image_x: float, panorama_width: int) -> float:
        """
        Calculate the theta angle needed to center the view on the given image_x coordinate.
        
        Args:
            image_x: Target x coordinate in the panorama (0 to panorama_width)
            panorama_width: Width of the full panorama
            
        Returns:
            theta: Horizontal angle in degrees to center the view
        """
        # Convert image_x to normalized coordinate (0-1)
        norm_x = image_x / panorama_width
        
        # Convert to longitude in equirectangular projection (-π to π)
        lon = (norm_x - 0.5) * 2 * np.pi
        
        # Convert to theta angle (horizontal rotation in degrees)
        theta = np.degrees(lon)
        
        # Normalize to [-180, 180] range
        theta = ((theta + 180) % 360) - 180
        
        logger.debug(f"🎯 Centering view at x={image_x} -> θ={theta:.2f}°")
        return theta
    
    def create_centered_view(self, panorama_image: np.ndarray, image_x: float,
                            panorama_width: int, panorama_height: int, 
                            view_width: int, view_height: int, FOV: int) -> np.ndarray:
        """
        Create a perspective view centered on the given image_x coordinate.
        
        Args:
            panorama_image: Full panorama image array
            image_x: Target x coordinate to center on
            panorama_width, panorama_height: Panorama dimensions
            view_width, view_height: Desired view dimensions
            FOV: Field of view in degrees
            
        Returns:
            perspective_view: Generated perspective view
        """
        # Calculate theta angle to center the view on image_x
        theta = self.calculate_centered_theta(image_x, panorama_width)
        
        # Create perspective view using existing unwrap function
        perspective_view = get_perspective(
            panorama_image, FOV, theta, 0,  # PHI = 0 (no vertical tilt)
            view_height, view_width, panorama_height, panorama_width,
        )
        
        return perspective_view
    
    def deserialize_mask(self, mask_data_obj):
        """Deserialize mask data from JSON."""
        try:
            if mask_data_obj.get("encoding") == "rle" and mask_data_obj.get("rle"):
                # Handle RLE encoded masks
                rle = mask_data_obj["rle"]
                if isinstance(rle['counts'], str):
                    rle['counts'] = rle['counts'].encode('utf-8')
                
                # Decode RLE to binary mask
                binary_mask = maskUtils.decode(rle)
                
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

    def plot_mask_on_panorama(self, mask_info: Dict, panorama_image: np.ndarray, 
                             theta: float, panorama_width: int, panorama_height: int) -> np.ndarray:
        """
        Plot a single mask on panorama image.
        
        Args:
            mask_info: Mask information from JSON
            panorama_image: Panorama image array
            theta: Theta angle for coordinate mapping
            panorama_width, panorama_height: Panorama dimensions
            
        Returns:
            panorama_with_mask: Panorama with mask overlay
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
                    
                    # Draw filled polygon with transparency
                    overlay = panorama_with_mask.copy()
                    cv2.fillPoly(overlay, [points_array], (0, 255, 0))
                    cv2.addWeighted(overlay, 0.3, panorama_with_mask, 0.7, 0, panorama_with_mask)
                    
                    # Draw outline
                    cv2.polylines(panorama_with_mask, [points_array], 
                                isClosed=True, color=(0, 255, 0), thickness=2)
            
            return panorama_with_mask
            
        except Exception as e:
            logger.error(f"❌ Error plotting mask: {str(e)}")
            return panorama_image

    async def generate_centered_view_for_row(self, row: pd.Series, session: aiohttp.ClientSession,
                                           output_dir: str = "data/views") -> Optional[Dict[str, Any]]:
        """
        Generate a centered view for a specific CSV row.
        
        Args:
            row: Pandas Series representing a single CSV row
            session: aiohttp ClientSession for HTTP requests
            output_dir: Directory to save the output
            
        Returns:
            Dictionary with result information or None if failed
        """
        try:
            pano_id = row['pano_id']
            image_x = row['image_x']
            image_y = row['image_y']
            image_path = row['image_path']
            theta = row['theta']
            
            logger.info(f"🔄 Generating centered view for {pano_id} - {Path(image_path).name}")
            
            # Fetch panorama data
            pano, panorama_image = await fetch_pano_by_id(pano_id, session)
            
            if pano is None or panorama_image is None:
                logger.warning(f"⚠️ Failed to fetch panorama: {pano_id}")
                return None
            
            # Get panorama dimensions
            panorama_height, panorama_width = panorama_image.shape[:2]
            
            # Plot the specific mask for this row
            mask_json_path = Path("masks") / f"{pano_id}_masks.json"
            panorama_with_mask = panorama_image.copy()
            
            if mask_json_path.exists():
                with open(mask_json_path, 'r') as f:
                    mask_data = json.load(f)
                
                # Find the specific mask for this image_path
                target_mask = None
                for view_name, view_masks in mask_data.get("views", {}).items():
                    for mask_info in view_masks:
                        if mask_info["image_path"] == image_path:
                            target_mask = mask_info
                            break
                    if target_mask:
                        break
                
                if target_mask:
                    panorama_with_mask = self.plot_mask_on_panorama(
                        target_mask, panorama_with_mask, theta, panorama_width, panorama_height
                    )
                    
                    # Draw center point
                    center_x = int(image_x)
                    center_y = int(image_y)
                    cv2.circle(panorama_with_mask, (center_x, center_y), 15, (0, 0, 255), -1)
                    cv2.circle(panorama_with_mask, (center_x, center_y), 20, (255, 255, 255), 2)
            
            # Create centered view with fixed dimensions 1024x720
            centered_view = self.create_centered_view(
                panorama_with_mask, image_x,
                panorama_width, panorama_height,
                1024, 720, 90
            )
            
            # Convert BGR to RGB for encoding
            centered_view_rgb = cv2.cvtColor(centered_view, cv2.COLOR_BGR2RGB)

            # Encode image as JPEG bytes (no disk write, no extra deps)
            encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            success, enc = cv2.imencode('.jpg', centered_view_rgb, encode_params)
            if not success:
                logger.error("❌ Failed to JPEG-encode centered view in memory")
                return None
            image_data = enc.tobytes()
            
            result = {
                'pano_id': pano_id,
                'image_data': image_data,
                'original_image_path': image_path,
                'tree_lat': row['tree_lat'],
                'tree_lng': row['tree_lng'],
                'stview_lat': row['stview_lat'],
                'stview_lng': row['stview_lng'],
                'image_x': image_x,
                'image_y': image_y,
                'conf': row['conf']
            }
            
            logger.info(f"✅ Created centered view in memory for {pano_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating centered view for {row.get('image_path', 'unknown')}: {str(e)}")
            return None

    async def generate_full_panorama_with_csv_masks(self, pano_id: str, csv_data: pd.DataFrame,
                                                   session: aiohttp.ClientSession,
                                                   output_dir: str = "data/full") -> Optional[Dict[str, Any]]:
        """
        Generate full panorama with all masks from CSV data for a specific pano_id.
        
        Args:
            pano_id: Panorama ID to process
            csv_data: DataFrame containing CSV data
            session: aiohttp ClientSession for HTTP requests
            output_dir: Directory to save the output
            
        Returns:
            Dictionary with result information or None if failed
        """
        try:
            logger.info(f"🔄 Generating full panorama with CSV masks for {pano_id}")
            
            # Filter CSV data for this pano_id
            pano_rows = csv_data[csv_data['pano_id'] == pano_id]
            
            if pano_rows.empty:
                logger.warning(f"⚠️ No CSV data found for pano_id: {pano_id}")
                return None
            
            # Fetch panorama data
            pano, panorama_image = await fetch_pano_by_id(pano_id, session)
            
            if pano is None or panorama_image is None:
                logger.warning(f"⚠️ Failed to fetch panorama: {pano_id}")
                return None
            
            # Get panorama dimensions
            panorama_height, panorama_width = panorama_image.shape[:2]
            
            # Start with original panorama
            panorama_with_masks = panorama_image.copy()
            
            # Load mask data
            mask_json_path = Path("masks") / f"{pano_id}_masks.json"
            
            if mask_json_path.exists():
                with open(mask_json_path, 'r') as f:
                    mask_data = json.load(f)
                
                # Process each row for this pano_id
                plotted_masks = 0
                for _, row in pano_rows.iterrows():
                    image_path = row['image_path']
                    theta = row['theta']
                    
                    # Find the specific mask for this image_path
                    target_mask = None
                    for view_name, view_masks in mask_data.get("views", {}).items():
                        for mask_info in view_masks:
                            if mask_info["image_path"] == image_path:
                                target_mask = mask_info
                                break
                        if target_mask:
                            break
                    
                    if target_mask:
                        panorama_with_masks = self.plot_mask_on_panorama(
                            target_mask, panorama_with_masks, theta, panorama_width, panorama_height
                        )
                        
                        # Draw center point for this detection
                        center_x = int(row['image_x'])
                        center_y = int(row['image_y'])
                        cv2.circle(panorama_with_masks, (center_x, center_y), 15, (0, 0, 255), -1)
                        cv2.circle(panorama_with_masks, (center_x, center_y), 20, (255, 255, 255), 2)
                        
                        plotted_masks += 1
                        logger.debug(f"✅ Plotted mask for {Path(image_path).name}")
            
            # Save the full panorama with masks
            output_filename = f"{pano_id}_full_with_csv_masks.jpg"
            output_path = Path(output_dir) / output_filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert BGR to RGB for saving
            panorama_rgb = cv2.cvtColor(panorama_with_masks, cv2.COLOR_BGR2RGB)
            cv2.imwrite(str(output_path), panorama_rgb)
            
            result = {
                'pano_id': pano_id,
                'full_pano_path': str(output_path),
                'masks_plotted': plotted_masks,
                'total_csv_rows': len(pano_rows)
            }
            
            logger.info(f"✅ Created full panorama with {plotted_masks} masks: {output_filename}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating full panorama for {pano_id}: {str(e)}")
            return None
