# Beta Skills API

Create and manage reusable capabilities with version control.

## Overview

The Skills API allows you to create, manage, and version reusable capabilities that can be used across conversations. Skills are defined by uploading files including a SKILL.md file that describes the skill's functionality.

## Key Features

- Create skills with file uploads
- Version control for skill evolution
- List and filter skills by source (custom or Anthropic-provided)
- Delete skills and specific versions
- Cursor-based pagination for scalability

## Skills API

### Create Skill

```python { .api }
def create(
    self,
    *,
    display_title: str | None = NOT_GIVEN,
    files: list[FileTypes] | None = NOT_GIVEN,
    **kwargs
) -> SkillCreateResponse:
    """
    Create a skill.

    Parameters:
        display_title: Display title for the skill (human-readable label, not included in model prompt)
        files: Files to upload for the skill
               All files must be in the same top-level directory
               Must include a SKILL.md file at the root

    Returns:
        SkillCreateResponse object
    """
    ...
```

### Retrieve Skill

```python { .api }
def retrieve(
    self,
    skill_id: str,
    **kwargs
) -> SkillRetrieveResponse:
    """
    Retrieve skill by ID.

    Parameters:
        skill_id: Unique identifier for the skill

    Returns:
        SkillRetrieveResponse with skill details
    """
    ...
```

### List Skills

```python { .api }
def list(
    self,
    *,
    limit: int = NOT_GIVEN,
    page: str | None = NOT_GIVEN,
    source: str | None = NOT_GIVEN,
    **kwargs
) -> SyncPageCursor[SkillListResponse]:
    """
    List skills with cursor-based pagination.

    Parameters:
        limit: Number of results per page (max 100, default 20)
        page: Pagination token from previous response's next_page field
        source: Filter by source ("custom" for user-created, "anthropic" for Anthropic-created)

    Returns:
        SyncPageCursor[SkillListResponse] with paginated results
    """
    ...
```

### Delete Skill

```python { .api }
def delete(
    self,
    skill_id: str,
    **kwargs
) -> SkillDeleteResponse:
    """
    Delete a skill.

    Parameters:
        skill_id: Unique identifier for the skill

    Returns:
        SkillDeleteResponse confirming deletion
    """
    ...
```

## Skill Versions API

Manage versions of existing skills for evolution and rollback capabilities.

### Create Version

```python { .api }
def create(
    self,
    skill_id: str,
    *,
    files: list[FileTypes] | None = NOT_GIVEN,
    **kwargs
) -> VersionCreateResponse:
    """
    Create a new version of a skill.

    Parameters:
        skill_id: Unique identifier for the skill
        files: Files to upload for the skill version
               Must include a SKILL.md file at the root

    Returns:
        VersionCreateResponse with new version details
    """
    ...
```

### Retrieve Version

```python { .api }
def retrieve(
    self,
    version: str,
    *,
    skill_id: str,
    **kwargs
) -> VersionRetrieveResponse:
    """
    Get details about a specific skill version.

    Parameters:
        version: Version identifier
        skill_id: Unique identifier for the skill

    Returns:
        VersionRetrieveResponse with version details
    """
    ...
```

### List Versions

```python { .api }
def list(
    self,
    skill_id: str,
    *,
    limit: int | None = NOT_GIVEN,
    page: str | None = NOT_GIVEN,
    **kwargs
) -> SyncPageCursor[VersionListResponse]:
    """
    List versions of a skill.

    Parameters:
        skill_id: Unique identifier for the skill
        limit: Number of items to return per page (default 20, range 1-1000)
        page: Pagination token from previous response's next_page field

    Returns:
        SyncPageCursor[VersionListResponse] with cursor-paginated versions
    """
    ...
```

### Delete Version

```python { .api }
def delete(
    self,
    version: str,
    *,
    skill_id: str,
    **kwargs
) -> VersionDeleteResponse:
    """
    Delete a specific skill version.

    Parameters:
        version: Version identifier
        skill_id: Unique identifier for the skill

    Returns:
        VersionDeleteResponse confirming deletion
    """
    ...
```

## Examples

### Create Simple Skill

