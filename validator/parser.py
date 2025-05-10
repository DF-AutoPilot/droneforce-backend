"""
Log parser module for DroneForce Protocol.
Responsible for parsing ArduPilot .bin log files using pymavlink.
"""
import os
import time
from typing import Dict, List, Any, Optional

from pymavlink import DFReader


class LogParser:
    """Parser for ArduPilot binary log files."""
    
    def __init__(self, log_path: str):
        """
        Initialize the log parser.
        
        Args:
            log_path: Path to the .bin log file
        """
        self.log_path = log_path
        
        if not os.path.exists(log_path):
            raise FileNotFoundError(f"Log file not found at {log_path}")
            
        if not log_path.endswith('.bin'):
            raise ValueError(f"Unsupported log format. Expected .bin file, got {log_path}")
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the binary log file and extract flight data.
        
        Returns:
            Dict containing parsed flight data:
            {
                'gps_points': List of GPS coordinates (lat, lng, alt, timestamp),
                'start_time': Flight start time (Unix timestamp),
                'end_time': Flight end time (Unix timestamp),
                'duration': Flight duration in seconds,
                'max_altitude': Maximum altitude reached during flight,
                'avg_altitude': Average altitude during flight,
                'operator_pubkey': Operator public key (if available)
            }
        """
        log = DFReader.DFReader_binary(self.log_path, zero_time_base=True)
        
        gps_points = []
        altitudes = []
        timestamps = []
        operator_pubkey = None
        
        # Process log messages
        while True:
            msg = log.recv_match()
            if msg is None:
                break
                
            msg_type = msg.get_type()
            
            # Extract GPS position
            if msg_type == 'GPS':
                if msg.Status >= 3:  # 3D Fix or better
                    lat = msg.Lat / 1e7  # Convert from scaled integer to degrees
                    lng = msg.Lng / 1e7
                    alt = msg.Alt / 100.0  # Convert from cm to meters
                    timestamp = msg._timestamp
                    
                    gps_points.append({
                        'lat': lat,
                        'lng': lng,
                        'alt': alt,
                        'timestamp': timestamp
                    })
                    
                    altitudes.append(alt)
                    timestamps.append(timestamp)
            
            # Extract operator public key (simplified - in a real system this would be from a custom message or parameter)
            elif msg_type == 'PARM' and msg.Name == 'OPERATOR_PUBKEY':
                operator_pubkey = msg.Value
        
        # Compute derived data
        if not gps_points:
            raise ValueError("No valid GPS points found in log file")
            
        start_time = min(timestamps) if timestamps else None
        end_time = max(timestamps) if timestamps else None
        duration = end_time - start_time if start_time and end_time else 0
        max_altitude = max(altitudes) if altitudes else 0
        avg_altitude = sum(altitudes) / len(altitudes) if altitudes else 0
        
        return {
            'gps_points': gps_points,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'max_altitude': max_altitude,
            'avg_altitude': avg_altitude,
            'operator_pubkey': operator_pubkey
        }
