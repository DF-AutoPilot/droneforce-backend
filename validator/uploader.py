"""
Arweave uploader module for DroneForce Protocol.
Responsible for uploading log files to Arweave.
"""
import os
import json
from typing import Any, Dict, Optional

import arweave
from arweave.arweave_lib import Wallet
from arweave.transaction import Transaction

from config import settings


class ArweaveUploader:
    """
    Handles uploads of log files to Arweave blockchain.
    """
    
    def __init__(self):
        """
        Initialize the Arweave uploader with wallet.
        """
        wallet_filepath = settings.ARWEAVE_WALLET_FILE
        
        if not os.path.exists(wallet_filepath):
            raise FileNotFoundError(f"Arweave wallet file not found: {wallet_filepath}")
        
        with open(wallet_filepath, 'r') as f:
            wallet_json = json.load(f)
            
        self.wallet = Wallet(wallet_json)
        self.arweave_client = arweave.Arweave(
            host=settings.ARWEAVE_HOST,
            port=settings.ARWEAVE_PORT,
            protocol=settings.ARWEAVE_PROTOCOL
        )
    
    async def upload_log(self, log_file_path: str) -> str:
        """
        Upload a log file to Arweave.
        
        Args:
            log_file_path: Path to the log file to upload
            
        Returns:
            str: Transaction ID of the uploaded file
        """
        # Read file contents
        with open(log_file_path, 'rb') as f:
            file_data = f.read()
        
        # Create transaction
        transaction = await self.arweave_client.transactions.create(
            wallet=self.wallet,
            data=file_data
        )
        
        # Add tags
        transaction.add_tag('Content-Type', 'application/octet-stream')
        transaction.add_tag('App-Name', 'DroneForce-Protocol')
        transaction.add_tag('Type', 'drone-flight-log')
        transaction.add_tag('Version', '1.0.0')
        
        # Sign and submit transaction
        await transaction.sign(self.wallet)
        await self.arweave_client.transactions.post(transaction)
        
        # Return transaction ID
        return transaction.id
    
    async def get_upload_status(self, tx_id: str) -> Dict[str, Any]:
        """
        Get the status of an uploaded file.
        
        Args:
            tx_id: Transaction ID of the uploaded file
            
        Returns:
            Dict with status information
        """
        # Get transaction status
        status = await self.arweave_client.transactions.get_status(tx_id)
        
        # Get transaction data
        transaction = await self.arweave_client.transactions.get(tx_id)
        
        return {
            'id': tx_id,
            'status': status,
            'confirmed': status == 200,
            'data_size': transaction.data_size if hasattr(transaction, 'data_size') else None,
            'owner': transaction.owner if hasattr(transaction, 'owner') else None
        }
