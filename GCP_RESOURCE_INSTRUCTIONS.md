# How to Increase Cloud Run Service Resources

A slow database connection in the Cloud Run environment is likely causing request timeouts (502 errors). This is often due to the default container having insufficient CPU and memory.

Increasing the resources allocated to your Cloud Run service is the most likely solution. Here are two methods to do this.

---

## Method 1: Using the Google Cloud Console (Web UI)

This is often the most straightforward way to manage your service's configuration.

1.  **Navigate to Cloud Run:**
    *   Open the [Google Cloud Console](https://console.cloud.google.com/).
    *   In the navigation menu (☰), go to `Serverless` > `Cloud Run`.

2.  **Select Your Service:**
    *   You will see a list of your Cloud Run services. Click on the name of your service (e.g., `proposal-generator` or `proposal-drafter-backend`).

3.  **Edit and Deploy a New Revision:**
    *   At the top of the service details page, click the **"EDIT & DEPLOY NEW REVISION"** button.

4.  **Adjust Resources:**
    *   On the configuration page, scroll down to the **"Container(s)"** section.
    *   Find the **"CPU and memory allocation"** settings.
    *   **Memory:** Click the dropdown and select a higher value. We recommend starting with **`2 GiB`**.
    *   **CPU:** Click the dropdown and select **`2`** vCPUs.

5.  **Deploy the Changes:**
    *   Scroll to the bottom of the page and click the **"DEPLOY"** button.

Cloud Run will now deploy a new revision of your service with the increased resources. Once it's ready, you can try accessing your application again and monitor the logs to see if the database connection time has improved.

---

## Method 2: Using the `gcloud` Command Line

This method is faster if you are comfortable with the command line.

### Command

Run the following command in your terminal after replacing the placeholders with your specific service details.

```bash
gcloud run services update YOUR_SERVICE_NAME \
    --memory=2Gi \
    --cpu=2 \
    --region=europe-west1 \
    --project=YOUR_PROJECT_ID
```

### Command Breakdown

*   `gcloud run services update YOUR_SERVICE_NAME`: This tells `gcloud` that you want to modify an existing Cloud Run service. You must replace `YOUR_SERVICE_NAME` with the actual name of your service.
*   `--memory=2Gi`: This flag sets the amount of memory allocated to your container. `2Gi` stands for 2 Gibibytes.
*   `--cpu=2`: This flag sets the number of virtual CPUs allocated. Allocating 2 vCPUs ensures that the CPU is not throttled during startup and request processing.
*   `--region=europe-west1`: You need to specify the region where your service is deployed.
*   `--project=YOUR_PROJECT_ID`: You need to specify the Google Cloud Project ID that owns the service.

---

Applying one of these methods should resolve the performance issue that is causing the 502 errors.
