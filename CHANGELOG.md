# [1.3.0](https://github.com/PAzter1101/patchnotes/compare/v1.2.1...v1.3.0) (2026-03-22)


### Features

* add admin panel, mkdocs blog, and helm chart ([277d3a5](https://github.com/PAzter1101/patchnotes/commit/277d3a5f342f401ccf4381e987764e626e42acd3))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.3.0`
- **Docker Hub**: `pazter1101/patchnotes:1.3.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.3.0
```

# [1.2.0](https://github.com/PAzter1101/patchnotes/compare/v1.1.0...v1.2.0) (2026-03-22)


### Features

* **config,git-diff:** add repo-level pattern overrides ([5eeb1b4](https://github.com/PAzter1101/patchnotes/commit/5eeb1b4e0e78274dc927c55eaa7f0f9bf398f42a))
* **helm,docker,ci:** add helm chart and multi-image docker builds ([b4e1615](https://github.com/PAzter1101/patchnotes/commit/b4e1615de448ce827abf166bea31133e99195f96))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.2.0`
- **Docker Hub**: `pazter1101/patchnotes:1.2.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.2.0
```

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
