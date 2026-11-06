![MintEye](static/full_name_logo.png)

# MintEye

**NFT risk classification for Solana.** A Solana Radar Hackathon prototype combining image classification and NFT metadata analysis in a Flask application.

[![Python](https://img.shields.io/badge/Python-3.10–3.12-3776AB?logo=python&logoColor=white)](#local-setup)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.17-FF6F00?logo=tensorflow&logoColor=white)](#models-and-predictions)
[![License: MIT](https://img.shields.io/badge/License-MIT-249B9A)](LICENSE)

## Overview

Enter a Solana NFT mint address to retrieve its metadata, analyze its image and available metadata features, and display a `legit` or `scam` prediction.

I developed and deployed the application’s frontend and backend, bringing NFT classification research into an interactive tool. The underlying research also informed my [master’s thesis](https://github.com/stefisha/DetectingNFTs-MasterThesis). By launch, interest in NFTs had declined substantially, limiting the project’s traction.

MintEye was built as a hackathon experiment. The labels are model predictions, not verified assessments of an NFT's safety. This repository contains the original web interface and trained inference artifacts; the training dataset and training notebooks are not included.

## How it works

1. **Retrieve the asset:** call a configured Solana DAS provider's `getAsset` method with the mint address.
2. **Analyze the image:** download the referenced image, convert it to RGB, resize it to 256 × 256, and run the fine-tuned MobileNetV3 classifier.
3. **Analyze metadata:** run up to five XGBoost classifiers when their required features are present, then use a majority vote.
4. **Combine results:** give the image and metadata class decisions equal weight. If one branch is unavailable, use the other. A combined value of at least `0.5` produces the `scam` label.

The response's historical `probability` field is the image classifier's confidence in its chosen class when an image prediction is available; otherwise it reflects the metadata decision. It is **not a calibrated probability that an NFT is a scam**.

## Local setup

Use Python 3.10–3.12, pip, and a Solana RPC provider that supports the Digital Asset Standard (DAS) `getAsset` method. A standard Solana JSON-RPC endpoint alone is not sufficient.

```sh
git clone https://github.com/stefisha/MintEye-Radar-Hackathon-Application.git
cd MintEye-Radar-Hackathon-Application

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

cp .env.example .env
```

On Windows, activate the environment with `.venv\Scripts\activate`. On macOS, XGBoost may require the OpenMP runtime (`brew install libomp`). TensorFlow 2.17 wheels support Apple silicon; Intel Mac users should use a compatible Linux environment for these pins.

Set `RPC_URL_DAS` in your local `.env` to your provider's authenticated DAS endpoint, then start the app:

```sh
python server.py
```

Open `http://127.0.0.1:5000`. The six model files are already included under `models/`; no training step is needed. Model, configuration, and log paths resolve relative to the project directory.

Debug mode is disabled by default. Set `FLASK_DEBUG=1` only for local debugging. The built-in Flask server is intended for local development.

## API

### `GET /`

Serves the original mint-address form, image preview, and prediction result.

### `POST /fetch_nft`

Accepts a form field named `nft_mint`:

```sh
curl -X POST http://127.0.0.1:5000/fetch_nft \
  --data-urlencode 'nft_mint=YOUR_NFT_MINT_ADDRESS'
```

Successful responses contain:

| Field | Meaning |
| --- | --- |
| `image_url` | Image URI from asset metadata, or `null` |
| `prediction` | `legit` or `scam` |
| `probability` | Historical confidence/decision output described above |

A missing mint returns HTTP 400. Provider or classification failures return HTTP 500 with an error message. Provider requests use a 15-second timeout; image downloads use a 5-second timeout.

## Models and predictions

| Artifact | Purpose |
| --- | --- |
| `models/mobilenetv3_tunned.keras` | Fine-tuned MobileNetV3 image classifier |
| `models/model_0.pkl` … `model_4.pkl` | Five metadata classifiers, each paired with its required feature list |

The dependency list uses TensorFlow 2.17 and Keras 3 to match the bundled image model format. Metadata models require XGBoost and scikit-learn. Load only trusted model artifacts: Python pickle files can execute code when loaded.

Metadata models are skipped when their required fields are absent. No prediction is returned if neither branch can produce a result. Evaluation metrics, calibration results, training data, and guarantees of generalization are not supplied by this repository.

## Validation

```sh
python -m pip check
python -m unittest discover -s tests -v
```

The tests load the bundled models, run local inference, exercise the Flask routes with mocked provider responses, and check that provider errors do not expose credentials. They make no live RPC calls.

The optional Locust script sends real requests to the configured app and provider:

```sh
python -m pip install -r requirements-dev.txt
locust -f locustfile.py --host http://127.0.0.1:5000
```

Configure your own test mint in `locustfile.py` and respect your provider's request limits.

## Repository structure

```text
models/                Trained image and metadata artifacts
static/                Original logo, images, and styles
templates/index.html   Original web interface
server.py              Flask routes and inference pipeline
locustfile.py          Optional load-testing script
tests/                 Offline model and route checks
.env.example           Safe local configuration template
requirements.txt       Application runtime dependencies
requirements-dev.txt   Optional load-test dependency
```

## Configuration and security

Keep provider credentials in the environment or an ignored `.env` file. Logs and generated Python files are excluded from Git. Provider response bodies and credential-bearing exception URLs are not logged or returned to the browser.

This is a prototype, not a hardened public service. Review request validation, remote image fetching, resource limits, authentication, rate limiting, and dependencies before exposing it publicly. See [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) · Copyright © 2024 Stefan Veličković.
