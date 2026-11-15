
import sqlite3
import pytest

from app.services.loader import SQLiteDataLoader, LoadingError


@pytest.fixture
def loader():
    return SQLiteDataLoader()


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def customers():
    return [
        {"customer_id": 1, "name": "Rajesh", "age": 21},
        {"customer_id": 2, "name": "Arun", "age": 25},
    ]


def get_rows(db_path):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(
            "SELECT customer_id, name, age FROM customers ORDER BY customer_id"
        ).fetchall()


def test_append_records(loader, db_path, customers):
    result = loader.load(
        customers, db_path, "customers", "append", ["customer_id"]
    )

    assert result["input_count"] == 2
    assert result["loaded_count"] == 2
    assert len(get_rows(db_path)) == 2


def test_append_adds_records(loader, db_path, customers):
    loader.load(customers, db_path, "customers", "append", ["customer_id"])

    new_records = [
        {"customer_id": 3, "name": "Sita", "age": 23}
    ]
    loader.load(new_records, db_path, "customers", "append", ["customer_id"])

    assert len(get_rows(db_path)) == 3


def test_replace_records(loader, db_path, customers):
    loader.load(customers, db_path, "customers", "append", ["customer_id"])

    replacement = [
        {"customer_id": 3, "name": "Kiran", "age": 24}
    ]
    result = loader.load(
        replacement, db_path, "customers", "replace", ["customer_id"]
    )

    assert result["loaded_count"] == 1
    assert get_rows(db_path) == [(3, "Kiran", 24)]


def test_upsert_inserts_and_updates(loader, db_path, customers):
    loader.load(customers, db_path, "customers", "append", ["customer_id"])

    updates = [
        {"customer_id": 1, "name": "Rajesh Updated", "age": 22},
        {"customer_id": 3, "name": "Sita", "age": 23},
    ]

    result = loader.load(
        updates, db_path, "customers", "upsert", ["customer_id"]
    )

    rows = get_rows(db_path)

    assert result["loaded_count"] == 2
    assert len(rows) == 3
    assert rows[0] == (1, "Rajesh Updated", 22)
    assert rows[2] == (3, "Sita", 23)


def test_upsert_requires_primary_key(loader, db_path, customers):
    with pytest.raises(LoadingError, match="primary key"):
        loader.load(customers, db_path, "customers", "upsert")



def test_duplicate_primary_key_rolls_back(loader, db_path):
    records = [
        {"customer_id": 1, "name": "Rajesh"},
        {"customer_id": 1, "name": "Duplicate"},
    ]

    with pytest.raises(LoadingError):
        loader.load(
            records, db_path, "customers", "append", ["customer_id"]
        )

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

    assert count == 0


def test_empty_input(loader, db_path):
    result = loader.load([], db_path, "customers")

    assert result["input_count"] == 0
    assert result["loaded_count"] == 0


def test_unsupported_mode(loader, db_path, customers):
    with pytest.raises(LoadingError, match="Unsupported load mode"):
        loader.load(customers, db_path, "customers", "merge")


def test_invalid_table_name(loader, db_path, customers):
    with pytest.raises(LoadingError, match="Invalid table name"):
        loader.load(customers, db_path, "customers; DROP TABLE users")


def test_inconsistent_record_columns(loader, db_path):
    records = [
        {"customer_id": 1, "name": "Rajesh"},
        {"customer_id": 2, "age": 25},
    ]

    with pytest.raises(LoadingError, match="same columns"):
        loader.load(records, db_path, "customers")


def test_upsert_updates_only_matching_key(loader, db_path, customers):
    loader.load(customers, db_path, "customers", "append", ["customer_id"])

    loader.load(
        [{"customer_id": 2, "name": "Arun Updated", "age": 26}],
        db_path,
        "customers",
        "upsert",
        ["customer_id"],
    )

    assert get_rows(db_path)[1] == (2, "Arun Updated", 26)


def test_nested_values_are_stored_as_json(loader, db_path):
    records = [
        {"customer_id": 1, "metadata": {"city": "Hyderabad"}}
    ]

    loader.load(records, db_path, "customer_metadata")

    with sqlite3.connect(db_path) as connection:
        value = connection.execute(
            "SELECT metadata FROM customer_metadata"
        ).fetchone()[0]

    assert value == '{"city": "Hyderabad"}'
