# CSV Parser

Backend system for uploading CSV files, extracting information, processing data and storing it in a database.

### Features
* Extract, compress and store image
* Google Cloud Storage integration for storing images
* Utilized background tasks for processing data


## Clone

* Use `git clone` to clone the repo
```bash
git clone git@github.com:FumaxIN/csv-parser.git
```

## Run

* Create a virtual environment
```bash
python -m venv ./venv
source venv/bin/activate
```

* Install the requirements
```bash
  pip install -r requirements.txt
```

* Run server
```bash
uvicorn main:app --reload
```

## Endpoints

* **Upload a file**
    ```
    POST: /api/v1/upload
    ```
    Request body:
    ```
    {
      "csv_file": [upload_file]
      "webhook_url": "[optional]"
    }
    ```
  A `csv_upload_id` will be returned.

* **Get status for processing of uploaded csv**
    ```
    GET: /status/{csv_upload_id}
    ```
  
* **Download output csv**
    ```
    GET: /download/{csv_upload_id}
    ```
  

## Async worker functions

* **async def upload_csv(....)**
    * Validates CSV file and creates a CSVupload object.
    * Extracts product information from csv file.
    * Creates an object for each product.
    * Calls `process_product(...)` as background task for each product.
    * Returns the `csv_upload_id` to track the status.


* **async def process_product(....)**
    * Extracts image from URL and compresses it using Pillow.
    * Uploads the image to Google Cloud Storage.
    * Updates product object's `output_image_urls` to that of cloud links.
    * Calls `send_webhook(...)` if webhook_url is provided.


* **async def get_status(csv_upload_id)** 
    * Returns the status of the CSV upload.


* **async def download_csv(csv_upload_id)**
    * Fetches all the products associated with the CSV upload.
    * Creates a new CSV file with the product information.
    * Returns the csv file.
