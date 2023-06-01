import os
import re
import csv

from oudjat.utils.color_print import ColorPrint

def export_2_csv(data, file_path, delimiter=','):
  """ Helper function to export data into a CSV file """
  full_path = os.path.join(os.getcwd(), file_path)

  with open(full_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)
    writer.writeheader()
    writer.writerows(data)

def import_csv(file_path, callback, delimiter=None):
  """ Helper function to import CSV content into a list of dictionaries """
  full_path = os.path.join(os.getcwd(), file_path)

  with open(full_path, "r", encoding="utf-8", newline="") as f:
    # Try to guess the delimiter if none was specified
    if not delimiter:
      first_line = f.readline().strip("\n")
      f.seek(0)
      delimiter = re.findall(r'\W', first_line)[0]

      ColorPrint.yellow(f"\nNo delimiter specified, guessed '{delimiter}' as a delimiter")

    reader = csv.DictReader(f, delimiter=delimiter, skipinitialspace=True)
    data = callback(list(reader))

  return data
