"""
Configuration settings for DroneForce Protocol backend.
Loads environment variables and provides default values.
"""
import os
import json
from pathlib import Path

# Firebase Configuration
FIREBASE_STORAGE_BUCKET = os.environ.get('FIREBASE_STORAGE_BUCKET', 'droneforce-protocol.appspot.com')

# Operator Configuration
# In a production environment, this would be fetched dynamically
OPERATOR_PUBKEY = os.environ.get('OPERATOR_PUBKEY', 'default_operator_pubkey')

# Arweave Configuration
ARWEAVE_HOST = os.environ.get('ARWEAVE_HOST', 'arweave.net')
ARWEAVE_PORT = int(os.environ.get('ARWEAVE_PORT', '443'))
ARWEAVE_PROTOCOL = os.environ.get('ARWEAVE_PROTOCOL', 'https')
ARWEAVE_WALLET_FILE = os.environ.get('ARWEAVE_WALLET_FILE', '/path/to/arweave-wallet.json')

# Solana Configuration
SOLANA_RPC_URL = os.environ.get('SOLANA_RPC_URL', 'https://api.devnet.solana.com')
SOLANA_PROGRAM_ID = os.environ.get('SOLANA_PROGRAM_ID', 'your_program_id_here')
SOLANA_VALIDATOR_PRIVATE_KEY = os.environ.get('SOLANA_VALIDATOR_PRIVATE_KEY', '')

# Load Solana Program IDL
SOLANA_PROGRAM_IDL_PATH = os.environ.get('SOLANA_PROGRAM_IDL_PATH', 'config/program_idl.json')
try:
    if os.path.exists(SOLANA_PROGRAM_IDL_PATH):
        with open(SOLANA_PROGRAM_IDL_PATH, 'r') as f:
            SOLANA_PROGRAM_IDL = json.load(f)
    else:
        # Simplified IDL for demo purposes
        SOLANA_PROGRAM_IDL = {
            "version": "0.1.0",
            "name": "droneforce_protocol",
            "instructions": [
                {
                    "name": "recordVerification",
                    "accounts": [
                        {
                            "name": "taskAccount",
                            "isMut": True,
                            "isSigner": False
                        },
                        {
                            "name": "validator",
                            "isMut": True,
                            "isSigner": True
                        },
                        {
                            "name": "systemProgram",
                            "isMut": False,
                            "isSigner": False
                        }
                    ],
                    "args": [
                        {
                            "name": "taskId",
                            "type": "string"
                        },
                        {
                            "name": "verificationResult",
                            "type": "bool"
                        },
                        {
                            "name": "verificationReportHash",
                            "type": "string"
                        }
                    ]
                }
            ],
            "accounts": [
                {
                    "name": "TaskAccount",
                    "type": {
                        "kind": "struct",
                        "fields": [
                            {
                                "name": "taskId",
                                "type": "string"
                            },
                            {
                                "name": "verificationResult",
                                "type": "bool"
                            },
                            {
                                "name": "verificationReportHash",
                                "type": "string"
                            },
                            {
                                "name": "verifiedAt",
                                "type": "i64"
                            },
                            {
                                "name": "verifiedBy",
                                "type": "publicKey"
                            }
                        ]
                    }
                }
            ]
        }
except Exception as e:
    print(f"Warning: Failed to load Solana Program IDL: {str(e)}")
    SOLANA_PROGRAM_IDL = {}
