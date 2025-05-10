"""
Flight validator module for DroneForce Protocol.
Responsible for validating flight logs against task specifications.
"""
from typing import Dict, List, Any, Tuple
import math


class FlightValidator:
    """
    Validator for flight logs against task specifications.
    Checks if the flight meets the requirements specified in the task.
    """
    
    def __init__(
        self,
        flight_data: Dict[str, Any],
        location: Dict[str, float],
        area_size: float,
        max_altitude: float,
        min_duration: float,
        geofencing_enabled: bool = True
    ):
        """
        Initialize the flight validator.
        
        Args:
            flight_data: Parsed flight data from LogParser
            location: Center location (lat, lng) of the flight area
            area_size: Size of the flight area in meters (square area)
            max_altitude: Maximum allowed altitude in meters
            min_duration: Minimum required flight duration in seconds
            geofencing_enabled: Whether geofencing is enabled
        """
        self.flight_data = flight_data
        self.center_location = location
        self.area_size = area_size
        self.max_altitude = max_altitude
        self.min_duration = min_duration
        self.geofencing_enabled = geofencing_enabled
        
        # Calculate bounding box (simplified - assumes square area around center point)
        # This is a simplified approximation - for production, use proper geo libraries
        # 1 degree of latitude = ~111,000 meters
        # 1 degree of longitude = ~111,000 * cos(latitude) meters
        lat_offset = (area_size / 2) / 111000
        lng_offset = (area_size / 2) / (111000 * math.cos(math.radians(location['lat'])))
        
        self.bounds = {
            'min_lat': location['lat'] - lat_offset,
            'max_lat': location['lat'] + lat_offset,
            'min_lng': location['lng'] - lng_offset,
            'max_lng': location['lng'] + lng_offset
        }
    
    def validate(self) -> bool:
        """
        Validate the flight data against the task specifications.
        
        Returns:
            bool: True if flight meets all requirements, False otherwise
        """
        # Validate flight duration
        duration_valid = self._validate_duration()
        
        # Validate altitude
        altitude_valid = self._validate_altitude()
        
        # Validate geofence if enabled
        geofence_valid = True
        if self.geofencing_enabled:
            geofence_valid = self._validate_geofence()
        
        # All validations must pass
        return duration_valid and altitude_valid and geofence_valid
    
    def _validate_duration(self) -> bool:
        """
        Validate that the flight duration meets the minimum requirement.
        
        Returns:
            bool: True if duration is valid, False otherwise
        """
        return self.flight_data['duration'] >= self.min_duration
    
    def _validate_altitude(self) -> bool:
        """
        Validate that the flight altitude is within the allowed limit.
        
        Returns:
            bool: True if altitude is valid, False otherwise
        """
        return self.flight_data['max_altitude'] <= self.max_altitude
    
    def _validate_geofence(self) -> bool:
        """
        Validate that the flight stayed within the defined geofence.
        
        Returns:
            bool: True if geofence was respected, False otherwise
        """
        for point in self.flight_data['gps_points']:
            # Check if the point is within the bounding box
            if (point['lat'] < self.bounds['min_lat'] or
                point['lat'] > self.bounds['max_lat'] or
                point['lng'] < self.bounds['min_lng'] or
                point['lng'] > self.bounds['max_lng']):
                return False
        
        return True
    
    def get_validation_details(self) -> Dict[str, Any]:
        """
        Get detailed validation results.
        
        Returns:
            Dict with detailed validation results:
            {
                'duration_valid': bool,
                'altitude_valid': bool,
                'geofence_valid': bool,
                'overall_valid': bool
            }
        """
        duration_valid = self._validate_duration()
        altitude_valid = self._validate_altitude()
        geofence_valid = True
        if self.geofencing_enabled:
            geofence_valid = self._validate_geofence()
        
        return {
            'duration_valid': duration_valid,
            'altitude_valid': altitude_valid,
            'geofence_valid': geofence_valid,
            'overall_valid': duration_valid and altitude_valid and geofence_valid
        }
