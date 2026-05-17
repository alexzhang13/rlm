"""Comprehensive tests for rlm.utils.dataframe_utils."""

import base64
import io

import pytest

from rlm.utils.dataframe_utils import (
    build_dataframe_context_code,
    dataframe_metadata,
    dataframe_to_parquet_b64,
    dataframe_to_parquet_bytes,
    get_dataframe_type,
    is_pandas_dataframe,
)

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------


class TestIsPandasDataframe:
    """Tests for is_pandas_dataframe()."""

    def test_true_for_dataframe(self):
        pd = pytest.importorskip("pandas")
        assert is_pandas_dataframe(pd.DataFrame({"a": [1]})) is True

    def test_false_for_dict(self):
        assert is_pandas_dataframe({"a": 1}) is False

    def test_false_for_list(self):
        assert is_pandas_dataframe([1, 2, 3]) is False

    def test_false_for_string(self):
        assert is_pandas_dataframe("hello") is False

    def test_false_for_none(self):
        assert is_pandas_dataframe(None) is False

    def test_false_for_int(self):
        assert is_pandas_dataframe(42) is False


class TestGetDataframeType:
    """Tests for get_dataframe_type()."""

    def test_pandas_dataframe(self):
        pd = pytest.importorskip("pandas")
        assert get_dataframe_type(pd.DataFrame({"x": [1]})) == "pandas"

    def test_non_dataframe_returns_none(self):
        assert get_dataframe_type("hello") is None
        assert get_dataframe_type(42) is None
        assert get_dataframe_type({"a": 1}) is None
        assert get_dataframe_type([1, 2]) is None
        assert get_dataframe_type(None) is None


# ---------------------------------------------------------------------------
# Parquet serialization
# ---------------------------------------------------------------------------


class TestDataframeToParquetBytes:
    """Tests for dataframe_to_parquet_bytes()."""

    def test_roundtrip(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        data, df_type = dataframe_to_parquet_bytes(df)
        assert df_type == "pandas"
        assert isinstance(data, bytes)
        roundtrip = pd.read_parquet(io.BytesIO(data))
        assert list(roundtrip.columns) == ["a", "b"]
        assert roundtrip["a"].tolist() == [1, 2, 3]

    def test_rejects_non_dataframe(self):
        with pytest.raises(ValueError, match="Unsupported DataFrame type"):
            dataframe_to_parquet_bytes({"not": "a df"})


class TestDataframeToParquetB64:
    """Tests for dataframe_to_parquet_b64()."""

    def test_roundtrip(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"col": [10, 20]})
        b64_str, df_type = dataframe_to_parquet_b64(df)
        assert df_type == "pandas"
        raw = base64.b64decode(b64_str)
        roundtrip = pd.read_parquet(io.BytesIO(raw))
        assert roundtrip["col"].tolist() == [10, 20]


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestDataframeMetadata:
    """Tests for dataframe_metadata()."""

    def test_basic(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        meta = dataframe_metadata(df)
        assert "Shape: 2 rows x 2 columns" in meta
        assert "pandas" in meta

    def test_nulls(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"a": [1, None, 3], "b": [None, None, "x"]})
        meta = dataframe_metadata(df)
        assert "Null counts" in meta

    def test_many_columns_truncation(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({f"col_{i}": [i] for i in range(25)})
        meta = dataframe_metadata(df)
        assert "5 more columns" in meta
        # Head/tail rows should also be truncated to displayed columns
        assert "col_20" not in meta
        assert "col_0" in meta

    def test_rejects_non_dataframe(self):
        with pytest.raises(ValueError, match="Unsupported DataFrame type"):
            dataframe_metadata("not a dataframe")


# ---------------------------------------------------------------------------
# Code generation — DataFrame path
# ---------------------------------------------------------------------------


class TestBuildDataframeContextCode:
    """Tests for build_dataframe_context_code()."""

    def test_exec_roundtrip(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"x": [10, 20, 30]})
        b64_str, df_type = dataframe_to_parquet_b64(df)
        code = build_dataframe_context_code(b64_str, df_type)
        ns = {}
        exec(code, ns)
        assert ns["context"]["x"].tolist() == [10, 20, 30]

    def test_custom_var_name(self):
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"v": [1]})
        b64_str, df_type = dataframe_to_parquet_b64(df)
        code = build_dataframe_context_code(b64_str, df_type, var_name="my_df")
        ns = {}
        exec(code, ns)
        assert "my_df" in ns
        assert ns["my_df"]["v"].tolist() == [1]
