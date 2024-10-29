# **Health Risk API**

## **Chatbot Data Integration & API Synchronization**

### **Project Overview**  
This project demonstrates the integration of user demographic and lifestyle data collected by a chatbot into a backend system built with **FastAPI**. The backend processes this data, generates **mock risk scores for insurance and diabetes**, stores the data in a **SQLite database**, and provides **API endpoints** for data retrieval. This project emphasizes **API communication, risk calculations**, and **error logging** to ensure a seamless flow between the chatbot and backend system.

---

## **Goals**  
- Retrieve user data from **Google Sheets**.  
- Process and store data in the backend API.  
- Generate **mock insurance and diabetes risk scores** based on provided data.  
- Implement **error handling** and **logging** to maintain traceability.

---

## **Table of Contents**  
- [Features](#features)  
- [Setup Instructions](#setup-instructions)  
- [Usage](#usage)  
- [API Endpoints](#api-endpoints)  
- [Technologies Used](#technologies-used)  
- [Conclusion](#conclusion)

---

## **Features**
- **Data Retrieval**: Fetches entries from a **Google Sheet** automatically.  
- **API Communication**: FastAPI handles demographic and lifestyle data submissions through endpoints.  
- **Risk Score Calculation**: Generates **mock insurance and diabetes risk scores** using the provided data.  
- **Data Storage**: Saves user data in a **SQLite database** for future analysis and retrieval.  
- **Error Handling and Logging**: Tracks and logs errors and API interactions to ensure smooth operations.  

---

## **Setup Instructions**

1. **Clone the Repository**:  
   Open your terminal and run the following command:
   ```bash
   git clone https://github.com/Himbaza123h/Health-Risk-API
   cd Health-Risk-API
   ```

2. **Create a Virtual Environment**:  
   It's recommended to use a virtual environment to manage dependencies.  
   Run the following commands:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

3. **Install Dependencies**:  
   Install the required packages using:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:  
   Create a `.env` file in the project directory with the following contents:
   ```plaintext
   DATABASE_URL=sqlite:///./database/your_database_name
   GOOGLE_SHEET_ID=your_google_sheet_id
   GOOGLE_SHEET_API_KEY=your_api_key
   APP_NAME=Health Risk API
   APP_VERSION=1.0.0
   ENVIRONMENT=development
   ```

5. **Initialize the Database**:  
   Run the following command to create the database tables:
   ```bash
   python initialize_db.py
   ```

6. **Run the API**:  
   Start the FastAPI server using:
   ```bash
   python run.py
   ```

7. **Access the API Documentation**:  
   Visit the API documentation at `http://127.0.0.1:8000/docs` in your web browser. 

---

## **API Endpoints**

### **Base Routes**
- **GET /**: Welcome message and basic information about the API.

### **User Data Endpoints**
- **POST /user/**: Create new user data and calculate risk scores.
- **GET /user/**: Retrieve a list of all user data.
- **DELETE /user/**: Delete all user data from the database.

### **Synchronization Endpoints**
- **GET /sync/test_connection**: Test connection to Google Sheets.
- **POST /sync/to_sheets**: Sync data from the database to Google Sheets.
- **POST /sync/from_sheets**: Sync data from Google Sheets to the database.
- **GET /sync/status**: Get the status of the last sync operation.
- **POST /sync/**: Sync data in both directions.

### **Risk Scores Endpoints**
- **POST /risk_scores/**: Calculate and return risk scores based on user data.

---

## **Technologies Used**
- **FastAPI**: For building the API.
- **SQLAlchemy**: For database interactions.
- **SQLite**: For storing user data.
- **Google Sheets API**: For retrieving data from Google Sheets.
- **Logging**: For error handling and monitoring.

---

## **Conclusion**
This Health Risk API provides a robust framework for integrating user data from a chatbot, calculating health risks, and syncing data with Google Sheets. The implementation emphasizes error handling and logging, ensuring reliable and maintainable operations.
