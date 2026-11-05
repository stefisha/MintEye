# Security notes

MintEye is a hackathon prototype. Its predictions are experimental, and the application has not undergone a complete security audit.

## Credentials and logs

- Store the authenticated DAS endpoint in a local `.env` or a server environment variable. Never commit a populated environment file.
- Avoid logging provider response bodies, authenticated endpoint URLs, or full request exceptions. Provider credentials may be embedded in URL query parameters.
- Keep runtime logs and generated artifacts out of Git. The included `.env.example` contains no credential values.
- Revoke or rotate credentials if they are ever exposed. Deleting a file does not remove it from earlier commits.

## Model artifacts

Use only trusted model files. Python pickle deserialization can execute code, and model loading should not accept user-supplied files. The bundled models are the original inference artifacts; this cleanup does not retrain them or validate their detection accuracy.

## Deployment boundaries

The application fetches images from NFT metadata and performs potentially expensive inference. Before a public deployment, review remote URL handling and SSRF protection, download and image size limits, rate limits, authentication, CORS policy, dependency advisories, and process isolation. Configure a production server and leave the development debugger disabled.

Do not post private credentials or personal data in public issues.
