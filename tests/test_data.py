"""Validate data functions."""
import glob
import logging
import os
import unittest

import pytest

from konfuzio_sdk.data import (
    Project,
    Annotation,
    Document,
    Label,
    AnnotationSet,
    LabelSet,
    Data,
    Span,
    download_training_and_test_data,
)
from konfuzio_sdk.utils import is_file, get_default_label_set_documents, separate_labels

logger = logging.getLogger(__name__)

TEST_PROJECT_ID = 46
TEST_DOCUMENT_ID = 44823


class TestOfflineDataSetup(unittest.TestCase):
    """Test data features without real data."""

    def test_to_add_label_to_Project(self):
        """Add one Label to a Project."""
        prj = Project(id_=None)
        label = Label(project=prj)
        prj.add_label(label)
        self.assertEqual([label], prj.labels)

    def test_to_add_label_twice_to_a_project(self):
        """Add the same Label twice to a Project."""
        prj = Project(id_=None)
        label = Label(project=prj)
        prj.add_label(label)
        prj.add_label(label)
        self.assertEqual([label], prj.labels)

    def test_to_add_two_labels_to_a_project(self):
        """Add two Labels to a Project."""
        prj = Project(id_=None)
        first_label = Label(project=prj)
        second_label = Label(project=prj)
        prj.add_label(first_label)
        prj.add_label(second_label)
        self.assertEqual([first_label, second_label], prj.labels)

    def test_to_add_spans_to_annotation(self):
        """Add one Span to one Annotation."""
        prj = Project(id_=None)
        doc = Document(project=prj)
        span = Span(start_offset=1, end_offset=2)
        annotation = Annotation(document=doc, spans=[span])
        self.assertEqual([span], annotation.spans)

    def test_to_there_must_not_be_a_folder(self):
        """Add one Span to one Annotation."""
        prj = Project(id_=None)
        doc = Document(project=prj)
        assert not os.path.isdir(doc.document_folder)

    def test_to_add_two_spans_to_annotation(self):
        """Add one Span to one Annotation."""
        prj = Project(id_=None)
        doc = Document(project=prj)
        span = Span(start_offset=1, end_offset=2)
        annotation = Annotation(document=doc, spans=[span, span])
        self.assertEqual([span], annotation.spans)

    def test_to_add_an_annotation_twice_to_a_document(self):
        """Test to add the same Annotation twice to a Document."""
        prj = Project(id_=None)
        span = Span(start_offset=1, end_offset=2)
        doc = Document(project=prj)
        annotation = Annotation(document=doc, spans=[span])
        doc.add_annotation(annotation)
        doc.add_annotation(annotation)
        self.assertEqual([annotation], doc.annotations(use_correct=False))

    def test_to_add_two_annotations_to_a_document(self):
        """Test to add an the same Annotation twice to a Document."""
        prj = Project(id_=None)
        first_span = Span(start_offset=1, end_offset=2)
        second_span = Span(start_offset=2, end_offset=3)
        doc = Document(project=prj)
        first_annotation = Annotation(document=doc, spans=[first_span])
        second_annotation = Annotation(document=doc, spans=[first_span, second_span])
        self.assertEqual([first_annotation, second_annotation], doc.annotations(use_correct=False))


class TestKonfuzioDataCustomPath(unittest.TestCase):
    """Test handle data."""

    def test_get_text_for_doc_needing_update(self):
        """Test to load the Project into a custom folder and only get one document."""
        prj = Project(id_=TEST_PROJECT_ID, project_folder='my_own_data')
        doc = prj.get_document_by_id(214414)
        doc.download_document_details()
        self.assertTrue(is_file(doc.txt_file_path))
        for document in prj.documents:
            if document.id_ != doc.id_:
                self.assertTrue(not is_file(document.txt_file_path, raise_exception=False))
        self.assertTrue(doc.text)
        prj.delete()

    def test_make_sure_text_is_downloaded_automatically(self):
        """Test if a Text downloaded automatically."""
        prj = Project(id_=TEST_PROJECT_ID, project_folder='my_own_data')
        doc = prj.get_document_by_id(214414)
        self.assertEqual(None, doc._text)
        self.assertTrue(doc.text)
        self.assertTrue(is_file(doc.txt_file_path))
        prj.delete()


