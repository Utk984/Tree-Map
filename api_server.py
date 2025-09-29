#!/usr/bin/env python3
"""
Flask API Server for Tree View Generation

This server provides an API endpoint to generate tree-centered views on demand
using the CSV index to fetch the corresponding row and generate the view.
"""

import os
import warnings
import time
from concurrent.futures import ThreadPoolExecutor

# Suppress multiprocessing resource tracker warnings (common on macOS)
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning:multiprocessing.resource_tracker'
warnings.filterwarnings('ignore', category=UserWarning, module='multiprocessing.resource_tracker')

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import pandas as pd
import aiohttp
from pathlib import Path
import logging
import io
import base64
import json
from panorama_fetcher import PanoramaFetcher
from mask_processor import MaskProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes to allow requests from GitHub Pages
CORS(app)

# Global variables to store data
csv_data = None
panorama_fetcher = None
mask_processor = None

# Thread pool for parallel processing
THREAD_POOL = ThreadPoolExecutor(max_workers=4)

def load_csv_data():
    """Load the CSV data once at startup."""
    global csv_data
    csv_path = "public/south_delhi_trees.csv"
    logger.info(f"Loading CSV data from {csv_path}")
    csv_data = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(csv_data)} rows from CSV")
    return csv_data

def initialize_processors():
    """Initialize the panorama fetcher and mask processor."""
    global panorama_fetcher, mask_processor
    panorama_fetcher = PanoramaFetcher(max_concurrent=4)
    mask_processor = MaskProcessor()
    logger.info("Initialized PanoramaFetcher and MaskProcessor")
    return panorama_fetcher, mask_processor


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "csv_rows": len(csv_data) if csv_data is not None else 0})

@app.route('/api/tree-info/<int:csv_index>', methods=['GET'])
def get_tree_info(csv_index):
    """
    Get tree information without generating the view.
    
    Args:
        csv_index: Index of the row in the CSV file
        
    Returns:
        JSON response with tree information
    """
    try:
        # Validate index
        if csv_data is None:
            return jsonify({"error": "CSV data not loaded"}), 500
        
        if csv_index < 0 or csv_index >= len(csv_data):
            return jsonify({"error": f"Invalid CSV index: {csv_index}"}), 400
        
        # Get the row from CSV
        row = csv_data.iloc[csv_index]
        
        # Return tree information
        response = {
            "success": True,
            "csv_index": csv_index,
            "pano_id": row['pano_id'],
            "tree_lat": float(row['tree_lat']),
            "tree_lng": float(row['tree_lng']),
            "stview_lat": float(row['stview_lat']),
            "stview_lng": float(row['stview_lng']),
            "image_x": float(row['image_x']),
            "image_y": float(row['image_y']),
            "theta": float(row['theta']),
            "confidence": float(row['conf']),
            "distance": float(row['distance_pano']) if 'distance_pano' in row else None
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting tree info for index {csv_index}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tree-data', methods=['GET'])
def get_tree_data():
    """Get preprocessed tree data for the map (optimized for large datasets)."""
    try:
        if csv_data is None:
            return jsonify({"error": "CSV data not loaded"}), 500
        
        # Filter and convert data efficiently using pandas
        filtered_data = csv_data[
            (csv_data['distance_pano'] < 12) & 
            (csv_data['distance_pano'].notna()) &
            (csv_data['tree_lat'].notna()) &
            (csv_data['tree_lng'].notna()) &
            (csv_data['pano_id'].notna())
        ].copy()
        
        # Convert to optimized format
        result = []
        for idx, (_, row) in enumerate(filtered_data.iterrows()):
            result.append({
                "tree_lat": float(row['tree_lat']),
                "tree_lng": float(row['tree_lng']),
                "pano_id": str(row['pano_id']),
                "csv_index": int(row.name),  # Original CSV index
                "image_x": float(row['image_x']) if pd.notna(row['image_x']) else None,
                "image_y": float(row['image_y']) if pd.notna(row['image_y']) else None,
                "conf": float(row['conf']) if pd.notna(row['conf']) else None,
                "distance_pano": float(row['distance_pano']) if pd.notna(row['distance_pano']) else None,
                "stview_lat": float(row['stview_lat']) if pd.notna(row['stview_lat']) else None,
                "stview_lng": float(row['stview_lng']) if pd.notna(row['stview_lng']) else None,
                "theta": float(row['theta']) if pd.notna(row['theta']) else None,
                "image_path": str(row['image_path']) if pd.notna(row['image_path']) else None
            })
        
        logger.info(f"📊 Returning {len(result)} tree records (filtered from {len(csv_data)} total)")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting tree data: {str(e)}")
        return jsonify({"error": "Failed to get tree data"}), 500

@app.route('/api/streetview-data', methods=['GET'])
def get_streetview_data():
    """Get preprocessed street view data for the map."""
    try:
        # Load street view data
        sv_path = "public/south_delhi_panoramas.csv"
        sv_data = pd.read_csv(sv_path)
        
        # Filter and convert data efficiently
        filtered_data = sv_data[
            (sv_data['lat'].notna()) &
            (sv_data['lng'].notna()) &
            (sv_data['pano_id'].notna())
        ].copy()
        
        result = []
        for _, row in filtered_data.iterrows():
            result.append({
                "lat": float(row['lat']),
                "lng": float(row['lng']),
                "pano_id": str(row['pano_id'])
            })
        
        logger.info(f"📍 Returning {len(result)} street view records")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting street view data: {str(e)}")
        return jsonify({"error": "Failed to get street view data"}), 500

@app.route('/api/panorama/<pano_id>', methods=['GET'])
def get_panorama(pano_id):
    """
    Fetch the panorama image with masks applied for the given pano_id.
    
    Args:
        pano_id: Panorama ID to fetch
        
    Returns:
        Image file (JPEG) with masks applied or error message
    """
    try:
        if panorama_fetcher is None or mask_processor is None or csv_data is None:
            return jsonify({"error": "Processors or CSV data not initialized"}), 500
        
        # Get the clicked tree info from query parameters
        clicked_image_path = request.args.get('image_path')
        
        logger.info(f"🖼️ Fetching panorama with masks for pano_id: {pano_id}")
        if clicked_image_path:
            logger.info(f"🎯 Highlighting clicked tree: {clicked_image_path}")
        
        # Fetch the panorama using the fetcher
        panorama_image = panorama_fetcher.fetch_panorama_sync(pano_id)
        
        if panorama_image is None:
            return jsonify({"error": "Failed to fetch panorama"}), 500
        
        # Load and apply mask data
        mask_data = mask_processor.load_mask_data(pano_id)
        if mask_data:
            logger.info(f"🎭 Applying mask data for {pano_id}")
            panorama_image = mask_processor.apply_masks_to_panorama(
                panorama_image, mask_data, csv_data, clicked_image_path
            )
        else:
            logger.info(f"⚠️ No mask data found for {pano_id}")
        
        # Save the final image
        image_buffer = io.BytesIO()
        panorama_image.save(image_buffer, format='JPEG', quality=95)
        image_bytes = image_buffer.getvalue()
        
        # Return the image
        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=False
        )
        
    except Exception as e:
        logger.error(f"Error fetching panorama: {str(e)}")
        return jsonify({"error": "Failed to fetch panorama"}), 500

