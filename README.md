# CV Builder Backend

## Description
This is the backend of the CV Builder app, developed with FastAPI. It handles authentication, email verification, and processes API requests for generating CVs and cover letters. The backend is hosted on Railway.

## How to Use the Backend

1. **Visit the API Documentation**:  
   Access the API documentation and test the endpoints by navigating to [**API Docs**](https://cv-builder-backend-production.up.railway.app/docs).

2. **Authentication**:  
   The backend supports user registration with email verification. You can register a user and verify their email through the API.

3. **CV Generation**:  
   Users can generate CVs by passing in their data, which will be processed and returned in a predefined template format.

4. **Cover Letter Generation**:  
   Although the feature is not yet available on the hosted version, it will allow users to generate cover letters based on the CV data.

5. **Exporting CVs**:  
   The API will provide CVs in both PDF and DOC formats, ready for download.

## Technologies
- FastAPI
- Python 3.10+
- FastAPI Mail (for email verification)
- OpenAI API (for generating cover letters)
- PostgreSQL (or your preferred database)

## Deployment
- **Backend**: Deployed on **Railway**. You can access the backend at [**CV Builder Backend**](https://cv-builder-backend-production.up.railway.app/).
