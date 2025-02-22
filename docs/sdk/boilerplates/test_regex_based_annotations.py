"""Test code examples for regex-based Annotations in the documentation."""


def test_regex_based_annotations():
    """Test regex-based Annotations."""
    from tests.variables import TEST_PROJECT_ID

    YOUR_PROJECT_ID = TEST_PROJECT_ID
    # start imports
    import re
    from konfuzio_sdk.data import Project, Annotation, Span

    my_project = Project(id_=YOUR_PROJECT_ID)
    # end imports
    my_project = Project(id_=YOUR_PROJECT_ID, strict_data_validation=False)
    # start regex based
    # Word/expression to annotate in the Document
    # should match an existing one in your Document
    input_expression = "Musterstraße"

    # Label for the Annotation
    label_name = "Lohnart"
    # Getting the Label from the Project
    my_label = my_project.get_label_by_name(label_name)

    # LabelSet to which the Label belongs
    label_set = my_label.label_sets[0]

    # First Document in the Project
    document = my_project.documents[0]

    # Matches of the word/expression in the Document
    matches_locations = [(m.start(0), m.end(0)) for m in re.finditer(input_expression, document.text)]

    # List to save the links to the Annotations created
    new_annotations_links = []

    # Create Annotation for each match
    for offsets in matches_locations:
        span = Span(start_offset=offsets[0], end_offset=offsets[1])
        annotation_obj = Annotation(
            document=document, label=my_label, label_set=label_set, confidence=1.0, spans=[span], is_correct=True
        )
        new_annotation_added = annotation_obj.save()
        if new_annotation_added:
            new_annotations_links.append(annotation_obj.get_link())
        annotation_obj.delete(delete_online=True)

    print(new_annotations_links)
    # end regex based
    assert my_label.name == label_name
    assert label_set.name == 'Brutto-Bezug'
    assert matches_locations == [(1590, 1602)]
    assert len(new_annotations_links) == 1
