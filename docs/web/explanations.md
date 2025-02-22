.. meta::
   :description: Use this section for explaining how the software works, without completing a specific task (see Tutorials).

# Explanations

*Explanation is discussion that clarifies and illuminates a particular topic.*
*Explanation is understanding-oriented.*

## Architectural Overview

The diagram illustrates the components of a Konfuzio Server deployment. Optional components are represented by dashed lines. The numbers in brackets represent the minimal and maximal container count per component.

.. mermaid::

   graph TD
      classDef client fill:#D5E8D4,stroke:#82B366,color:#000000;
      classDef old_optional fill:#E1D5E7,stroke:#9673A6,color:#000000;
      classDef optional fill:#DAE8FC,stroke:#6C8EBF,color:#000000,stroke-dasharray: 3 3;
      
      ip("Loadbalancer / Public IP")
      smtp("SMTP Mailbox")
      a("Database")
      b("Task Queue")
      c("File Storage")
      worker("Generic Worker (1:n)")
      web("Web & API (1:n)")
      beats("Beats Worker (1:n)")
      mail("Mail-Scan (0:1)")
      
      %% Outside references
      smtp <-- Poll emails --> mail
      ip <--> web
      
      %% Optional Containers
      ocr("OCR (0:n)")
      segmentation("Segmentation (0:n)")
      summarization("Summarization (0:n)")
      flower("Flower (0:1)")
      
      %% Server / Cluster
      h0("Server 1")
      h1("Server 2")
      h2("Server 3")
      h3("Server 4")
      h4("Server 5")
      i("...")
      j("Server with GPU")

      subgraph all["Private Network"]
      subgraph databases["Persistent Container / Services"]
      a
      c
      b
      end
      subgraph containers["Stateless Containers"]
      mail
      web
      flower
      worker
      beats
      subgraph optional["Optional Containers"]
      ocr
      segmentation
      summarization
      end
      end
      subgraph servers["Server / Cluster"]
      h0
      h1
      h2
      h3
      h4
      i
      j
      end    
      worker <--> databases
      worker -- Can delegate tasks--> optional
      worker -- "Can process tasks"--> worker
      web <--> databases
      web <--> flower
      flower <--> b
      mail <--> databases
      beats <--> databases
      containers -- "Operated on"--> servers
      databases -- "Can be operated on"--> servers
      end
      
      click flower "/web/on_premises.html#optional-6-use-flower-to-monitor-tasks"
      click web "/web/on_premises.html#start-the-container"
      click worker "/web/on_premises.html#start-the-container"
      click ocr "/web/on_premises.html#optional-7-use-azure-read-api-on-premise"
      click segmentation "/web/on_premises.html#optional-8-install-document-segmentation-container"
      click summarization "/web/on_premises.html#optional-9-install-document-summarization-container" 
      
      class flower optional
      class ocr optional
      class mail optional
      class ocr optional
      class segmentation optional
      class summarization optional
      class h1 optional
      class h2 optional
      class h3 optional
      class h4 optional
      class i optional
      class j optional



## OCR Processing

