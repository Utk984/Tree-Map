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
import asyncio
import aiohttp
from pathlib import Path
import logging
import io
import base64
import cv2
import numpy as np
import signal
import atexit

# Import the PanoramaProcessor from fetch.py
from fetch import PanoramaProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes to allow requests from GitHub Pages
CORS(app)

# Global variables to store data
csv_data = None
processor = None

# Thread pool for parallel processing
THREAD_POOL = ThreadPoolExecutor(max_workers=4)

def load_csv_data():
    """Load the CSV data once at startup."""
    global csv_data
    csv_path = "public/south_delhi_trees_cleaned.csv"
    logger.info(f"Loading CSV data from {csv_path}")
    csv_data = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(csv_data)} rows from CSV")
    return csv_data

def initialize_processor():
    """Initialize the PanoramaProcessor."""
    global processor
    processor = PanoramaProcessor(max_concurrent=4)
    logger.info("Initialized PanoramaProcessor")
    return processor


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "csv_rows": len(csv_data) if csv_data is not None else 0})

@app.route('/api/tree-view/<int:csv_index>', methods=['GET'])
async def get_tree_view(csv_index):
    """
    Generate a tree-centered view for a specific CSV index with caching and optimizations.
    
    Args:
        csv_index: Index of the row in the CSV file
        
    Returns:
        JSON response with base64 encoded image or error message
    """
    start_time = time.time()
    
    try:
        # Validate index
        if csv_data is None:
            return jsonify({"error": "CSV data not loaded"}), 500
        
        if csv_index < 0 or csv_index >= len(csv_data):
            return jsonify({"error": f"Invalid CSV index: {csv_index}"}), 400
        
        # Get the row from CSV
        row = csv_data.iloc[csv_index]
        pano_id = row['pano_id']
        
        logger.info(f"⚡ Fast generating view for CSV index {csv_index}, pano_id: {pano_id}")
        
        # Fetch panorama and generate view with masks
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Use method with masks (generate_centered_view_for_row)
            result = await processor.generate_centered_view_for_row(row, session)
        
        if result is None:
            return jsonify({"error": "Failed to generate view"}), 500
        
        # Get the image data from result (now includes masks)
        image_data = result.get('image_data')
        if image_data is None:
            return jsonify({"error": "No image data generated"}), 500
        
        # Encode the image data as base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Generated view with masks in {processing_time:.2f}s")
        
        # Return the response with image and metadata
        response = {
            "success": True,
            "csv_index": csv_index,
            "pano_id": result.get('pano_id', pano_id),
            "tree_lat": float(result.get('tree_lat', row['tree_lat'])),
            "tree_lng": float(result.get('tree_lng', row['tree_lng'])),
            "image_x": float(result.get('image_x', row['image_x'])),
            "image_y": float(result.get('image_y', row['image_y'])),
            "confidence": float(result.get('conf', row['conf'])),
            "image_base64": image_base64,
            "processing_time": round(processing_time, 2)
        }
        
        return jsonify(response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Error generating tree view for index {csv_index} after {processing_time:.2f}s: {str(e)}")
        return jsonify({"error": str(e)}), 500

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

def run_async(coro):
    """Helper function to run async functions in Flask."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Override the route handler to support async
original_get_tree_view = get_tree_view
def get_tree_view_sync(csv_index):
    return run_async(original_get_tree_view(csv_index))
app.view_functions['get_tree_view'] = get_tree_view_sync

def cleanup_resources():
    """Clean up resources on server shutdown."""
    global processor
    try:
        logger.info("🧹 Cleaning up resources...")
        if processor:
            # Clean up any async resources
            if hasattr(processor, 'cleanup'):
                processor.cleanup()
            processor = None
        
        # Clean up any remaining async tasks
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
        except RuntimeError:
            # No event loop running, that's fine
            pass
            
        logger.info("✅ Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")

@app.route('/api/panorama/<pano_id>', methods=['GET'])
def get_panorama(pano_id):
    """
    Fetch the original panorama image for the given pano_id.
    
    Args:
        pano_id: Panorama ID to fetch
        
    Returns:
        Image file (JPEG) or error message
    """
    try:
        if processor is None:
            return jsonify({"error": "Processor not initialized"}), 500
        
        logger.info(f"🖼️ Fetching panorama for pano_id: {pano_id}")
        
        # Fetch the panorama using the processor (synchronous version)
        panorama_data = processor.fetch_panorama_sync(pano_id)
        
        if panorama_data is None:
            return jsonify({"error": "Failed to fetch panorama"}), 500
        
        # Handle PIL Image directly without any processing/conversion
        if hasattr(panorama_data, 'save'):  # It's a PIL Image
            image_buffer = io.BytesIO()
            panorama_data.save(image_buffer, format='JPEG', quality=95)
            image_bytes = image_buffer.getvalue()
        else:  # It's a numpy array (fallback)
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            _, buffer = cv2.imencode('.jpg', panorama_data, encode_params)
            image_bytes = buffer.tobytes()
        
        # Return the image
        return send_file(
            io.BytesIO(image_bytes),
            mimetype='image/jpeg',
            as_attachment=False
        )
        
    except Exception as e:
        logger.error(f"Error fetching panorama: {str(e)}")
        return jsonify({"error": "Failed to fetch panorama"}), 500

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("🛑 Received shutdown signal, cleaning up...")
    cleanup_resources()
    exit(0)

if __name__ == '__main__':
    # Register cleanup handlers
    atexit.register(cleanup_resources)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize data and processor
    load_csv_data()
    initialize_processor()
    
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
    print("  GET /api/tree-view/<csv_index> - Generate and return tree view")
    print("  GET /api/tree-info/<csv_index> - Get tree information")
    print("  GET /health - Health check")
    print("="*60 + "\n")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5001, threaded=True)
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user")
    finally:
        cleanup_resources()
