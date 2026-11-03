"""
Reading CSV/Excel files and merging several files into one table.

The merged table gets an extra "File Name" column that tells which file each
row came from. Columns missing from a file are NaN for that file's rows.
Nothing here touches tkinter, so it can be tested without the GUI.
"""
import os
import pandas as pd

FILE_NAME_COLUMN = "File Name"
EXCEL_EXTENSIONS = ('.xlsx', '.xlsm', '.xls')

# Warn when more than this share of the columns differ from the first file
COLUMN_MISMATCH_THRESHOLD = 0.30


class LoadCancelled(Exception):
    """The user cancelled a choice (e.g. the sheet picker) while loading"""


# ---------------------------------------------------------------------------
# Reading single files
# ---------------------------------------------------------------------------

def read_data_file(file_path, choose_sheet):
    """Read a CSV or Excel file.

    choose_sheet(file_path, sheet_names) is called for workbooks with several
    sheets and returns the sheet name, or None to cancel.
    Returns (DataFrame with cleaned headers, sheet name or None).
    """
    if file_path.lower().endswith(EXCEL_EXTENSIONS):
        df, sheet_name = _read_excel(file_path, choose_sheet)
    else:
        df, sheet_name = _read_csv(file_path), None
    return clean_headers(df), sheet_name


def _read_csv(file_path):
    """Read a CSV saved as UTF-8 (with or without BOM) or Windows-1252 (Excel default)"""
    try:
        return pd.read_csv(file_path, encoding='utf-8-sig')
    except UnicodeDecodeError:
        return pd.read_csv(file_path, encoding='cp1252')


def _read_excel(file_path, choose_sheet):
    """Read one sheet of an Excel workbook"""
    with pd.ExcelFile(file_path) as workbook:
        sheet_names = workbook.sheet_names
        if not sheet_names:
            raise ValueError(f"'{os.path.basename(file_path)}' has no sheets")

        if len(sheet_names) == 1:
            sheet_name = sheet_names[0]
        else:
            sheet_name = choose_sheet(file_path, sheet_names)
            if sheet_name is None:
                raise LoadCancelled()

        df = workbook.parse(sheet_name)

    # Drop fully empty rows/columns that Excel often leaves around the data
    df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)
    if df.empty:
        raise ValueError(f"Sheet '{sheet_name}' in '{os.path.basename(file_path)}' has no data")
    return df, sheet_name


def clean_headers(df):
    """Make headers text without surrounding spaces, so 'Speed ' and 'Speed' match.

    Excel headers can be numbers/dates; the rest of the app expects text names.
    Names that collide after stripping get a .1, .2 ... suffix (like pandas does).
    """
    seen = {}
    new_columns = []
    for col in df.columns:
        name = str(col).strip()
        if name in seen:
            seen[name] += 1
            candidate = f"{name}.{seen[name]}"
            while candidate in seen:
                seen[name] += 1
                candidate = f"{name}.{seen[name]}"
            name = candidate
        seen.setdefault(name, 0)
        new_columns.append(name)
    df.columns = new_columns
    return df


# ---------------------------------------------------------------------------
# Naming the files
# ---------------------------------------------------------------------------

def make_display_names(paths, existing_names=()):
    """Short, unique names for the "File Name" column.

    Normally just the file name. Files with the same name from different
    folders get as many parent folders as needed: 'run1/results.csv'.
    A name that is still taken (same file loaded again) gets ' (2)', ' (3)'...
    """
    paths = [os.path.normpath(os.path.abspath(p)) for p in paths]
    parts = [p.split(os.sep) for p in paths]
    depth = [1] * len(paths)

    def name_at(i):
        return "/".join(parts[i][-depth[i]:])

    # Lengthen names that clash with each other until they differ
    while True:
        names = [name_at(i) for i in range(len(paths))]
        changed = False
        for i, name in enumerate(names):
            clashing = [j for j, other in enumerate(names) if other == name and paths[j] != paths[i]]
            if clashing and depth[i] < len(parts[i]):
                depth[i] += 1
                changed = True
        if not changed:
            break

    # Same file twice, or a name already used by loaded data
    taken = set(existing_names)
    result = []
    for name in names:
        unique = name
        counter = 2
        while unique in taken:
            unique = f"{name} ({counter})"
            counter += 1
        taken.add(unique)
        result.append(unique)
    return result


# ---------------------------------------------------------------------------
# Checks before merging
# ---------------------------------------------------------------------------

def _data_columns(columns):
    return [c for c in columns if c != FILE_NAME_COLUMN]


def find_column_mismatches(reference_name, reference_columns, files,
                           threshold=COLUMN_MISMATCH_THRESHOLD):
    """Compare each file's columns with the first file's columns.

    files: list of (display name, columns).
    The share that differs = columns in only one of the two / columns in either.
    Returns a list of dicts for files above the threshold.
    """
    reference = set(_data_columns(reference_columns))
    mismatches = []
    for name, columns in files:
        current = set(_data_columns(columns))
        union = reference | current
        if not union:
            continue
        missing = [c for c in reference_columns if c in reference - current]
        extra = [c for c in columns if c in current - reference]
        share = (len(missing) + len(extra)) / len(union)
        if share > threshold:
            mismatches.append({
                'file': name,
                'reference': reference_name,
                'share': share,
                'missing': missing,
                'extra': extra,
            })
    return mismatches


def find_type_conflicts(frames):
    """Find columns that hold numbers in some files and text in others.

    frames: list of (display name, DataFrame).
    After merging, such a column becomes text and HiPlot shows it as categories.
    Returns a list of dicts: column, numeric files, text files, sample text values.
    """
    kinds = {}  # column -> {'numeric': [names], 'text': [names], 'samples': [...]}
    for name, df in frames:
        for col in _data_columns(df.columns):
            values = df[col].dropna()
            if values.empty:
                continue  # an empty column fits any type
            info = kinds.setdefault(col, {'numeric': [], 'text': [], 'samples': []})
            if pd.api.types.is_numeric_dtype(values):
                info['numeric'].append(name)
            else:
                info['text'].append(name)
                # Show the values that are not numbers - usually 'N/A', '-', ...
                as_numbers = pd.to_numeric(values, errors='coerce')
                for sample in values[as_numbers.isna()].astype(str).unique()[:3]:
                    if sample not in info['samples']:
                        info['samples'].append(sample)

    return [
        {'column': col, 'numeric_files': info['numeric'],
         'text_files': info['text'], 'samples': info['samples'][:3]}
        for col, info in kinds.items()
        if info['numeric'] and info['text']
    ]


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def tag_with_file_name(df, display_name):
    """Return the table with a first "File Name" column filled with display_name.

    If the table already has that column (e.g. a merged file exported earlier
    and loaded again), its values are kept and only empty cells are filled.
    """
    df = df.copy()
    if FILE_NAME_COLUMN in df.columns:
        names = df.pop(FILE_NAME_COLUMN)
        names = names.where(names.notna() & (names.astype(str).str.strip() != ""), display_name)
    else:
        names = pd.Series(display_name, index=df.index)
    df.insert(0, FILE_NAME_COLUMN, names.astype(str))
    return df


def merge_frames(frames):
    """Stack tagged tables into one.

    frames: list of (display name, DataFrame). Columns are the union in order of
    first appearance; a column missing from a file is NaN for its rows.
    The index is renumbered 0..N-1 so row edits touch exactly one row.
    """
    tagged = [tag_with_file_name(df, name) for name, df in frames]
    return pd.concat(tagged, ignore_index=True, sort=False)
