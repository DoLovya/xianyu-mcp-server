## ADDED Requirements

### Requirement: Upload media as reusable asset

The system SHALL provide an MCP tool `upload_media` that uploads a local file path or a remote http/https URL to the goofish upload endpoint and returns a reusable asset URL.

#### Scenario: Upload local image file
- **WHEN** the caller provides an absolute local image path
- **THEN** the system uploads the file and returns `success=true` with a non-empty `url`

#### Scenario: Upload remote image URL
- **WHEN** the caller provides a remote http/https URL
- **THEN** the system downloads it to a temporary local file, uploads it, deletes the temporary file, and returns `success=true` with a non-empty `url`

#### Scenario: Upload unsupported or missing path
- **WHEN** the caller provides a non-existing local path
- **THEN** the system returns an error indicating the file does not exist

### Requirement: Return pixel metadata when available

If the upstream upload response contains pixel metadata, the system SHALL expose it in the tool result and provide parsed width/height when the format is `WxH`.

#### Scenario: Upstream returns pix
- **WHEN** the upload response includes `object.pix`
- **THEN** the system returns `pix` and parsed `width`/`height`

### Requirement: Respect write guardrails

The upload operation SHALL be executed as a write operation under the request guardrails to ensure global serialization and rate limiting.

#### Scenario: Upload is treated as write operation
- **WHEN** `upload_media` is invoked
- **THEN** the upload is executed through write guardrails, not read guardrails
