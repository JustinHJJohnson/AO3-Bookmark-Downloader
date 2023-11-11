import sqlite3
from typing import List
import AO3T
import argparse
import toml
import os
import time


config = toml.load(f"./config.toml")

class LibraryBook(object):
    title: str
    lastModified: str
    
    def __init__(self, title: str, lastModified: str) -> None:
        self.title = title
        self.lastModified = lastModified
    
    def __str__(self):
        return f'{self.title} {self.lastModified}'


def arguments():
    parser = argparse.ArgumentParser("AO3Sync")
    parser.add_argument("--test", help="Testing flag", action='store_true')
    parser.add_argument('--dryrun', help="Fetch works but don't download", action='store_true')
    parser.add_argument('-a', '--all', help="Check all bookmarks, without this flag only the first page will be checked", action='store_true')
    parser.add_argument('-d', '--delay', help="Delay in seconds to wait between loading each work. Default is 0", action='store', type=int, default=0)
    return parser.parse_args()

def get_calibre_books() -> List[LibraryBook]:
    con = sqlite3.connect(config['calibre_db_path'])
    cur = con.cursor()
    res = cur.execute("SELECT title, timestamp FROM books")
    books = []
    for row in res:
        books.append(LibraryBook(*row))
    con.close()
    return books

def get_kavita_books() -> List[LibraryBook]:
    con = sqlite3.connect(config['kavita_db_path'])
    cur = con.cursor()
    res = cur.fetchmany
    res = cur.execute("SELECT TitleName, LastModified FROM Chapter")
    books = []
    for row in res:
        books.append(LibraryBook(*row))
    con.close()
    return books

def test_get_kavita_books() -> List[LibraryBook]:
    test_data = [
        LibraryBook("Quick Step", ""),
        LibraryBook("suck the rot right out of my bloodstream", ""),
        LibraryBook("I'm Up, I'm Up", ""),
        LibraryBook("A Fine Tradition", ""),
        LibraryBook("no one will love me like you again", ""),
        LibraryBook("Silver-Tongue", ""),
        LibraryBook("don't you know (i dream of you)", ""),
        LibraryBook("Kill your darlings", ""),
        LibraryBook("The Dekarios Folly", ""),
        LibraryBook("From the root", ""),
        LibraryBook("Fool's luck", ""),
        LibraryBook("fire in my brain and i'm burning up", ""),
        LibraryBook("Someone Else's Soul", ""),
        LibraryBook("Memories of the Seasons", ""),
        LibraryBook("discounted", ""),
        LibraryBook("10 Ways to Say I Love You", ""),
        LibraryBook("Gimmie Love", ""),
        LibraryBook("New Game Plus", ""),
        LibraryBook("New Miracle", ""),
        LibraryBook("", ""),
    ]
    return test_data

def get_ao3_bookmarks(get_all_bookmarks=False) -> List[AO3T.Work]:
    session = AO3T.Session(config['ao3_username'], config['ao3_password'])
    bookmarks = session.get_bookmarks() if get_all_bookmarks else session.get_bookmarks(pages=1)
    for bookmark in bookmarks:
        bookmark.set_session(session)
    return bookmarks

def sync_library_and_bookmarks(bookmarks: List[AO3T.Work], library_books: List[LibraryBook]) -> List[AO3T.Work]:
    library_titles = []
    for book in library_books:
        library_titles.append(book.title)
    missing_works = bookmarks.copy()

    for bookmark_work in bookmarks:
        for library_book_title in library_titles:
            if library_book_title == bookmark_work.title:
                missing_works.remove(bookmark_work)
                break
    return missing_works

def walk(top, maxdepth: int):
    dirs, nondirs = [], []
    for name in os.listdir(top):
        (dirs if os.path.isdir(os.path.join(top, name)) else nondirs).append(name)
    yield top, dirs, nondirs
    if maxdepth > 1:
        for name in dirs:
            for x in walk(os.path.join(top, name), maxdepth-1):
                yield x

def main():
    args = arguments()
    kavita_books = get_kavita_books()
    bookmarks = get_ao3_bookmarks(args.all)
    missing_works = sync_library_and_bookmarks(bookmarks, kavita_books)
    print(f'The following works are bookmarked, but not downloaded:')
    for work in missing_works: print(f'{work.title}')
    print()
    if (not args.dryrun):
        existing_folders = dict()
        for (root, dirs, files) in walk(config['download_path'], 2):
            clean_root = root[len(config['download_path'])+1:]
            if (clean_root == ""):
                for dir in dirs:
                    existing_folders[dir] = dict()
            else:
                for dir in dirs:
                    existing_folders[clean_root][dir] = True
        print("Done loading existing folders", end="\n\n")
        for work in missing_works:
            time.sleep(args.delay)
            print(f"Loading {work.title}")
            work.reload()
            download_path = config['download_path']
            author = work.authors[0].username
            download_path += f"/{author}"
            if (existing_folders.get(author) == None):
                os.mkdir(download_path)
                existing_folders[author] = dict()
            if (work.series):
                series = work.series[0].name
                download_path += f"/{series}"
                if (existing_folders[author].get(series) == None):
                    os.mkdir(download_path)
                    existing_folders[author][series] = True
            print(f"Downloading {work.title}")
            download_path += f"/{work.title}.epub"
            with open(download_path, "wb") as file:
                file.write(work.download("EPUB"))
                file.close()


if __name__ == "__main__":
    main()