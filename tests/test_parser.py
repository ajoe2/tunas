from tunas import parser
import os

TESTS_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_PATH = os.path.join(TESTS_DIRECTORY_PATH, "test_data.cl2")


class TestParser:
    """
    Test parser logic.
    """

    def test_read_cl2_basic(self):
        db = parser.read_cl2(TEST_DATA_PATH)

        assert db != None
        assert len(db.get_clubs()) > 0
        assert len(db.get_meet_results()) > 0
        assert len(db.get_swimmers()) > 0
