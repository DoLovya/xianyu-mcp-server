## ADDED Requirements

### Requirement: Service can run without source checkout
`xianyu-mcp` MUST be runnable after installing from PyPI, without requiring users to clone the repository or initialize git submodules.

#### Scenario: uvx run
- **WHEN** a user runs `uvx xianyu-mcp`
- **THEN** the MCP server process MUST start successfully (imports and module initialization complete)

### Requirement: Runtime dependency uses installed `pyxianyu`
At runtime, the MCP server MUST load `pyxianyu` from the Python environment (site-packages) and MUST NOT depend on `third_party/pyxianyu` being present.

#### Scenario: Import uses pyxianyu namespace
- **WHEN** the server initializes its underlying API client
- **THEN** it MUST be able to `import pyxianyu` and resolve required classes (client/apis/message/utils)

### Requirement: Developer workflow remains usable
For repository development, the MCP server MAY support an optional fallback that uses the local `third_party/pyxianyu` checkout when present, but this MUST NOT be required for installed usage.

#### Scenario: Fallback only in dev
- **WHEN** running from a source checkout with `third_party/pyxianyu` present
- **THEN** the server MAY use local code for convenience