@pytest.mark.serial
class TestKonfuzioDataSetup(unittest.TestCase):
    """Test handle data."""

    document_count = 27
    test_document_count = 3
    annotations_correct = 25

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize the test Project."""
        cls.prj = Project(id_=46)

    def test_number_training_documents(self):
        """Test the number of Documents in data set status training."""
        assert len(self.prj.documents) == self.document_count

    def test_number_test_documents(self):
        """Test the number of Documents in data set status test."""
        assert len(self.prj.test_documents) == self.test_document_count

    def test_number_excluded_documents(self):
        """Test the number of Documents in data set status excluded."""
        assert len(self.prj.excluded_documents) == 1

    def test_all_labels_have_threshold(self):
        """Test that all labels have the attribute threshold."""
        for label in self.prj.labels:
            assert hasattr(label, 'threshold')

    def test_number_preparation_documents(self):
        """Test the number of Documents in data set status preparation."""
        assert len(self.prj.preparation_documents) == 0

    def test_annotation_of_label(self):
        """Test the number of Annotations across all Documents in training."""
        label = self.prj.get_label_by_id(867)
        assert len(label.correct_annotations) == self.annotations_correct

    def test_annotation_hashable(self):
        """Test if an annotation can be hashed."""
        set(self.prj.get_document_by_id(TEST_DOCUMENT_ID).annotations())

    def test_number_of_label_sets(self):
        """Test Label Sets numbers."""
        assert self.prj.label_sets.__len__() == 5

    def test_check_tokens(self):
        """Test to find not matched Annotations."""
        spans = self.prj.get_label_by_id(867).check_tokens()
        assert len(spans) == 1

    def test_has_multiple_annotation_sets(self):
        """Test Label Sets in the test Project."""
        assert self.prj.get_label_set_by_name('Brutto-Bezug').has_multiple_annotation_sets

    def test_has_not_multiple_annotation_sets(self):
        """Test Label Sets in the test Project."""
        assert not self.prj.get_label_set_by_name('Lohnabrechnung').has_multiple_annotation_sets

    def test_default_label_set(self):
        """Test the main Label Set incl. it's labels."""
        default_label_set = self.prj.get_label_set_by_name('Lohnabrechnung')
        assert default_label_set.labels.__len__() == 10

    def test_to_filter_annotations_by_label(self):
        """Test to get correct Annotations of a Label."""
        label = self.prj.get_label_by_id(858)
        self.assertEqual(len(label.correct_annotations), self.annotations_correct + 1)

    def test_category(self):
        """Test if Category of main Label Set is initialized correctly."""
        assert len(self.prj.categories) == 1
        assert self.prj.categories[0].id_ == 63
        assert self.prj.label_sets[0].categories[0].id_ == 63

    def test_label_set_multiple(self):
        """Test Label Set config that is set to multiple."""
        label_set = self.prj.get_label_set_by_name('Brutto-Bezug')
        assert label_set.categories.__len__() == 1

    def test_number_of_labels_of_label_set(self):
        """Test the number of Labels of the default Label Set."""
        label_set = self.prj.get_label_set_by_name('Lohnabrechnung')
        assert label_set.categories == []  # defines a category
        assert label_set.labels.__len__() == 10

    def test_categories(self):
        """Test get Labels in the Project."""
        assert self.prj.categories.__len__() == 1
        assert self.prj.categories[0].name == 'Lohnabrechnung'
        assert self.prj.categories[0].is_default
        assert not self.prj.categories[0].has_multiple_annotation_sets

    def test_get_images(self):
        """Test get paths to the images of the first training document."""
        self.prj.documents[0].get_images()
        assert len(self.prj.documents[0].image_paths) == len(self.prj.documents[0].pages)

    def test_get_file(self):
        """Test get path to the file of the first training document."""
        self.prj.documents[0].get_file()
        assert self.prj.documents[0].ocr_file_path

    def test_get_file_without_ocr(self):
        """Download file without OCR."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        doc.get_file(ocr_version=False)
        is_file(doc.file_path)

    def test_get_file_with_ocr(self):
        """Download file without OCR."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        doc.get_file()
        is_file(doc.ocr_file_path)

    def test_get_bbox(self):
        """Test to get BoundingBox of Text offset."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        annotation = Annotation(document=doc)
        span = Span(start_offset=44, end_offset=65, annotation=annotation)
        span.bbox()
        self.assertEqual(span.top, 23.849)
        self.assertEqual(span.bottom, 32.849)
        self.assertEqual(span.page_index, 0)
        self.assertEqual(span.x0, 426.0)
        self.assertEqual(span.x1, 442.8)
        self.assertEqual(span.y0, 808.831)
        self.assertEqual(span.y1, 817.831)

    def test_size_of_project(self):
        """Test size of Project and compare it to the size after Documents have been loaded."""
        import sys
        from types import ModuleType, FunctionType
        from gc import get_referents

        # Custom objects know their class.
        # Function objects seem to know way too much, including modules.
        # Exclude modules as well.
        BLACKLIST = type, ModuleType, FunctionType

        def _getsize(obj):
            """Sum size of object & members. From https://stackoverflow.com/a/30316760."""
            if isinstance(obj, BLACKLIST):
                raise TypeError('getsize() does not take argument of type: ' + str(type(obj)))
            seen_ids = set()
            size = 0
            objects = [obj]
            while objects:
                need_referents = []
                for obj in objects:
                    if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                        seen_ids.add(id(obj))
                        size += sys.getsizeof(obj)
                        need_referents.append(obj)
                objects = get_referents(*need_referents)
            return size

        # start of test
        prj = Project(id_=46)
        before = _getsize(prj)
        for document in prj.documents:
            document.text
        after = _getsize(prj)
        assert after / before > 1.8

    def test_create_new_doc_via_text_and_bbox(self):
        """Test to create a new Document which by a text and a bbox."""
        doc = Project(id_=46).get_document_by_id(TEST_DOCUMENT_ID)
        new_doc = Document(project=doc.project, text=doc.text, bbox=doc.get_bbox())
        assert new_doc.text
        assert new_doc.get_bbox()
        assert new_doc.number_of_pages == 1

    def test_category_of_document(self):
        """Test to download a file which includes a whitespace in the name."""
        category = Project(id_=46).get_document_by_id(44860).category
        self.assertEqual(category.name, 'Lohnabrechnung')

    def test_category_of_document_without_category(self):
        """Test the Category of a Document without Category."""
        category = Project(id_=46).get_document_by_id(44864).category
        self.assertIsNone(category)

    def test_get_file_with_white_colon_name(self):
        """Test to download a file which includes a whitespace in the name."""
        doc = Project(id_=46).get_document_by_id(44860)
        doc.get_file()

    def test_labels(self):
        """Test get Labels in the Project."""
        assert len(self.prj.labels) == 18

    def test_project(self):
        """Test basic properties of the Project object."""
        assert is_file(self.prj.meta_file_path)
        assert self.prj.documents[1].id_ > self.prj.documents[0].id_
        assert len(self.prj.documents)
        # check if we can initialize a new project object, which will use the same data
        assert len(self.prj.documents) == self.document_count
        new_project = Project(id_=TEST_PROJECT_ID)
        assert len(new_project.documents) == self.document_count
        assert new_project.meta_file_path == self.prj.meta_file_path

    def test_update_prj(self):
        """Test number of Documents after updating a Project."""
        assert len(self.prj.documents) == self.document_count
        self.prj.get(update=True)
        assert len(self.prj.documents) == self.document_count
        is_file(self.prj.meta_file_path)

    def test_document(self):
        """Test properties of a specific Documents in the test Project."""
        doc = self.prj.get_document_by_id(44842)
        assert doc.category.name == 'Lohnabrechnung'
        assert len(self.prj.labels[0].correct_annotations) == self.annotations_correct
        doc.update()
        self.assertEqual(len(self.prj.labels[0].correct_annotations), self.annotations_correct)
        assert len(doc.text) == 4793
        assert len(glob.glob(os.path.join(doc.document_folder, '*.*'))) == 4

    def test_annotations_in_document(self):
        """Test number and value of Annotations."""
        doc = self.prj.get_document_by_id(44842)
        assert len(doc.annotations(use_correct=False)) == 24
        assert doc.annotations()[0].offset_string == ['22.05.2018']  # start_offset=465, start_offset=466
        assert len(doc.annotations()) == 24
        assert doc.annotations()[0].is_online
        assert not doc.annotations()[0].save()  # Save returns False because Annotation is already online.

    def test_annotation_sets_in_document(self):
        """Test number of Annotation Sets in a specific Document in the test Project."""
        doc = self.prj.get_document_by_id(44842)
        assert len(doc.annotation_sets) == 5

    def test_get_annotation_set_after_removal(self):
        """Test get an annotation set that no longer exists."""
        with self.assertRaises(IndexError) as _:
            # create annotation for a certain annotation set in a document
            doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)

            # get the annotation set ID of the first annotation
            annotations = doc.annotations()
            annotation_set_id = annotations[0].annotation_set.id_

            assert isinstance(annotation_set_id, int)

            # delete annotation set
            doc._annotation_sets = []

            # trying to get an annotation set that no longer exists
            _ = doc.get_annotation_set_by_id(annotation_set_id)

    def test_document_with_multiline_annotation(self):
        """Test properties of a specific Documents in the test Project."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        assert doc.category.name == 'Lohnabrechnung'
        label = self.prj.get_label_by_id(867)
        self.assertEqual(len(label.correct_annotations), self.annotations_correct)
        doc.update()
        self.assertEqual(len(label.correct_annotations), self.annotations_correct)
        self.assertEqual(len(doc.text), 4537)
        self.assertEqual(len(glob.glob(os.path.join(doc.document_folder, '*.*'))), 4)

        # existing annotation
        # https://app.konfuzio.com/admin/server/sequenceannotation/?document_id=44823&project=46
        self.assertEqual(len(doc.annotations(use_correct=False)), 22)
        # a multiline Annotation in the top right corner, see https://app.konfuzio.com/a/4419937
        # todo improve multiline support
        self.assertEqual(66, doc.annotations()[0]._spans[0].start_offset)
        self.assertEqual(78, doc.annotations()[0]._spans[0].end_offset)
        self.assertEqual(159, doc.annotations()[0]._spans[1].start_offset)
        self.assertEqual(169, doc.annotations()[0]._spans[1].end_offset)
        self.assertEqual(len(doc.annotations()), 19)
        self.assertTrue(doc.annotations()[0].is_online)
        self.assertTrue(not doc.annotations()[0].save())  # Save returns False because Annotation is already online.

    def test_add_document_twice(self):
        """Test adding same Document twice."""
        old_doc = self.prj.documents[1]
        assert len(self.prj.documents) == self.document_count
        self.prj.add_document(old_doc)
        assert len(self.prj.documents) == self.document_count

    def test_correct_annotations(self):
        """Test correct Annotations of a certain Label in a specific document."""
        doc = self.prj.get_document_by_id(44842)
        label = self.prj.get_label_by_id(867)
        assert len(doc.annotations(label=label)) == 1

    def test_annotation_start_offset_zero_filter(self):
        """Test Annotations with start offset equal to zero."""
        doc = self.prj.get_document_by_id(44842)
        assert len(doc.annotations()) == 24
        assert doc.annotations()[0].start_offset == 188
        assert len(doc.annotations()) == 24

    def test_multiline_annotation(self):
        """Test to convert a multiline span Annotation to a dict."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        assert len(doc.annotations()[0].eval_dict) == 2

    def test_annotation_to_dict(self):
        """Test to convert a Annotation to a dict."""
        for annotation in self.prj.documents[0].annotations():
            if annotation.id_ == 4420022:
                anno = annotation.eval_dict[0]

        assert anno["confidence"] == 1.0
        # assert anno["created_by"] ==  todo: support this variable provided via API in the Annotation
        # assert anno["custom_offset_string"] ==   todo: support this variable provided via API in the Annotation
        assert anno["end_offset"] == 366  # todo support multiline Annotations
        # assert anno["get_created_by"] == "ana@konfuzio.com"  todo: support this variable provided via API
        # assert anno["get_revised_by"] == "n/a" todo: support this variable provided via API in the Annotation
        assert anno["is_correct"]
        assert anno["label_id"] == 860  # original REST API calls it "label" however means label_id
        # assert anno["label_data_type"] == "Text"  # todo add to evaluation
        # assert anno["label_text"] ==  not supported in SDK but in REST API
        assert anno["label_threshold"] == 0.1
        # assert anno["normalized"] == '1'  # todo normalized is not really normalized data, e.g. for dates
        # assert anno["offset_string"] ==  # todo not supported by SDK but REST API
        # assert anno["offset_string_original"] ==  # todo not supported by SDK but REST API
        assert not anno["revised"]
        # self.assertIsNone(anno["revised_by"])   # todo not supported by SDK but REST API
        assert anno["annotation_set_id"] == 78730  # v2 REST API calls it still section
        assert anno["label_set_id"] == 63  # v2 REST API call it still section_label_id
        # assert anno["annotation_set_text"] == "Lohnabrechnung"  # v2 REST API call it still section_label_text
        assert anno["start_offset"] == 365
        # self.assertIsNone(anno["translated_string"])  # todo: how to translate null in a meaningful way

    def test_document_annotations_filter(self):
        """Test Annotations filter."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        self.assertEqual(len(doc.annotations()), 19)
        assert len(doc.annotations(label=self.prj.get_label_by_id(858))) == 1
        assert len(doc.annotations(use_correct=False)) == 22

    def test_document_offset(self):
        """Test Document offsets."""
        doc = self.prj.get_document_by_id(44842)
        assert doc.text[395:396] == '4'
        annotations = doc.annotations()
        self.assertEqual(24, len(annotations))
        assert annotations[2].offset_string == ['4']

    @unittest.skip(reason='Waiting for API to support to add to default Annotation Set')
    def test_document_add_new_annotation(self):
        """Test adding a new annotation."""
        doc = self.prj.labels[0].documents[5]  # the latest document
        # we create a revised Annotations, as only revised Annotation can be deleted
        # if we would delete an unrevised annotation, we would provide feedback and thereby keep the
        # Annotation as "wrong" but "revised"
        assert len(doc.annotations(use_correct=False)) == 23
        label = self.prj.labels[0]
        new_anno = Annotation(
            start_offset=225,
            end_offset=237,
            label=label.id_,
            label_set_id=None,  # hand selected document section label
            revised=True,
            is_correct=True,
            accuracy=0.98765431,
            document=doc,
        )
        # make sure Document Annotations are updated too
        assert len(doc.annotations(use_correct=False)) == 24
        self.assertEqual(self.document_count + 1, len(self.prj.labels[0].correct_annotations))
        assert new_anno.id_ is None
        new_anno.save()
        assert new_anno.id_
        new_anno.delete()
        assert new_anno.id_ is None
        assert len(doc.annotations(use_correct=False)) == 13
        self.assertEqual(self.document_count, len(self.prj.labels[0].correct_annotations))

    @unittest.skip(reason="Skip: Changes in Trainer Annotation needed to require a Label for every Annotation init.")
    def test_document_add_new_annotation_without_label(self):
        """Test adding a new annotation."""
        with self.assertRaises(AttributeError) as _:
            _ = Annotation(
                start_offset=225,
                end_offset=237,
                label=None,
                label_set_id=0,  # hand selected document section label
                revised=True,
                is_correct=True,
                accuracy=0.98765431,
                document=Document(),
            )
        # TODO: expand assert to check for specific error message

    @unittest.skip(reason="Skip: Changes in Trainer Annotation needed to require a Document for every Annotation init.")
    def test_init_annotation_without_document(self):
        """Test adding a new annotation."""
        with self.assertRaises(AttributeError) as _:
            _ = Annotation(
                start_offset=225,
                end_offset=237,
                label=None,
                label_set_id=0,
                revised=True,
                is_correct=True,
                accuracy=0.98765431,
                document=None,
            )

        # TODO: expand assert to check for specific error message

    @pytest.mark.xfail(reason='We cannot define the Annotation Set automatically.')
    def test_init_annotation_with_default_annotation_set(self):
        """Test adding a new Annotation without providing the Annotation Set."""
        prj = Project(id_=TEST_PROJECT_ID)
        doc = Document(project=prj)
        annotation = Annotation(
            start_offset=225,
            end_offset=237,
            label=prj.labels[0],
            label_set_id=0,
            revised=True,
            is_correct=True,
            accuracy=0.98765431,
            document=doc,
            annotation_set=None,
        )

        # an Annotation Set needs to be created or retrieved after the Annotation is saved
        assert annotation.annotation_set.id_ == 78730

    @unittest.skip(reason="Issue https://gitlab.com/konfuzio/objectives/-/issues/8664.")
    def test_get_text_in_bio_scheme(self):
        """Test getting Document in the BIO scheme."""
        doc = self.prj.documents[0]
        bio_annotations = doc.get_text_in_bio_scheme()
        assert len(bio_annotations) == 398
        # check for multiline support in bio schema
        assert bio_annotations[1][0] == '328927/10103/00104'
        assert bio_annotations[1][1] == 'B-Austellungsdatum'
        assert bio_annotations[8][0] == '22.05.2018'
        assert bio_annotations[8][1] == 'B-Austellungsdatum'

    def test_number_of_all_documents(self):
        """Count the number of all available documents online."""
        prj = Project(id_=TEST_PROJECT_ID)
        assert len(prj._documents) == 42

    def test_create_empty_annotation(self):
        """Create an empty Annotation and get the start offset."""
        prj = Project(id_=TEST_PROJECT_ID)
        label = Label(project=prj)
        doc = Document(text='', project=prj)
        label_set = LabelSet(project=prj)
        annotation_set = AnnotationSet(document=doc, label_set=label_set)
        _ = Annotation(label=label, annotation_set=annotation_set, label_set=label_set, document=doc)

    def test_get_annotations_for_offset_of_first_and_last_name(self):
        """Get Annotations for all offsets in the document."""
        doc = self.prj.get_document_by_id(TEST_DOCUMENT_ID)
        filtered_annotations = doc.annotations(start_offset=1500, end_offset=1530)
        self.assertEqual(len(filtered_annotations), 3)  # 3 is correct even 4 Spans!
        text = '198,34\n  Erna-Muster Eiermann                         KiSt      15,83   Solz        10,89\n  '
        self.assertEqual(doc.text[1498:1590], text)

    def test_create_list_of_regex_for_label_without_annotations(self):
        """Check regex build for empty Labels."""
        try:
            label = next(x for x in self.prj.labels if len(x.annotations) == 0)
            automated_regex_for_label = label.regex()
            # There is no regex available.
            assert len(automated_regex_for_label) == 0
            is_file(label.regex_file_path)
        except StopIteration:
            pass

    @pytest.mark.xfail(reason='Refactoring via Pair Programming needed to clean up code and clarify test cases.')
    def test_get_default_label_set_documents(self):
        """Check get Documents and Labels associated to a default annotation_set label."""
        default_label_sets = [x for x in self.prj.label_sets if x.is_default]

        default_label_set_documents_dict, default_labels_dict = get_default_label_set_documents(
            documents=self.prj.documents,
            selected_default_label_sets=default_label_sets,
            project_label_sets=self.prj.label_sets,
            merge_multi_default=False,
        )

        assert list(default_label_set_documents_dict.keys()) == [63]
        self.assertEqual(len(default_label_set_documents_dict[63]), self.correct_document_count)
        assert default_label_set_documents_dict.keys() == default_labels_dict.keys()
        assert len(default_labels_dict[63]) == 17

    @pytest.mark.xfail(reason='Refactoring via Pair Programming needed to clean up code and clarify test cases.')
    def test_separate_labels(self):
        """Test Label Sets and Labels can be combined correctly."""
        self.assertEqual(len(self.prj.label_sets), 5)
        assert len(self.prj.labels) == 18

        labels_with_annotations = {}

        for label_set in [x for x in self.prj.label_sets if not x.is_default]:
            labels_names = [label.name for label in label_set.labels if len(label.annotations) > 0]
            labels_with_annotations[label_set.name] = labels_names

        n_labels_with_annotations = 0

        for _, labels_names in labels_with_annotations.items():
            n_labels_with_annotations += len(labels_names)

        prj = separate_labels(project=self.prj)
        assert len(prj.label_sets) == 5

        # separate Labels changes the Labels of the Annotations that belong to non default label_sets in the project
        separated_labels_with_annotations = [
            label.name
            for label in prj.labels
            if len([s for s in label.label_sets if not s.is_default]) > 0 and len(label.annotations) > 0
        ]

        assert len(separated_labels_with_annotations) == n_labels_with_annotations
        assert len(prj.documents) == self.document_count  # only 29 Documents have been added to the dataset

        # verify if new Labels are indeed added
        for label_set in [x for x in prj.label_sets if not x.is_default]:
            new_labels = [label.name for label in label_set.labels if len(label.annotations) > 0 and "__" in label.name]

            assert len(new_labels) > 0
            original_labels = labels_with_annotations[label_set.name]

            for label in new_labels:
                original_label = label.split("__")[1]
                assert original_label in original_labels

        self.prj = Project(id_=46)
        assert len(self.prj.label_sets) == 5
        assert len(self.prj.labels) == 18
        assert len(self.prj.labels[0].correct_annotations) == self.correct_document_count

    @unittest.skip(reason='Waiting for Text-Annotation Documentation.')
    def test_to_change_an_annotation_online(self):
        """Test to update an Annotation from revised to not revised and back to revised."""
        doc = self.prj.get_document_by_id(44864)
        annotations = doc.annotations(start_offset=10, end_offset=200)
        first_annotation = annotations[0]
        first_annotation.revised = False
        first_annotation.save()

    @classmethod
    def tearDownClass(cls) -> None:
        """Test if the Project remains the same as in the beginning."""
        assert len(cls.prj.documents) == cls.document_count
        assert len(cls.prj.test_documents) == cls.test_document_count
        assert len(cls.prj.labels[0].annotations) == cls.annotations_correct


@pytest.mark.serial
class TestFillOperation(unittest.TestCase):
    """Seperate Test as we add non Labels to the Project."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initialize the test: https://app.konfuzio.com/projects/46/docs/44823/bbox-annotations/."""
        cls.prj = Project(id_=46)
        cls.doc = cls.prj.get_document_by_id(TEST_DOCUMENT_ID)
        default_label_set = cls.prj.get_label_set_by_name('Lohnabrechnung')
        assert default_label_set.labels.__len__() == 10
        cls.annotations = cls.doc.annotations(start_offset=1498, end_offset=1590, fill=True)
        cls.sorted_spans = sorted([span for annotation in cls.annotations for span in annotation.spans])
        assert default_label_set.labels.__len__() == 11
        cls.text = '198,34\n  Erna-Muster Eiermann                         KiSt      15,83   Solz        10,89\n  '
        assert cls.doc.text[1498:1590] == cls.text

    def test_number_of_annotations(self):
        """Get Annotations for all offsets in the document."""
        self.assertEqual(len(self.annotations), 7)  # 2 single line Annotation, one multiline with two spans

    def test_number_of_spans(self):
        """Get Annotations for all offsets in the document."""
        self.assertEqual(len([span for annotation in self.annotations for span in annotation.spans]), 10)

    @unittest.skip(reason="Documents without Category cannot be processed.")
    def test_fill_doc_without_category(self):
        """Try to fill a Document without Category."""
        self.prj.get_document_by_id(44864).annotations(fill=True)

    def test_fill_full_document_with_category(self):
        """Try to fill a Document with Category."""
        self.prj.get_document_by_id(TEST_DOCUMENT_ID).annotations(fill=True)

    def test_correct_text_offset(self):
        """Test if the the sorted spans can create the offset text."""
        offsets = [sorted_span.offset_string for sorted_span in self.sorted_spans]
        span_text = "".join(offsets)
        self.assertEqual(self.doc.text[1498:1590], span_text)

    def test_span_start_and_end(self):
        """Test if the Spans have the correct offsets."""
        spa = [(span.start_offset, span.end_offset) for span in self.sorted_spans]
        assert self.doc.text[slice(spa[0][0], spa[0][1])] == self.doc.text[1498:1504] == '198,34'
        assert self.doc.text[slice(spa[1][0], spa[1][1])] == self.doc.text[1504:1505] == '\n'
        assert self.doc.text[slice(spa[2][0], spa[2][1])] == self.doc.text[1505:1507] == '  '
        assert self.doc.text[slice(spa[3][0], spa[3][1])] == self.doc.text[1507:1518] == 'Erna-Muster'
        assert self.doc.text[slice(spa[4][0], spa[4][1])] == self.doc.text[1518:1519] == ' '
        assert self.doc.text[slice(spa[5][0], spa[5][1])] == self.doc.text[1519:1527] == 'Eiermann'
        unlabeled = '                         KiSt      15,83   Solz        '
        assert self.doc.text[slice(spa[6][0], spa[6][1])] == self.doc.text[1527:1582] == unlabeled
        assert self.doc.text[slice(spa[7][0], spa[7][1])] == self.doc.text[1582:1587] == '10,89'
        assert self.doc.text[slice(spa[8][0], spa[8][1])] == self.doc.text[1587:1588] == '\n'
        assert self.doc.text[slice(spa[9][0], spa[9][1])] == self.doc.text[1588:1590] == '  '


@pytest.mark.local
class TestData(unittest.TestCase):
    """Test functions that don't require data."""

    def test_compare_none_and_id(self):
        """Test to compare an instance to None."""
        a = Data()
        a.id_ = 5
        self.assertNotEqual(a, None)

    def test_compare_nones(self):
        """Test to compare an instance with None ID to None."""
        a = Data()
        self.assertNotEqual(a, None)

    def test_compare_id_with_instance_without(self):
        """Test to compare an instance with ID to an instance with None ID."""
        a = Data()
        a.id_ = 5
        b = Data()
        self.assertNotEqual(a, b)


def test_download_training_and_test_data():
    """Test downloading of data from training and test documents."""
    download_training_and_test_data(TEST_PROJECT_ID)


def test_to_init_prj_from_folder():
    """Load Project from folder."""
    prj = Project(id_=46, project_folder='data_46')
    assert len(prj.documents) == 27
