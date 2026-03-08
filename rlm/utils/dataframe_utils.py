import base64
import io
import json
from typing import Any, Literal

DataFrameType = Literal["pandas"]


def is_pandas_dataframe(value: Any) -> bool:
    try:
        import pandas as pd
    except ImportError:
        return False
    return isinstance(value, pd.DataFrame)


def get_dataframe_type(value: Any) -> DataFrameType | None:
    if is_pandas_dataframe(value):
        return "pandas"
    return None


def dataframe_to_parquet_bytes(value: Any) -> tuple[bytes, DataFrameType]:
    df_type = get_dataframe_type(value)
    if df_type is None:
        raise ValueError(f"Unsupported DataFrame type: {type(value)}")

    buffer = io.BytesIO()
    value.to_parquet(buffer, index=False)
    return buffer.getvalue(), df_type


def dataframe_to_parquet_b64(value: Any) -> tuple[str, DataFrameType]:
    data, df_type = dataframe_to_parquet_bytes(value)
    return base64.b64encode(data).decode("ascii"), df_type


def dataframe_metadata(value: Any) -> str:
    df_type = get_dataframe_type(value)
    if df_type is None:
        raise ValueError(f"Unsupported DataFrame type: {type(value)}")

    rows, cols = value.shape
    all_cols = list(value.columns)
    dtypes = {col: str(dtype) for col, dtype in value.dtypes.items()}
    null_counts = value.isna().sum().to_dict()
    memory_bytes = int(value.memory_usage(deep=True).sum())

    if cols > 20:
        displayed_cols = all_cols[:20]
        extra = cols - 20
        dtypes = {col: dtypes[col] for col in displayed_cols}
        dtypes["..."] = f"{extra} more columns"
        null_counts = {col: null_counts[col] for col in displayed_cols}
        null_counts["..."] = f"{extra} more columns"
        preview_df = value[displayed_cols]
    else:
        preview_df = value

    head_rows = preview_df.head(3).to_dict(orient="records")
    tail_rows = preview_df.tail(3).to_dict(orient="records")

    summary_lines = [
        f"DataFrame type: {df_type}",
        f"Shape: {rows} rows x {cols} columns",
        f"Dtypes: {dtypes}",
        f"Null counts: {null_counts}",
        f"Estimated memory: {memory_bytes} bytes",
        f"Head (3): {head_rows}",
        f"Tail (3): {tail_rows}",
    ]
    return "\n".join(summary_lines)


def build_dataframe_context_code(
    parquet_b64: str,
    df_type: DataFrameType,
    var_name: str = "context",
) -> str:
    return (
        "import base64, io\n"
        "import pandas as pd\n"
        f"_parquet_bytes = base64.b64decode('{parquet_b64}')\n"
        f"{var_name} = pd.read_parquet(io.BytesIO(_parquet_bytes))"
    )


def build_context_code(context_payload: Any, var_name: str = "context") -> str:
    """Build Python code that reconstructs *context_payload* as a variable.

    Handles three payload shapes:
    - pandas DataFrame  → Parquet-over-base64 round-trip
    - str               → triple-quoted string literal
    - other (dict/list) → ``json.loads`` from a JSON string literal
    """
    df_type = get_dataframe_type(context_payload)
    if df_type is not None:
        parquet_b64, df_type = dataframe_to_parquet_b64(context_payload)
        return build_dataframe_context_code(parquet_b64, df_type, var_name=var_name)

    if isinstance(context_payload, str):
        escaped = context_payload.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return f'{var_name} = """{escaped}"""'

    context_json = json.dumps(context_payload)
    escaped_json = context_json.replace("\\", "\\\\").replace("'", "\\'")
    return f"import json; {var_name} = json.loads('{escaped_json}')"