After [uploading a document](https://help.konfuzio.com/modules/documents/index.html#upload-new-documents), depending on
how your project was set up, the document is automatically queued and processed by our OCR. In the below breakdown we
try to demystify this process, and give you some insight into all the steps which happen during OCR processing.

### Project settings

We first look at the projects settings to see what base settings have been set up for your documents.

1. **Chosen OCR engine**
    1. easy
    2. precise

2. **Chosen processing type**
    1. OCR
    2. Embedding
    3. Embedding and OCR

3. **Chosen auto-rotation option**

   (Only available for precise OCR engine)

    1. None
    2. Rounded
    3. Exact

### File pre-processing

During file upload, after the Project settings have been evaluated, we look at the file:

1. We check if the filetype is [supported](https://dev.konfuzio.com/web/api-v3.html#supported-file-types).
2. We check if the file is valid and/or corrupted.
3. If the file is corrupted, some repairing is attempted.
4. We check if the filetype provides embeddings.
5. We check if the project enforces OCR.
6. We then conduct OCR on the file.
7. We check if the image is angled.
8. We create thumbnails per page.
9. We create images per page.


### OCR Text extraction

During evaluation of both project settings and file, we also process OCR extraction

1. We use the chosen engine on the pre-processed file.
    1. If "Embedding and OCR" is chosen, internally we check which processing type is the most suitable, and use either
       Embedding or OCR
    2. Depending on chosen processing type, some pre-processing may be done:
        1. Convert non-PDF Documents to a [PDF](https://dev.konfuzio.com/web/api.html#pdfs) 
           that is being used here
        2. Convert PDF to text (in case of embeddings)
    3. If some sort of PDF corruption is detected, within our ability we attempt to repair the PDF
    4. If the PDF or TIFF is multi page (and valid) we split the document in pages and process each page separately
2. We check whether auto-rotation was chosen when the precise OCR engine is used]
    1. If rounded angle correction was chosen, we rotate the image to the nearest 45/90 degrees.
    2. If exact angle rotation was chosen, we rotate the image at its exact angle rotation value.
3. We attempt to extract the text from (either ocr, embedded or both)
    1. OCR may fail because text on the document is technically unreadable, the file is corrupted or empty and cannot be
       repaired
    2. OCR may fail because engine does not support the text language

Finally, we return you the extracted text.

## Background processes

Processes within our server are distributed between
[Celery](https://docs.celeryq.dev/en/stable/) [workers](https://docs.celeryq.dev/en/stable/userguide/workers.html)
between several [tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html). Together this creates the definition 
of Servers internal workflow. Below the individual tasks of the Server's workflow are described in order of their 
triggered events. Tasks are run in parallel queue's which are grouped in celery chords. While some tasks in each queue 
run in parallel, some tasks are still dependent on others. And no next queue will start until all tasks in the queue are finished. 
More on Celery workflows can be found here: https://docs.celeryq.dev/en/stable/userguide/canvas.html

### Queue's


| id  | queue-name       |                   description                   |
|-----|------------------|:-----------------------------------------------:|
| 1   | `ocr`            |             ocr and post ocr tasks              |
| 2   | `processing`     |               non dependent tasks               |
| 3   | `categorize`     |              categorization tasks               |
| 4   | `extract`        |              extraction after ocr               |
| 5   | `finalize`       | end queue after OCR and extraction has occurred |
| 6   | `training`       |              queue for AI training              |
| 7   | `training_heavy` |       queue for RAM intensive ai training       |
| 8   | `evaluation`     |             queue for AI evaluation             |



### Celery Tasks

#### Document tasks

Series of events & tasks triggered when uploading a Document

| Queue | task id | task name                    | description                                                                                                     | default time limit |
|-------|---------|------------------------------|-----------------------------------------------------------------------------------------------------------------|--------------------|
| 1, 2  | 1       | page_ocr                     | Apply OCR to the documents page(s).                                                                             | 10 minutes         |
| 1, 2  | 2       | page_image                   | Create png image for a page. If a PNG was submitted or already exists it will be returned without regeneration. | 10 minutes         |
| 1     | 3       | set_document_text_and_bboxes | Collect the result of the pages OCR (OCR from task_id #1) and set text & bboxes.                                | 1 minute           |
| 3     | 4       | categorize                   | Categorize the document.                                                                                        | 3 minutes          |
| 4     | 5       | document_extract             | Extract the document using the AI models linked to the Project.                                                 | 60 minutes         |
| 5     | 6       | build_sandwich               | Generates the pdfsandwich for a submitted PDF                                                                   | 30 minutes         |
| 5     | 7       | generate_entities            | Generate entities for a document which are shown in the labeling tool.                                          | 60 minutes         |
| 5     | 8       | set_labeling_available       | Sets the document available for labeling                                                                        | 10 minutes         |
| 5     | 9       | get_hocr                     | Get hOCR representation for bboxes (bboxes from task_id #3).                                                    | 5 minutes          |

The overall time to complete all tasks related to a Document (DOCUMENT_WORKFLOW_TIME_LIMIT) is restricted to 2 hours.

#### Extraction & Category AI Training

##### Extraction AI

Series of events triggered when training an extraction AI

| Queue   | task id | task name           | description                                                                                                     | default time limit |
|---------|---------|---------------------|-----------------------------------------------------------------------------------------------------------------|--------------------|
| 2       | 1       | page_image          | Create png image for a page. If a PNG was submitted or already exists it will be returned without regeneration. | 10 minutes         |
| 6, 7    | 1       | train_extraction_ai | Start the training of the Ai model.                                                                             | 20 hours           |
| 4       | 2       | document_extract    | Extract the document using the AI models linked to the Project.                                                 | 60 minutes         |
| 6, 7, 8 | 3       | evaluate_ai_model   | Evaluate the trained Ai models performance.                                                                     | 60 minutes         |

##### Category AI

Series of events triggered when training a Categorization AI

| Queue      | task id | task name         | description                                                                                                     | default time limit |
|------------|---------|-------------------|-----------------------------------------------------------------------------------------------------------------|--------------------|
| 8          | 2       | train_category_ai | Start the training of the categorization model.                                                                 | 10 hours           |
| 8, 3       | 3       | categorize        | Run the categorization against all Documents in the its category.                                               | 3 minutes          |
| 6, 7, 8, 3 | 4       | evaluate_ai_model | Evaluate the categorization Ai models performance.                                                              | 60 hours           | 

