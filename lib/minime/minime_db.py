import argparse
from signal import signal, SIGPIPE, SIG_DFL
from collections import defaultdict

import minime.db_conn
from minime.extraction_model import ExtractionModel
from minime.rocket import Rocket
from minime.generator import Generator
import minime.config_file_loader


def main(args):
    parser = argparse.ArgumentParser(
        description='Minimize a database')
    parser.add_argument(dest='config_path', metavar='CONFIG_PATH',
                        help="path to extraction config file")
    parser.add_argument(dest='src_url', metavar='SRC_URL',
                        help="source database url")
    parser.add_argument(dest='dst_url', metavar='DST_URL',
                        help="destination database url")
    parser.add_argument('-e', '--explain', dest='explain', action='store_true',
                        default=False,
                        help='explain where rows are coming from')

    # Ignore SIG_PIPE and don't throw exceptions on it
    signal(SIGPIPE, SIG_DFL)

    args = parser.parse_args(args)

    print('Connecting to', args.src_url)
    src_dbconn = minime.db_conn.load(args.src_url)

    print('Querying...')
    extraction_model_data = minime.config_file_loader.load(args.config_path)
    extraction_model = ExtractionModel.load(src_dbconn.schema,
                                            extraction_model_data)
    rocket = Rocket(src_dbconn, extraction_model, explain=args.explain)
    rocket.launch()

    if args.explain:
        exit(0)

    generator = Generator(src_dbconn.schema, rocket)
    generator.generate_statements()
    src_dbconn.disconnect()

    print('Connecting to', args.dst_url)
    dst_dbconn = minime.db_conn.load(args.dst_url)

    connection = dst_dbconn.connect()

    table_row_counts = defaultdict(int)
    table_update_counts = defaultdict(int)
    cur = connection.cursor()
    try:
        total_insert_count = len(generator.insert_statements)
        insert_count = 0
        for insert_statement in generator.insert_statements:
            (table, values) = insert_statement
            table_row_counts[table] += 1
            insert_count += 1
            print("Inserting (%5d/%5d) row %5d into table %s" % (
                insert_count, total_insert_count,
                table_row_counts[table], table))
            dst_dbconn.insert_rows([insert_statement], cursor=cur)

        total_update_count = len(generator.update_statements)
        update_count = 0
        for update_statement in generator.update_statements:
            table = update_statement[0]
            table_update_counts[table] += 1
            update_count += 1
            print("Updating (%5d/%5d) update %d on table %s" % (
                update_count, total_update_count,
                table_update_counts[table], table))
            dst_dbconn.update_rows([update_statement], cursor=cur)

        connection.commit()
    finally:
        try:
            connection.rollback()
        except Exception as e:
            print("Some thing went wrong while trying a rollback: %s" % str(e))

        dst_dbconn.disconnect()