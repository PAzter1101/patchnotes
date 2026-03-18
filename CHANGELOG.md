# [1.1.0](https://github.com/PAzter1101/patchnotes/compare/v1.0.0...v1.1.0) (2026-03-18)


### Features

* **config,git-diff:** add tag-based diff mode and timezone support ([36ee099](https://github.com/PAzter1101/patchnotes/commit/36ee099a90b16020c3d8b40adcc84b256d66708e))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.1.0`
- **Docker Hub**: `pazter1101/patchnotes:1.1.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.1.0
```

# 1.0.0 (2026-03-18)


### Features

* add synthesis, review, and improved configuration pipeline ([ab68f4d](https://github.com/PAzter1101/patchnotes/commit/ab68f4d1a073a6986623f3ab1c909c584324b85c))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.0.0`
- **Docker Hub**: `pazter1101/patchnotes:1.0.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.0.0
```