@app.route('/api/mask-data/<pano_id>', methods=['GET'])
def get_mask_data(pano_id):
    """
    Fetch mask data for the given pano_id.
    
    Args:
        pano_id: Panorama ID to fetch mask data for
        
    Returns:
        JSON with mask data or 404 if not found
    """
    try:
        logger.info(f"🎭 Fetching mask data for pano_id: {pano_id}")
        
        # Construct the mask file path
        mask_file_path = Path("masks") / f"{pano_id}_masks.json"
        
        if not mask_file_path.exists():
            logger.warning(f"⚠️ Mask file not found: {mask_file_path}")
            return jsonify({"error": "Mask data not found"}), 404
        
        # Read and return the mask data
        with open(mask_file_path, 'r') as f:
            mask_data = json.load(f)
        
        logger.info(f"✅ Successfully loaded mask data for {pano_id}")
        return jsonify(mask_data)
        
    except Exception as e:
        logger.error(f"Error fetching mask data: {str(e)}")
        return jsonify({"error": "Failed to fetch mask data"}), 500

if __name__ == '__main__':
    # Initialize data and processors
    load_csv_data()
    initialize_processors()
    
    # Create output directory for API-generated views
    Path("data/api_views").mkdir(parents=True, exist_ok=True)
    
    # Run the Flask server
    print("\n" + "="*60)
    print("🌳 TREE VIEW API SERVER")
    print("="*60)
    print(f"✅ Loaded {len(csv_data)} tree records")
    print(f"🚀 Starting server on http://localhost:5001")
    print("="*60)
    print("\nAPI Endpoints:")
    print("  GET /api/tree-info/<csv_index> - Get tree information")
    print("  GET /health - Health check")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
