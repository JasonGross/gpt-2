import tqdm
import sys
from tensorflow import gfile
import time

def file_size(f):
  if isinstance(f, str):
    with try_open(f) as f:
      return file_size(f)
  if isinstance(f, gfile.FastGFile):
    return f.size()
  else:
    was = f.tell()
    try:
      f.seek(0, 2)
      pos = f.tell()
    finally:
      f.seek(was, 0)
    return pos

def count_lines(f, verbose=True, ignore_errors=True):
    if isinstance(f, str):
      with try_open(f) as f:
        return count_lines(f)
    n = 0
    prev = None
    size = file_size(f)
    f.seek(0)
    prev_pos = 0
    pos = 0
    update_time = time.time() + 1.0
    with tqdm.tqdm(total=size, desc="Counting lines in text file...") as pbar:
      while True:
        try:
          for line in f:
            pos += len(line)
            if time.time() > update_time:
              pbar.update(pos - prev_pos)
              prev_pos = pos
              update_time = time.time() + 1.0
            n += 1
            prev = line
            #print(n)
          break
        except UnicodeDecodeError:
          if verbose:
            sys.stderr.write('Error on line %d after %s\n' % (n+1, repr(prev)))
          if not ignore_errors:
            raise
    # Reset the file iterator, or later calls to f.tell will
    # raise an IOError or OSError:
    f.seek(0)
    return n

def for_each_line(f, total=None, verbose=True, ignore_errors=True, message=None):
    if isinstance(f, str):
      with try_open(f) as f:
        for i, line in for_each_line(f, total=total, verbose=verbose, ignore_errors=ignore_errors, message=message):
          yield i, line
    i = 0
    if isinstance(f, list):
      for line in tqdm.tqdm(f) if verbose else f:
        yield i, line
        i += 1
    else:
      prev = None
      pos = 0
      size = file_size(f)
      n = 0
      while True:
        try:
          with tqdm.tqdm(f, total=size) as pbar:
            for line in f:
              yield i, line
              i += 1
              pos += len(line)
              pbar.moveto(pos)
              prev = line
            break
        except UnicodeDecodeError:
          n += 1
          if verbose:
            sys.stderr.write('Error on line %d after %s\n' % (i+n+1, repr(prev)))
          if not ignore_errors:
            raise

import time

def try_open(filename, *args, **kws):
  if filename.startswith("gs://"):
    return gfile.FastGFile(filename, *args, **kws)
  else:
    return open(filename, *args, **kws)

def ensure_open(filename, *args, **kws):
  while True:
    try:
      return try_open(filename, *args, **kws)
    except Exception as exc:
      if not isinstance(exc, FileNotFoundError):
        import traceback
        traceback.print_exc()
      sys.stderr.write('Failed to open file: %s. Trying again in 1.0 seconds...\n' % filename)
      time.sleep(1.0)

import numpy as np
import io

def tokens_to_buffer(chunks, stride):
  assert stride in [2, 4]
  tokens = np.array(chunks, dtype=np.uint16 if stride == 2 else np.int32)
  out = io.BytesIO()
  tokens.tofile(out)
  return out.getvalue()

def tokens_from_buffer(data, stride):
  assert stride in [2, 4]
  return np.frombuffer(data, dtype=np.uint16 if stride == 2 else np.int32)

def tokens_to_file(out, chunks, stride):
  assert stride in [2, 4]
  tokens = np.array(chunks, dtype=np.uint16 if stride == 2 else np.int32)
  tokens.tofile(out)

def tokens_from_file(f, stride):
  assert stride in [2, 4]
  return np.fromfile(f, dtype=np.uint16 if stride == 2 else np.int32)

