# DroneForce Protocol Backend

A Google Cloud Functions backend for the DroneForce Protocol, validating drone flight logs against task specifications and recording results on the Solana blockchain.

## Architecture

This backend is triggered when a drone uploads a .bin ArduPilot log file to Firebase Storage. It validates the flight log against the task specifications, uploads the log to Arweave for permanent storage, and records the verification result on a Solana smart contract.

## Features

- Parses ArduPilot .bin log files using pymavlink
- Validates flight parameters:
  - Flight path inside the specified bounding box
  - Altitude below the specified maximum
  - Flight duration greater than the specified minimum
- Computes a verification report hash
- Uploads log files to Arweave blockchain
- Records verification results on a Solana smart contract
- Updates task status in Firestore

## Project Structure

```
droneforce-backend/
 ├── main.py                # Cloud Function handler
 ├── requirements.txt       # Dependencies
 ├── validator/
 │   ├── parser.py          # Log file parser
 │   ├── validator.py       # Flight validation logic
 │   ├── uploader.py        # Arweave uploader
 │   └── blockchain.py      # Solana integration
 └── config/
     └── settings.py        # Configuration settings
```

## Setup and Deployment

### Prerequisites

- Google Cloud Platform account with Cloud Functions enabled
- Firebase project with Firestore and Storage enabled
- Solana wallet and program deployment
- Arweave wallet

### Environment Variables

Set the following environment variables:

```
FIREBASE_STORAGE_BUCKET=your-firebase-bucket.appspot.com
OPERATOR_PUBKEY=your_operator_public_key
ARWEAVE_WALLET_FILE=/path/to/arweave-wallet.json
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_PROGRAM_ID=your_solana_program_id
SOLANA_VALIDATOR_PRIVATE_KEY=your_base64_encoded_private_key
```

### Deployment

Deploy the Cloud Function using Firebase CLI:

```bash
firebase deploy --only functions
```

Alternatively, you can deploy using gcloud CLI:

```bash
gcloud functions deploy process_drone_log \
  --runtime python39 \
  --trigger-resource your-firebase-bucket.appspot.com \
  --trigger-event google.storage.object.finalize \
  --entry-point process_drone_log \
  --memory 256MB \
  --timeout 540s
```

## Task Specification

The task specifications are stored in Firestore at `/tasks/{taskId}` with the following schema:

```json
{
  "location": { "lat": 17.3850, "lng": 78.4867 },
  "area_size": 100,
  "altitude": 80,
  "duration": 300,
  "task_type": "PHOTO_TOPDOWN",
  "geofencing_enabled": true,
  "description": "Survey rooftop"
}
```

## Workflow

1. Drone uploads .bin log file to Firebase Storage at `/logs/{taskId}.bin`
2. Cloud Function is triggered automatically
3. Function downloads and parses the log file
4. Function validates the flight path, altitude, and duration
5. Function computes verification hash and uploads to Arweave
6. Function records verification result on Solana blockchain
7. Function updates task status in Firestore

## Testing

To test the function locally, you can use the Functions Framework:

```bash
functions-framework --target=process_drone_log
```

## License

MIT
