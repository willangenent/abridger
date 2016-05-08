import pytest
from pprint import pprint

from minime.extraction_model import ExtractionModel
from minime.rocket import Rocket


class TestRocketBase(object):
    @pytest.fixture(autouse=True)
    def default_fixtures(self, sqlite_conn, sqlite_dbconn):
        self.dbconn = sqlite_dbconn
        self.conn = sqlite_conn

    def check_launch(self, schema, tables, expected_data,
                     relations=None, global_relations=None,
                     expected_fetch_count=None,
                     one_subject=True):
        if one_subject:
            extraction_model_data = [{'subject': [{'tables': tables}]}]
            if relations is not None:
                extraction_model_data[0]['subject'].append(
                    {'relations': relations})
        else:
            extraction_model_data = []
            for t in tables:
                subject = [{'tables': [t]}]
                if relations is not None:
                    subject.append({'relations': relations})
                extraction_model_data.append({'subject': subject})

        if global_relations is not None:
            extraction_model_data.append({'relations': global_relations})

        extraction_model = ExtractionModel.load(schema, extraction_model_data)
        rocket = Rocket(self.dbconn, extraction_model).launch()

        expected_data = sorted(expected_data, key=lambda t: t[0].name)

        if rocket.flat_results() != expected_data:
            print
            print 'Got results:'
            pprint(rocket.flat_results())
            print 'Expected results:'
            pprint(expected_data)
        assert rocket.flat_results() == expected_data
        if expected_fetch_count is not None:
            assert rocket.fetch_count == expected_fetch_count
        return rocket

    def check_one_subject(self, schema, tables, expected_data,
                          relations=None, global_relations=None,
                          expected_fetch_count=None):
        self.check_launch(schema, tables, expected_data, relations=relations,
                          global_relations=global_relations, one_subject=True)

    def check_two_subjects(self, schema, tables, expected_data,
                           relations=None, global_relations=None,
                           expected_fetch_count=None):
        self.check_launch(schema, tables, expected_data, relations=relations,
                          global_relations=global_relations, one_subject=False)