"""
Blockchain interaction module for DroneForce Protocol.
Responsible for interacting with Solana blockchain.
"""
import os
import base64
from typing import Dict, Any, Optional

import solana
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Confirmed
from anchorpy import Program, Provider, Wallet

from config import settings


class SolanaClient:
    """
    Client for interacting with Solana blockchain and smart contracts.
    """
    
    def __init__(self):
        """
        Initialize the Solana client with wallet and RPC connection.
        """
        # Load validator wallet keypair
        if settings.SOLANA_VALIDATOR_PRIVATE_KEY:
            secret_key = base64.b64decode(settings.SOLANA_VALIDATOR_PRIVATE_KEY)
            self.keypair = Keypair.from_secret_key(secret_key)
        else:
            raise ValueError("Solana validator private key not provided")
        
        # Create RPC client
        self.client = AsyncClient(settings.SOLANA_RPC_URL, commitment=Confirmed)
        
        # Set up Anchor provider and program
        self.provider = Provider(
            self.client, 
            Wallet(self.keypair),
            opts={"commitment": "confirmed"}
        )
        
        # Load program if the ID is provided
        self.program_id = settings.SOLANA_PROGRAM_ID
        if self.program_id:
            self.program = Program(
                settings.SOLANA_PROGRAM_IDL,
                PublicKey(self.program_id),
                self.provider
            )
        else:
            self.program = None
            
    async def record_verification(
        self, 
        task_id: str, 
        verification_result: bool, 
        verification_report_hash: str
    ) -> str:
        """
        Record verification result on the Solana blockchain.
        
        Args:
            task_id: Task ID
            verification_result: Verification result (True/False)
            verification_report_hash: SHA-256 hash of verification report
            
        Returns:
            str: Transaction signature
        """
        if not self.program:
            raise ValueError("Solana program not initialized")
        
        # Get the program account for the task (simplified - in a real system you'd derive this)
        task_key = PublicKey.create_with_seed(
            self.keypair.public_key,
            task_id,
            PublicKey(self.program_id)
        )
        
        # Call the record_verification function on the smart contract
        tx_sig = await self.program.rpc["record_verification"](
            task_id,
            verification_result,
            verification_report_hash,
            ctx=solana.rpc.types.TxOpts(
                skip_preflight=False,
                preflight_commitment=Confirmed
            )
        )
        
        # Return the transaction signature
        return tx_sig
    
    async def get_verification_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the verification status of a task from the blockchain.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict with verification status
        """
        if not self.program:
            raise ValueError("Solana program not initialized")
        
        # Get the program account for the task (simplified - in a real system you'd derive this)
        task_key = PublicKey.create_with_seed(
            self.keypair.public_key,
            task_id,
            PublicKey(self.program_id)
        )
        
        # Fetch the account data
        account_info = await self.client.get_account_info(task_key)
        
        if account_info.value is None:
            return {
                "found": False,
                "task_id": task_id
            }
        
        # Deserialize the account data using Anchorpy
        task_account = self.program.account["TaskAccount"].parse(account_info.value.data)
        
        return {
            "found": True,
            "task_id": task_id,
            "verification_result": task_account.verification_result,
            "verification_report_hash": task_account.verification_report_hash,
            "verified_at": task_account.verified_at,
            "verified_by": task_account.verified_by
        }
    
    async def close(self):
        """Close the RPC client connection."""
        await self.client.close()
