# Compario: AI-Powered Price Comparison 🛒

## Project Overview

Compario is an AI-driven web application designed to solve the inefficiency of manually searching for the best product deals across multiple e-commerce platforms. 

Developed over an 8-week agile timeline during the Infosys Springboard Virtual Internship 6.0, this project enables users to upload a product image, automatically identifies the item, and scans various online stores to find the lowest available price. 

By aggregating real-time data from platforms like Amazon, Flipkart, and Snapdeal, Compario provides consumers with significant cost savings and a highly convenient, time-efficient shopping experience.

## Architecture & Workflow

The system architecture seamlessly integrates machine learning, real-time web scraping, and a robust frontend interface into a unified platform. 

* **Visual Product Recognition:** Users upload product images (JPEG, PNG, JPG), which are preprocessed using techniques like resizing and noise reduction before being analyzed by a fine-tuned Vision Transformer (ViT) model implemented via PyTorch. 
* **Automated Feature Mapping:** The AI model converts visual data into relevant product keywords (e.g., recognizing a photo as a "Bluetooth Speaker") with high accuracy, completely eliminating the need for manual text input. 
* **Real-Time Data Aggregation:** The recognized keywords are passed to a scraping engine that utilizes BeautifulSoup and Selenium to extract pricing, delivery details, ratings, and reviews simultaneously from multiple retailers. 
* **Interactive Analytics Dashboard:** The Streamlit backend processes and sorts the collected data, displaying a visually clear, sortable comparison table while highlighting the absolute lowest price for immediate action.

## Technical Stack & Challenges Overcome

Building this full-stack application required integrating a diverse set of modern Python libraries and handling complex data pipelines. 

* **Core Technologies:** The frontend and backend are powered entirely by Streamlit and Python, while local data persistence (such as user accounts and search history) is managed securely through a serverless SQLite3 database. 
* **AI & Scraping Ecosystem:** The object recognition leverages PyTorch and the Transformers library, while data extraction relies heavily on Selenium, WebDriver-Manager, BeautifulSoup4, lxml, and Regex. 
* **Navigating Site Structures:** Inconsistent HTML layouts across different e-commerce sites were navigated by implementing robust, site-specific parsing scripts. 
* **Rate Limiting Avoidance:** Issues with CORS and dynamic site restrictions were successfully resolved by optimizing API routing and introducing strategic request delays to ensure consistent data retrieval.

## Local Installation Setup

To run this project locally, clone the repository and execute the following commands in your terminal:

```bash
git clone [https://github.com/ShivadityaMondal/infosys-internship-project.git](https://github.com/ShivadityaMondal/infosys-internship-project.git)
cd infosys-internship-project
pip install -r requirements.txt
streamlit run app.py
