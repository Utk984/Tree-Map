import logging
import numpy as np
import cv2
import asyncio
import time
from streetlevel import streetview
from aiohttp import ClientSession

logger = logging.getLogger(__name__)


def xyz2lonlat(xyz):
    """
    Convert 3D XYZ coordinates to longitude/latitude.

    Parameters:
    - xyz (np.ndarray): 3D coordinates.

    Returns:
    - lonlat (np.ndarray): Longitude/latitude coordinates.
    """
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    lon = np.arctan2(x, z)
    hyp = np.sqrt(x**2 + z**2)
    lat = np.arctan2(y, hyp)
    return np.stack([lon, lat], axis=-1)

def lonlat2XY(lonlat, width_src, height_src):
    """
    Convert longitude/latitude to XY coordinates on the equirectangular image.

    Parameters:
    - lonlat (np.ndarray): Longitude/latitude coordinates.
    - width_src (int): Source image width.
    - height_src (int): Source image height.

    Returns:
    - XY (np.ndarray): XY coordinates on the equirectangular image.
    """
    lon, lat = lonlat[..., 0], lonlat[..., 1]
    x = (lon / (2 * np.pi) + 0.5) * width_src
    # y = (0.5 - lat / np.pi) * height_src
    y = (lat / np.pi + 0.5) * height_src
    return np.stack([x, y], axis=-1)


def map_perspective_point_to_original(x, y, theta, img_shape, height, width, FOV):
    """
    Map perspective point to original equirectangular coordinates with logging.
    """
    logger.debug(f"🔄 Mapping point ({x}, {y}) at θ={theta}° to equirectangular coordinates")
    logger.debug(f"📏 Image shape: {img_shape}, View dimensions: {width}x{height}")
    
    try:
        PHI = 0
        width_src, height_src = img_shape

        # Calculate perspective camera parameters
        f = 0.5 * width * 1 / np.tan(0.5 * FOV / 180.0 * np.pi)
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0

        # Create camera matrix
        K = np.array(
            [
                [f, 0, cx],
                [0, f, cy],
                [0, 0, 1],
            ],
            np.float32,
        )

        # Convert perspective point to normalized coordinates
        point = np.array([x, y, 1.0], dtype=np.float32)
        normalized = np.linalg.inv(K) @ point

        # Calculate rotation matrices
        y_axis = np.array([0.0, 1.0, 0.0], np.float32)
        x_axis = np.array([1.0, 0.0, 0.0], np.float32)
        R1, _ = cv2.Rodrigues(y_axis * np.radians(theta))
        R2, _ = cv2.Rodrigues(np.dot(R1, x_axis) * np.radians(PHI))
        R = R2 @ R1

        # Apply rotation to get 3D direction vector
        xyz = normalized @ R.T

        # Convert to longitude/latitude
        lon = np.arctan2(xyz[0], xyz[2])
        hyp = np.sqrt(xyz[0] ** 2 + xyz[2] ** 2)
        lat = np.arctan2(xyz[1], hyp)

        # Convert to equirectangular pixel coordinates
        eq_x = (lon / (2 * np.pi) + 0.5) * width_src
        eq_y = (lat / np.pi + 0.5) * height_src

        logger.debug(f"✅ Mapped to equirectangular: ({eq_x:.2f}, {eq_y:.2f})")
        
        return (eq_x, eq_y)
        
    except Exception as e:
        logger.error(f"❌ Error mapping point ({x}, {y}) at θ={theta}°: {str(e)}")
        raise

def get_perspective(img, FOV, THETA, PHI, height, width, height_src, width_src):
    """
    Extract a perspective view from an equirectangular image.

    Parameters:
    - img (np.ndarray): Source equirectangular image.
    - FOV (int): Field of View in degrees.
    - THETA (int): Horizontal angle in degrees.
    - PHI (int): Vertical angle in degrees.
    - height (int): Height of the perspective image.
    - width (int): Width of the perspective image.
    - width_src (int): Source image width.
    - height_src (int): Source image height.

    Returns:
    - persp_img (np.ndarray): The resulting perspective image.
    """
    logger.debug(f"🎯 Extracting perspective view: θ={THETA}°, φ={PHI}°, FOV={FOV}°")
    
    try:
        f = 0.5 * width * 1 / np.tan(0.5 * FOV / 180.0 * np.pi)
        cx = (width - 1) / 2.0
        cy = (height - 1) / 2.0
        K = np.array(
            [
                [f, 0, cx],
                [0, f, cy],
                [0, 0, 1],
            ],
            np.float32,
        )
        K_inv = np.linalg.inv(K)

        x = np.arange(width)
        y = np.arange(height)
        x, y = np.meshgrid(x, y)
        z = np.ones_like(x)
        xyz = np.stack([x, y, z], axis=-1) @ K_inv.T

        y_axis = np.array([0.0, 1.0, 0.0], np.float32)
        x_axis = np.array([1.0, 0.0, 0.0], np.float32)
        R1, _ = cv2.Rodrigues(y_axis * np.radians(THETA))
        R2, _ = cv2.Rodrigues(np.dot(R1, x_axis) * np.radians(PHI))
        R = R2 @ R1
        xyz = xyz @ R.T

        lonlat = xyz2lonlat(xyz)
        XY = lonlat2XY(lonlat, width_src, height_src).astype(np.float32)
        persp_img = cv2.remap(
            img,
            XY[..., 0],
            XY[..., 1],
            cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_WRAP,
        )

        logger.debug(f"✅ Perspective view extracted successfully - Output shape: {persp_img.shape}")
        return persp_img
        
    except Exception as e:
        logger.error(f"❌ Error extracting perspective view at θ={THETA}°: {str(e)}")
        raise

async def fetch_pano_by_id(pano_id: str, session: ClientSession, max_retries: int = 3):
    """Fetch panorama by ID with retry logic and optimized networking."""
    logger.info(f"🔍 Fetching panorama: {pano_id}")
    fetch_start_time = time.time()
    
    for attempt in range(max_retries):
        try:
            # Fetch panorama metadata and depth
            pano = await streetview.find_panorama_by_id_async(
                pano_id, session, download_depth=True
            )
            
            if pano is None:
                logger.warning(f"⚠️ No panorama found for {pano_id}")
                return None, None

            if pano.depth is None:
                logger.warning(f"⚠️ No depth map for {pano_id}")
                return None, None
                
            logger.info(f"📍 Panorama found: {pano_id} at ({pano.lat}, {pano.lon})")
            
            # Fetch RGB image with retry
            rgb = await streetview.get_panorama_async(pano, session) 
            rgb_array = np.array(rgb)
            
            fetch_time = time.time() - fetch_start_time
            logger.info(f"✅ Panorama {pano_id} fetched in {fetch_time:.2f}s - Shape: {rgb_array.shape}")
            
            return pano, rgb_array
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout fetching {pano_id} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
        except ValueError as e:
            if "invalid literal for int() with base 2" in str(e):
                logger.warning(f"🔧 Binary parsing error for {pano_id} (attempt {attempt + 1}/{max_retries}): Corrupted panorama data")
            else:
                logger.warning(f"❌ ValueError fetching panorama {pano_id} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
        except Exception as e:
            logger.warning(f"❌ Error fetching panorama {pano_id} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                continue
    
    logger.error(f"❌ Failed to fetch panorama {pano_id} after {max_retries} attempts")
    return None, None
