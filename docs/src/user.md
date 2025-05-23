# User Documentation
## Admin Page
![alt text](../assets/images/sidebar.png)

### Description of The Admin Sidebar
1. Filter, to search left sidebar.
2. Sidebar menu, click to show the record.
3. Toggle hide/show sidebar


## Add Crawler
1. Select Crawlers on th left sidebar.

![alt text](../assets/images/image-1.png)

2. On the right sidebar, click **ADD CRAWLER**.

![alt text](../assets/images/image-2.png)

3. Fill the Name, Description, Province, Image Type, and Resolution. Bbox will be populated automatically from selected Province.

![alt text](../assets/images/image-0.png)

4. Click Save at the bottom of the page

![alt text](../assets/images/image-3.png)

## Run Periodic Task
Periodic task has been set to run automatically on the 1st date every month. It will process data from previous month. Example: Periodic task that runs on March 1st 2025 will process data from February 2025. 

### Run All Crawler
Follow these steps to run periodic task manually:
1. Go to **Periodic tasks** menu on the left sidebar. You can also search it.

![alt text](../assets/images/image-4.png)

2. Click on the checkbox to the left of **update_stored_data_monthly**.
3. On the **Action** dropdown, select **Run selected tasks**.
4. Click **Go**.

![alt text](../assets/images/image-6.png)
5. A success message should be shown.

![alt text](../assets/images/image-7.png)


### Run selected crawler
Follow these steps to run periodic task manually:
1. Go to **Crawlers** menu on the left sidebar. You can also search it.
2. Select the Crawlers that you want to run.
3. Click dropdown, select **Run crawler for last month**.
4. Click **Go**

![alt text](../assets/images/run-crawler-1.png)

5. Success essage should be shown

![alt text](../assets/images/run-crawler-2.png)

### Show Crawler Progress
1. Go to **Crawl progresses** menu on the left sidebar. You can also search it.

2. You can see the progress

![alt text](../assets/images/crawler-progress.png)

## Checking Task Logs
1. Go to **Task logs** menu on the left sidebar. You can also search it.

## Checking Task Outputs
### Using Admin Page
Go to **Task outputs** menu on the left sidebar. You can also search it.
### Using API
Make request to this URL to get paginated results of Task Outputs.

http://10.150.16.178:8888/api/task-outputs/

You can also filter the results by **monitoring_type__name**, **from_date**, **to_date**, **bbox**, **page**, and **page_size**.

http://10.150.16.178:8888/api/task-outputs/?monitoring_type__name=AWEI&from_date=2025-03-01&to_date=2025-03-31&bbox=18.8710767506562824,-33.8205932191388783,18.8736486550678428,-33.8184169923290980&page=1&page_size=10&page_size=100&page=1

It will give you AWEI output between March 1st 2025 to March 31st 2025, for the specified bbox, with 100 records on each page, and show records on page 1 (if there are multiple pages of the result).