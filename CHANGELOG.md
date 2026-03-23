# [1.6.0](https://github.com/PAzter1101/patchnotes/compare/v1.5.1...v1.6.0) (2026-03-23)


### Features

* **admin:** add auto-publish toggle and improve post workflow ([ec7f1b9](https://github.com/PAzter1101/patchnotes/commit/ec7f1b9ebb75cbb7c8cdf7ce03328964fcddd744))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.6.0`
- **Docker Hub**: `pazter1101/patchnotes:1.6.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.6.0
```

## [1.5.1](https://github.com/PAzter1101/patchnotes/compare/v1.5.0...v1.5.1) (2026-03-23)


### Bug Fixes

* readme ([00295b8](https://github.com/PAzter1101/patchnotes/commit/00295b8dbb293ef8501ff90f3b180ede37c88b23))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.5.1`
- **Docker Hub**: `pazter1101/patchnotes:1.5.1`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.5.1
```

# [1.5.0](https://github.com/PAzter1101/patchnotes/compare/v1.4.0...v1.5.0) (2026-03-23)


### Features

* **admin:** reorganize navigation and add prompts/repos management ([a6b4ede](https://github.com/PAzter1101/patchnotes/commit/a6b4ede8b8fdc92fc04bf05f0ab9ada4ed04fa44))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.5.0`
- **Docker Hub**: `pazter1101/patchnotes:1.5.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.5.0
```

# [1.4.0](https://github.com/PAzter1101/patchnotes/compare/v1.3.0...v1.4.0) (2026-03-22)


### Features

* **admin:** add settings page and improve generation workflow ([d16b475](https://github.com/PAzter1101/patchnotes/commit/d16b475615f8c0e82057db6c5ef77d4c49133276))
* **helm:** add init containers and security context for deployments ([a60e744](https://github.com/PAzter1101/patchnotes/commit/a60e74412751898fbd270c7f5c1acb8341d09e8b))

## Docker Images

- **GitHub Container Registry**: `ghcr.io/pazter1101/patchnotes:1.4.0`
- **Docker Hub**: `pazter1101/patchnotes:1.4.0`

### Usage
```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v ./config.yml:/config.yml \
  -v ./prompts:/prompts \
  -v ./output:/output \
  ghcr.io/pazter1101/patchnotes:1.4.0
```

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
