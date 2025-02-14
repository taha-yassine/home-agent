# Home Agent for Home Assistant

Home Agent is an AI module for Home Assistant that adds powerful conversational and automation capabilities to your smart home. It leverages agentic LLMs to handle and execute tasks.

## Overview

The project consists of two main parts:

2. **Add-on**: Manages AI models and provides advanced orchestration capabilities
1. **Custom Component**: Integrates directly with Home Assistant to handle conversations and state management

## Features

Features:
- [x] Basic conversation interception through Home Assistant
- [x] Basic tool usage
- [ ] Smart conversation routing and processing
- [ ] Interactive UI
- [ ] Conversation history and analytics
- [ ] Token usage monitoring
- [ ] KV caching and preloading
- [ ] RAG-based context management

## Installation

### Prerequisites
- Home Assistant instance (Core, OS, or Container)
- Add-on support enabled (for Home Assistant OS or supervised installations)

### Custom Component Installation
1. Copy the `custom_component` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant
3. Add the integration through the Home Assistant UI

### Add-on Installation
1. Add this repository to your Home Assistant Add-on Store
2. Install the Home Agent Add-on
3. Configure the add-on settings
4. Start the add-on

## Configuration

Detailed configuration documentation coming soon.

## Development

This project is under active development.

## License

[License details to be added]
