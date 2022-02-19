from typing import Generator

import api
from classes import ZBError

def massrollback(pages: list[tuple[str, int]],
                 summary: str = "",
                 markbot: bool = False) -> None:
    """Call `api.rollback` on a list of MW pageids."""
    for page in pages:
        try:
            api.rollback(page[1],
                         summary=summary,
                         markbot=markbot,
                         site=page[0])
        except ZBError:
            print("Did not rollback " + page_id)


def generate_page_list(file_name: str) -> Generator[int, None, None]:
    """Create a page list from a file, readable by `massrollback`.

    Each page in the file should be in its own row, consiting of a site name,
    (everything before the `.org`), a space, and then a pageid.  For instance:
        en.wikipedia 1234
        fr.wikisource 5678
    """
    with open("data/" + file_name, 'r', encoding='utf-8') as f:
        for line in f.read().split("\n"):
            if not line:
                continue
            try:
                site, page_id = line.split(" ")
            except ValueError:
                print("Line formatted incorrectly " + line)
                continue
            try:
                yield site, int(page_id)
            except ValueError:
                print(line + " is not an integer")


def main(file_name: str, summary: str = "", markbot: bool = False) -> None:
    massrollback(generate_page_list(file_name), summary, markbot)