```python
from anthropic import Anthropic
from anthropic._utils import file_from_path

client = Anthropic()

# Create skill with SKILL.md
skill = client.beta.skills.create(
    display_title="Weather Analyzer",
    files=[
        file_from_path("SKILL.md"),  # Required: skill description
        file_from_path("weather.py"),  # Optional: implementation files
    ]
)

print(f"Created skill: {skill.id}")
print(f"Display title: {skill.display_title}")
```

### SKILL.md Format

```markdown
# Weather Analyzer

Analyze weather data and provide recommendations.

## Capabilities

- Temperature analysis
- Humidity assessment
- Weather recommendations

## Usage

Call this skill with temperature and humidity values to get weather analysis.
```

### List Skills

```python
# List all custom skills
for skill in client.beta.skills.list(source="custom"):
    print(f"Skill: {skill.display_title} ({skill.id})")

# List Anthropic-provided skills
for skill in client.beta.skills.list(source="anthropic"):
    print(f"Anthropic skill: {skill.display_title}")

# Paginated listing
page_result = client.beta.skills.list(limit=10)
for skill in page_result:
    print(f"Skill: {skill.display_title}")

# Get next page
if page_result.next_page:
    next_page = client.beta.skills.list(limit=10, page=page_result.next_page)
```

### Retrieve Skill

```python
skill = client.beta.skills.retrieve("skill_abc123")
print(f"Name: {skill.display_title}")
print(f"Created: {skill.created_at}")
print(f"Latest version: {skill.latest_version}")
```

### Delete Skill

```python
# Delete entire skill
deleted = client.beta.skills.delete("skill_abc123")
print(f"Deleted skill: {deleted.id}")
```

### Create New Version

```python
# Create new version with updated files
version = client.beta.skills.versions.create(
    skill_id="skill_abc123",
    files=[
        file_from_path("SKILL.md"),  # Updated description
        file_from_path("weather_v2.py"),  # New implementation
    ]
)

print(f"Created version: {version.version}")
print(f"Version ID: {version.id}")
```

### List Versions

```python
# List all versions of a skill
for version in client.beta.skills.versions.list(skill_id="skill_abc123"):
    print(f"Version: {version.version}")
    print(f"Created: {version.created_at}")
    print(f"Status: {version.status}")
    print("---")

# Paginated version listing
versions = client.beta.skills.versions.list(
    skill_id="skill_abc123",
    limit=5
)

for version in versions:
    print(f"Version: {version.version}")

# Get next page
if versions.next_page:
    next_versions = client.beta.skills.versions.list(
        skill_id="skill_abc123",
        limit=5,
        page=versions.next_page
    )
```

### Retrieve Specific Version

```python
version = client.beta.skills.versions.retrieve(
    skill_id="skill_abc123",
    version="v1"
)

print(f"Version: {version.version}")
print(f"Created: {version.created_at}")
```

### Delete Version

```python
# Delete specific version
deleted = client.beta.skills.versions.delete(
    skill_id="skill_abc123",
    version="v1"
)

print(f"Deleted version: {deleted.version}")
```

### Version Management Pattern

```python
# Create skill
skill = client.beta.skills.create(
    display_title="Data Processor",
    files=[file_from_path("SKILL.md"), file_from_path("processor_v1.py")]
)

print(f"Created skill {skill.id} with version {skill.latest_version}")

# Update skill with new version
v2 = client.beta.skills.versions.create(
    skill_id=skill.id,
    files=[file_from_path("SKILL.md"), file_from_path("processor_v2.py")]
)

print(f"Created version {v2.version}")

# List all versions
versions = list(client.beta.skills.versions.list(skill_id=skill.id))
print(f"Total versions: {len(versions)}")

# Rollback by deleting latest version (if needed)
if len(versions) > 1:
    latest = versions[0]
    client.beta.skills.versions.delete(
        skill_id=skill.id,
        version=latest.version
    )
    print(f"Rolled back to previous version")
```

### Multi-File Skill

```python
# Create skill with multiple files
skill = client.beta.skills.create(
    display_title="Advanced Calculator",
    files=[
        file_from_path("SKILL.md"),
        file_from_path("calculator.py"),
        file_from_path("math_utils.py"),
        file_from_path("constants.py"),
    ]
)

print(f"Created skill with {len(skill.files)} files")
```

