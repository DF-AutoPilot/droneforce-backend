import os
import hashlib
import json
import tempfile
from typing import Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud import storage as google_storage
from google.cloud.functions import Context
import functions_framework

from validator.parser import LogParser
from validator.validator import FlightValidator
from validator.uploader import ArweaveUploader
from validator.blockchain import SolanaClient

# Initialize Firebase
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
})
db = firestore.client()

@functions_framework.cloud_event
async def process_drone_log(cloud_event: Dict[str, Any], context: Context) -> None:
    """
    Cloud Function triggered when a .bin log file is uploaded to Firebase Storage.
    
    Args:
        cloud_event: The Cloud Event object.
        context: The event context.
    """
    try:
        # Extract file path from the cloud event
        bucket_name = cloud_event['bucket']
        file_path = cloud_event['name']
        
        # Validate that this is a log file in the logs directory
        if not file_path.startswith('logs/') or not file_path.endswith('.bin'):
            print(f"Ignoring file: {file_path} - not a log file in the logs directory")
            return
        
        # Extract task ID from file path (assuming format logs/{taskId}.bin)
        task_id = file_path.split('/')[1].replace('.bin', '')
        print(f"Processing log for task ID: {task_id}")
        
        # Get the task specification from Firestore
        task_doc = db.collection('tasks').document(task_id).get()
        if not task_doc.exists:
            raise ValueError(f"Task with ID {task_id} not found in Firestore")
        
        task_spec = task_doc.to_dict()
        print(f"Task specification retrieved: {task_spec}")
        
        # Download the log file
        bucket = storage.bucket(bucket_name)
        blob = bucket.blob(file_path)
        
        # Create a temporary file to store the log
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            blob.download_to_filename(temp_file.name)
            log_file_path = temp_file.name
        
        # Parse the log file
        parser = LogParser(log_file_path)
        parsed_log = parser.parse()
        
        # Validate the log
        validator = FlightValidator(
            parsed_log,
            location=task_spec['location'],
            area_size=task_spec['area_size'],
            max_altitude=task_spec['altitude'],
            min_duration=task_spec['duration'],
            geofencing_enabled=task_spec['geofencing_enabled']
        )
        
        verification_result = validator.validate()
        print(f"Verification result: {verification_result}")
        
        # Generate verification report hash
        verification_params = json.dumps({
            'location': task_spec['location'],
            'area_size': task_spec['area_size'],
            'altitude': task_spec['altitude'],
            'duration': task_spec['duration'],
            'geofencing_enabled': task_spec['geofencing_enabled']
        })
        
        # Read binary log file for hash
        with open(log_file_path, 'rb') as f:
            log_content = f.read()
        
        # Create hash of log file + validation params + result
        verification_data = log_content + verification_params.encode() + str(verification_result).encode()
        verification_report_hash = hashlib.sha256(verification_data).hexdigest()
        print(f"Verification report hash: {verification_report_hash}")
        
        # Upload log to Arweave
        uploader = ArweaveUploader()
        arweave_tx_id = await uploader.upload_log(log_file_path)
        print(f"Log uploaded to Arweave with transaction ID: {arweave_tx_id}")
        
        # Call Solana contract
        solana_client = SolanaClient()
        tx_signature = await solana_client.record_verification(
            task_id, 
            verification_result, 
            verification_report_hash
        )
        print(f"Verification recorded on Solana with signature: {tx_signature}")
        
        # Update task in Firestore
        task_update = {
            'verification_result': verification_result,
            'verification_report_hash': verification_report_hash,
            'arweave_tx_id': arweave_tx_id,
            'solana_tx_signature': tx_signature,
            'verification_timestamp': firestore.SERVER_TIMESTAMP
        }
        
        db.collection('tasks').document(task_id).update(task_update)
        print(f"Task {task_id} updated in Firestore with verification results")
        
        # Clean up temporary file
        os.unlink(log_file_path)
        
    except Exception as e:
        print(f"Error processing drone log: {str(e)}")
        raise  # Re-raise the exception to fail the function
