# Health Risk API

# Chatbot Data Integration & API Synchronization

## Project Overview
This project simulates the integration of user demographic and lifestyle data collected by a chatbot into a backend system. The backend processes this data to generate mock risk scores for insurance and diabetes, stores the data in a SQLite database, and provides an API for data retrieval. This solution is designed to demonstrate effective data handling, API communication, and backend functionality.

## Goals
- Retrieve user data from a Google Sheet.
- Process and store the data in a backend API.
- Generate mock risk scores for insurance and diabetes.
- Implement error handling and logging for API interactions.

## Table of Contents
- [Features](#features)
- [Setup Instructions](#setup-instructions)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Technologies Used](#technologies-used)
- [Conclusion](#conclusion)

## Features
- **Data Retrieval**: Automatically fetches new entries from a Google Sheet.
- **API Communication**: Accepts demographic and lifestyle data through a FastAPI endpoint.
- **Risk Score Calculation**: Generates mock insurance and diabetes risk scores based on user data.
- **Data Storage**: Saves user data in a SQLite database for future retrieval.
- **Error Handling and Logging**: Logs errors and interactions to ensure traceability.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Himbaza123h/Health-Risk-API
   cd Health-Risk-API