### Async Skills Operations

```python
import asyncio
from anthropic import AsyncAnthropic

async def main():
    client = AsyncAnthropic()

    # Create skill asynchronously
    skill = await client.beta.skills.create(
        display_title="Async Processor",
        files=[file_from_path("SKILL.md")]
    )

    # List skills
    async for skill in client.beta.skills.list():
        print(f"Skill: {skill.display_title}")

    # Create version
    version = await client.beta.skills.versions.create(
        skill_id=skill.id,
        files=[file_from_path("SKILL.md")]
    )

    print(f"Created version: {version.version}")

asyncio.run(main())
```

### Error Handling

```python
from anthropic import APIError, BadRequestError

try:
    # Create skill
    skill = client.beta.skills.create(
        display_title="Test Skill",
        files=[file_from_path("SKILL.md")]
    )
except BadRequestError as e:
    if "SKILL.md" in str(e):
        print("Error: SKILL.md file is required at root")
    else:
        print(f"Invalid request: {e.message}")
except APIError as e:
    print(f"API error: {e.message}")

# Validate skill exists before operations
try:
    skill = client.beta.skills.retrieve("skill_abc123")
    print(f"Skill exists: {skill.display_title}")
except APIError:
    print("Skill not found")
```

## File Requirements

### SKILL.md File

- **Required**: Every skill must include a SKILL.md file at the root
- **Purpose**: Describes the skill's capabilities and usage
- **Format**: Markdown file with skill documentation
- **Location**: Must be in the root directory with other skill files

### File Organization

- All skill files must be in the same top-level directory
- No subdirectories allowed
- Include all necessary implementation files
- Keep files focused and modular

### Example Structure

```
skill_files/
  ├── SKILL.md           # Required: skill description
  ├── main.py            # Optional: implementation
  ├── utils.py           # Optional: utilities
  └── constants.json     # Optional: configuration
```

## Best Practices

### 1. Clear SKILL.md Documentation

Write comprehensive SKILL.md files:
```markdown
# Skill Name

Clear one-line description.

## Capabilities

- Bullet list of what the skill does
- Specific use cases

## Usage

How to invoke and use the skill.

## Requirements

Any prerequisites or constraints.
```

### 2. Version Management

- Create new versions for updates instead of deleting and recreating
- Keep version history for rollback capability
- Document changes in SKILL.md for each version

### 3. Naming Conventions

Use descriptive display titles:
```python
# Good
display_title="Weather Data Analyzer"

# Bad
display_title="skill1"
```

### 4. File Organization

Keep related functionality together:
```python
files=[
    file_from_path("SKILL.md"),
    file_from_path("analyzer.py"),     # Main logic
    file_from_path("data_utils.py"),   # Helper functions
    file_from_path("config.json"),     # Configuration
]
```

### 5. Error Handling

Always validate operations:
```python
try:
    skill = client.beta.skills.retrieve(skill_id)
    # Use skill
except APIError:
    # Handle missing skill
    pass
```

### 6. Pagination

Use cursor pagination for large lists:
```python
page = None
while True:
    results = client.beta.skills.list(limit=100, page=page)
    for skill in results:
        process_skill(skill)

    if not results.next_page:
        break
    page = results.next_page
```

## Limitations and Considerations

### File Constraints

- All files must be in same directory (no subdirectories)
- SKILL.md required at root
- File size limits apply (check API documentation)

### Version Limits

- Check API for maximum versions per skill
- Old versions remain until explicitly deleted
- Deleting a skill deletes all versions

### Source Filtering

- "custom": User-created skills
- "anthropic": Anthropic-provided skills
- Use source filter to separate your skills from system skills

### Pagination

- Default page size: 20
- Maximum page size: 100 (skills), 1000 (versions)
- Use next_page token for cursor-based pagination

## See Also

- [Beta Overview](./index.md) - Overview of all beta features
- [Files API](./files.md) - File upload and management
- [Beta Batches](./batches.md) - Batch processing with beta features
- [Message Features](./message-features.md) - Beta message enhancement features
