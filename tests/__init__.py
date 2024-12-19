from collections import namedtuple

SchemaFixture = namedtuple("SchemaFixture", ["schema", "config_filename", "expected_labels", "converted_weights_name"])
