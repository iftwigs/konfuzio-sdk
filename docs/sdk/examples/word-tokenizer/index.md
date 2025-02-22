## Getting Word Bounding Box (BBox) for a Document

In this tutorial, we will walk through how to extract the bounding box ([BBox](https://dev.konfuzio.com/sdk/sourcecode.html#bbox)) 
for words in a Document, rather than for individual characters, using the Konfuzio SDK. This process involves the use of 
the `WhitespaceTokenizer` from the Konfuzio SDK to tokenize the Document and identify word-level Spans, which can then 
be visualized or used to extract BBox information.

### Prerequisites

- You will need to have the Konfuzio SDK installed.
- You should have access to a Project on the Konfuzio platform.

### Preview of Result

<img src="https://github.com/konfuzio-ai/konfuzio-sdk/assets/2879188/5f7a8501-cd89-487d-a332-0703f3c35fc8" data-canonical-src="https://github.com/konfuzio-ai/konfuzio-sdk/assets/2879188/5f7a8501-cd89-487d-a332-0703f3c35fc8" width="200" height="400" />

### Steps

1. **Import necessary modules**:

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start import
      :end-before: end import
      :dedent: 4

2. **Initialize your Project**:

   This involves creating a Project instance with the appropriate ID.

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start project
      :end-before: end project
      :dedent: 4

3. **Retrieve a Document from your Project**:

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start document
      :end-before: end document
      :dedent: 4

4. **Create a copy of your Document without Annotations**:

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start copy
      :end-before: end copy
      :dedent: 4

5. **Tokenize the Document**:

   This process involves splitting the Document into word-level Spans using the `WhitespaceTokenizer`.

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start tokenize
      :end-before: end tokenize
      :dedent: 4

6. **Visualize all word-level Annotations**:

   After getting the bounding box for all Spans, you might want to visually check the results to make sure the bounding 
   boxes are correctly assigned. Here's how you can do it:

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start image
      :end-before: end image
      :dedent: 4

   .. image:: /sdk/examples/word-tokenizer/word-bboxes.png

   This will display an image of the Document with all word-level Annotations. The image may look a bit messy with all 
   the Labels.

7. **Get bounding box for all Spans**:

   You can retrieve bounding boxes for all word-level Spans using the following code:

   .. literalinclude:: /sdk/boilerplates/test_word_bboxes.py
      :language: python
      :start-after: start spans
      :end-before: end spans
      :dedent: 4

   Each bounding box (`Bbox`) corresponds to a particular word and is characterized by four coordinates: x0 and y0 define 
   the bottom-left corner, while x1 and y1 indicate the top-right corner. These coordinates detail the bounding box's 
   location and size on the Document Page.

